"""Provider CRUD, safe credential metadata, and connection checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Provider
from backend.app.services.credential_resolver import (
    CredentialResolutionError,
    CredentialResolver,
    mask_reference,
)
from backend.app.utils.ids import new_id


class ProviderService:
    def __init__(self, session: Session, resolver: CredentialResolver | None = None) -> None:
        self.session = session
        self.resolver = resolver or CredentialResolver()

    def list_providers(self, include_deleted: bool = False) -> list[Provider]:
        stmt = select(Provider).order_by(Provider.name)
        if not include_deleted:
            stmt = stmt.where(Provider.deleted_at.is_(None))
        return list(self.session.scalars(stmt).all())

    def get_provider(self, provider_id: str) -> Provider:
        provider = self.session.get(Provider, provider_id)
        if provider is None or provider.deleted_at is not None:
            raise KeyError("provider_not_found")
        return provider

    def create_provider(self, data: dict[str, Any]) -> Provider:
        provider = Provider(id=data.pop("id", new_id("prv")), **self._normalize_provider_data(data))
        self.session.add(provider)
        self.session.commit()
        self.session.refresh(provider)
        return provider

    def update_provider(self, provider_id: str, data: dict[str, Any]) -> Provider:
        provider = self.get_provider(provider_id)
        for key, value in self._normalize_provider_data(data, partial=True).items():
            setattr(provider, key, value)
        self.session.commit()
        self.session.refresh(provider)
        return provider

    def delete_provider(self, provider_id: str) -> Provider:
        provider = self.get_provider(provider_id)
        provider.enabled = False
        provider.deleted_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(provider)
        return provider

    def test_connection(self, provider_id: str) -> dict[str, Any]:
        provider = self.get_provider(provider_id)
        try:
            credential = self.resolver.resolve(provider)
        except CredentialResolutionError as exc:
            provider.status = "error"
            provider.last_health_status = "error"
            provider.last_health_error = exc.code
            self.session.commit()
            return {"ok": False, "status": "error", "code": exc.code, "message": exc.message}

        provider.status = "active"
        provider.last_health_status = "ok"
        provider.last_health_error = None
        provider.masked_credential = mask_reference(provider.credential_ref or credential.reference)
        self.session.commit()
        return {"ok": True, "status": "active", "message": "Provider connection test passed"}

    def seed_defaults(self) -> list[Provider]:
        existing = {provider.name for provider in self.list_providers(include_deleted=True)}
        created: list[Provider] = []
        for seed in DEFAULT_PROVIDERS:
            if seed["name"] in existing:
                continue
            provider = Provider(id=new_id("prv"), **self._normalize_provider_data(seed))
            self.session.add(provider)
            created.append(provider)
        self.session.commit()
        for provider in created:
            self.session.refresh(provider)
        return created

    def _normalize_provider_data(self, data: dict[str, Any], partial: bool = False) -> dict[str, Any]:
        normalized = dict(data)
        if "enabled" not in normalized and not partial:
            normalized["enabled"] = False
        if "status" not in normalized and not partial:
            normalized["status"] = "active" if normalized.get("enabled") else "disabled"
        if "provider_type" not in normalized and not partial:
            normalized["provider_type"] = "cloud_api"
        if "auth_type" not in normalized and not partial:
            normalized["auth_type"] = "none"
        if "credential_source" not in normalized and not partial:
            normalized["credential_source"] = "none"
        if "masked_credential" not in normalized:
            normalized["masked_credential"] = mask_reference(
                normalized.get("credential_ref") or normalized.get("credential_file")
            )
        return normalized


DEFAULT_PROVIDERS: tuple[dict[str, Any], ...] = (
    {
        "name": "openai",
        "display_name": "OpenAI",
        "provider_type": "cloud_api",
        "auth_type": "bearer_token",
        "credential_source": "docker_secret",
        "credential_ref": "openai_api_key",
        "credential_file": "/run/secrets/openai_api_key",
        "enabled": False,
        "status": "disabled",
        "adapter_name": "openai",
        "capability_summary_json": ["tts", "stt", "image_generation", "image_edit"],
    },
    {
        "name": "elevenlabs",
        "display_name": "ElevenLabs",
        "provider_type": "cloud_api",
        "auth_type": "api_key",
        "credential_source": "docker_secret",
        "credential_ref": "elevenlabs_api_key",
        "credential_file": "/run/secrets/elevenlabs_api_key",
        "enabled": False,
        "status": "disabled",
        "adapter_name": "elevenlabs",
        "capability_summary_json": ["tts", "stt", "voice_clone"],
    },
    {
        "name": "fal",
        "display_name": "fal.ai",
        "provider_type": "model_gateway",
        "auth_type": "api_key",
        "credential_source": "docker_secret",
        "credential_ref": "fal_key",
        "credential_file": "/run/secrets/fal_key",
        "enabled": False,
        "status": "disabled",
        "adapter_name": "fal",
        "capability_summary_json": ["image_generation", "image_edit", "video_generation"],
    },
    {
        "name": "bailian",
        "display_name": "Alibaba Cloud Bailian",
        "provider_type": "model_gateway",
        "auth_type": "bearer_token",
        "credential_source": "docker_secret",
        "credential_ref": "dashscope_api_key",
        "credential_file": "/run/secrets/dashscope_api_key",
        "enabled": False,
        "status": "disabled",
        "adapter_name": "bailian",
        "api_base": "https://dashscope.aliyuncs.com",
        "capability_summary_json": ["tts", "stt", "voice_clone", "image_generation", "video_generation"],
    },
    {
        "name": "replicate",
        "display_name": "Replicate",
        "provider_type": "model_gateway",
        "auth_type": "bearer_token",
        "credential_source": "docker_secret",
        "credential_ref": "replicate_api_token",
        "credential_file": "/run/secrets/replicate_api_token",
        "enabled": False,
        "status": "disabled",
        "adapter_name": "replicate",
        "capability_summary_json": ["image_generation", "image_edit", "video_generation"],
    },
    {
        "name": "mock",
        "display_name": "Local Mock",
        "provider_type": "mock",
        "auth_type": "none",
        "credential_source": "none",
        "enabled": True,
        "status": "active",
        "adapter_name": "mock",
        "capability_summary_json": ["tts", "stt", "voice_clone", "image_generation", "video_generation"],
    },
)
