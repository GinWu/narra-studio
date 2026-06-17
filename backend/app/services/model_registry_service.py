"""Model Registry CRUD and default model lookup."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Model, Provider
from backend.app.utils.ids import new_id


class ModelRegistryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_models(
        self,
        provider_id: str | None = None,
        capability_type: str | None = None,
        enabled: bool | None = None,
        include_deleted: bool = False,
    ) -> list[Model]:
        stmt = select(Model).order_by(Model.capability_type, Model.name)
        if not include_deleted:
            stmt = stmt.where(Model.deleted_at.is_(None))
        if provider_id:
            stmt = stmt.where(Model.provider_id == provider_id)
        if capability_type:
            stmt = stmt.where(Model.capability_type == capability_type)
        if enabled is not None:
            stmt = stmt.where(Model.enabled.is_(enabled))
        return list(self.session.scalars(stmt).all())

    def get_model(self, model_id: str) -> Model:
        model = self.session.get(Model, model_id)
        if model is None or model.deleted_at is not None:
            raise KeyError("model_not_found")
        return model

    def create_model(self, data: dict[str, Any]) -> Model:
        self._ensure_provider(data["provider_id"])
        payload = self._normalize_model_data(data)
        if payload.get("is_default"):
            self._clear_default(payload["capability_type"])
        model = Model(id=payload.pop("id", new_id("mdl")), **payload)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def update_model(self, model_id: str, data: dict[str, Any]) -> Model:
        model = self.get_model(model_id)
        payload = self._normalize_model_data(data, partial=True)
        if payload.get("provider_id"):
            self._ensure_provider(payload["provider_id"])
        if payload.get("is_default"):
            self._clear_default(payload.get("capability_type") or model.capability_type, exclude_id=model.id)
        for key, value in payload.items():
            setattr(model, key, value)
        self.session.commit()
        self.session.refresh(model)
        return model

    def delete_model(self, model_id: str) -> Model:
        model = self.get_model(model_id)
        model.enabled = False
        model.deleted_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(model)
        return model

    def get_default_model(self, capability_type: str) -> Model:
        stmt = (
            select(Model)
            .where(Model.deleted_at.is_(None))
            .where(Model.enabled.is_(True))
            .where(Model.status == "active")
            .where(Model.capability_type == capability_type)
            .where(Model.is_default.is_(True))
        )
        model = self.session.scalars(stmt).first()
        if model is None:
            raise KeyError("default_model_not_found")
        return model

    def seed_mock_models(self, provider_id: str) -> list[Model]:
        self._ensure_provider(provider_id)
        existing = {
            (model.provider_id, model.name)
            for model in self.list_models(provider_id=provider_id, include_deleted=True)
        }
        seeds = (
            {
                "name": "mock-tts",
                "capability_type": "tts",
                "adapter_key": "mock",
                "is_default": True,
                "metadata_json": {
                    "supports_voice_profile": True,
                    "supports_voice_id": True,
                    "supports_builtin_voice": True,
                    "supports_reference_audio_tts": False,
                    "voice_profile_provider_scope": "same_provider",
                },
                "default_params_json": {"voice": "mock-default"},
            },
            {"name": "mock-stt", "capability_type": "stt", "adapter_key": "mock", "is_default": True},
            {"name": "mock-voice-clone", "capability_type": "voice_clone", "adapter_key": "mock", "is_default": True},
            {
                "name": "mock-image-generation",
                "capability_type": "image_generation",
                "adapter_key": "mock",
                "is_default": True,
            },
            {
                "name": "mock-video-generation",
                "capability_type": "video_generation",
                "adapter_key": "mock",
                "is_default": True,
            },
        )
        created: list[Model] = []
        for seed in seeds:
            if (provider_id, seed["name"]) in existing:
                continue
            created.append(self.create_model({"provider_id": provider_id, **seed}))
        return created

    def seed_bailian_models(self, provider_id: str) -> list[Model]:
        self._ensure_provider(provider_id)
        existing = {
            (model.provider_id, model.name)
            for model in self.list_models(provider_id=provider_id, include_deleted=True)
        }
        seeds = (
            {
                "name": "bailian-tts",
                "capability_type": "tts",
                "adapter_key": "bailian",
                "external_model_id": "qwen-tts",
                "enabled": False,
                "is_default": False,
                "default_params_json": {"voice": "Cherry", "response_format": "mp3"},
                "metadata_json": {
                    "provider_family": "bailian",
                    "supports_builtin_voice": True,
                    "supports_voice_id": True,
                    "supports_voice_profile": True,
                    "default_endpoint_path": "/compatible-mode/v1/audio/speech",
                },
            },
            {
                "name": "bailian-stt",
                "capability_type": "stt",
                "adapter_key": "bailian",
                "external_model_id": "paraformer-v2",
                "enabled": False,
                "is_default": False,
                "metadata_json": {
                    "provider_family": "bailian",
                    "default_endpoint_path": "/api/v1/services/audio/asr/transcription",
                    "input_mode": "multipart",
                },
            },
            {
                "name": "bailian-voice-clone",
                "capability_type": "voice_clone",
                "adapter_key": "bailian",
                "external_model_id": "cosyvoice-clone",
                "enabled": False,
                "is_default": False,
                "metadata_json": {
                    "provider_family": "bailian",
                    "default_endpoint_path": "/api/v1/services/audio/voice-clone",
                    "input_mode": "multipart",
                    "requires_consent": True,
                },
            },
        )
        created: list[Model] = []
        for seed in seeds:
            if (provider_id, seed["name"]) in existing:
                continue
            created.append(self.create_model({"provider_id": provider_id, **seed}))
        return created

    def _ensure_provider(self, provider_id: str) -> Provider:
        provider = self.session.get(Provider, provider_id)
        if provider is None or provider.deleted_at is not None:
            raise KeyError("provider_not_found")
        return provider

    def _clear_default(self, capability_type: str, exclude_id: str | None = None) -> None:
        stmt = select(Model).where(Model.capability_type == capability_type).where(Model.is_default.is_(True))
        for existing in self.session.scalars(stmt).all():
            if exclude_id and existing.id == exclude_id:
                continue
            existing.is_default = False

    def _normalize_model_data(self, data: dict[str, Any], partial: bool = False) -> dict[str, Any]:
        payload = dict(data)
        if "enabled" not in payload and not partial:
            payload["enabled"] = True
        if "status" not in payload and not partial:
            payload["status"] = "active"
        if "adapter_key" not in payload and not partial:
            provider = self._ensure_provider(payload["provider_id"])
            payload["adapter_key"] = provider.adapter_name or provider.name
        return payload
