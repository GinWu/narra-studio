"""Audio Lab STT and Voice Clone workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.capabilities.types import RuntimeFileRef
from backend.app.db.models import Experiment, Provider, VoiceProfile
from backend.app.services.asset_service import AssetService
from backend.app.services.audio_input_validator import AudioInputValidationError, AudioInputValidator
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunOutcome, CapabilityRunService
from backend.app.services.cost_service import CostService
from backend.app.services.voice_profile_service import VoiceProfileError, VoiceProfileService


class AudioLabError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SttRunInput:
    audio_asset_id: str
    model_id: str | None = None
    language: str | None = None
    params_json: dict[str, Any] | None = None
    project_id: str | None = None
    shot_id: str | None = None


@dataclass(frozen=True)
class VoiceCloneRunInput:
    reference_audio_asset_ids: list[str]
    voice_name: str
    display_name: str | None = None
    model_id: str | None = None
    consent_status: str = "granted"
    consent_type: str | None = "self_attested"
    consent_file_asset_id: str | None = None
    source_person_note: str | None = None
    usage_scope: str | None = "personal"
    commercial_allowed: bool = False
    allowed_platforms_json: list[str] | None = None
    ai_disclosure_required: bool = True
    risk_level: str = "medium"
    params_json: dict[str, Any] | None = None
    project_id: str | None = None


@dataclass(frozen=True)
class AudioLabOutcome:
    capability_outcome: CapabilityRunOutcome
    voice_profile: VoiceProfile | None = None


class AudioLabService:
    def __init__(self, session: Session, adapter_registry: AdapterRegistry) -> None:
        self.session = session
        self.adapter_registry = adapter_registry

    def run_stt(self, payload: SttRunInput) -> AudioLabOutcome:
        validation = AudioInputValidator(self.session).validate_audio_asset(payload.audio_asset_id)
        runtime_file = self._runtime_file_ref("audio", payload.audio_asset_id, validation.asset.filename, validation.asset.mime_type)
        params = dict(payload.params_json or {})
        if payload.language:
            params["language"] = payload.language
        if validation.asset.duration_ms is not None:
            params.setdefault("duration_seconds", validation.asset.duration_ms / 1000)
        outcome = self._runner().run(
            CapabilityRunCommand(
                capability_type="stt",
                input_json={
                    "audio_asset_id": payload.audio_asset_id,
                    "audio_mime_type": validation.asset.mime_type,
                    "warnings": validation.warnings,
                },
                params_json=params,
                model_id=payload.model_id,
                project_id=payload.project_id,
                shot_id=payload.shot_id,
                runtime_files={"audio": runtime_file},
            )
        )
        return AudioLabOutcome(capability_outcome=outcome)

    def run_voice_clone(self, payload: VoiceCloneRunInput) -> AudioLabOutcome:
        validations = AudioInputValidator(self.session).validate_voice_clone_assets(payload.reference_audio_asset_ids)
        runtime_files = {
            f"audio_{index}": self._runtime_file_ref(
                f"audio_{index}",
                validation.asset.id,
                validation.asset.filename,
                validation.asset.mime_type,
            )
            for index, validation in enumerate(validations)
        }
        params = dict(payload.params_json or {})
        params["voice_name"] = payload.voice_name
        outcome = self._runner().run(
            CapabilityRunCommand(
                capability_type="voice_clone",
                input_json={
                    "reference_audio_asset_ids": payload.reference_audio_asset_ids,
                    "voice_name": payload.voice_name,
                    "display_name": payload.display_name,
                    "audio_warnings": [warning for result in validations for warning in result.warnings],
                },
                params_json=params,
                model_id=payload.model_id,
                project_id=payload.project_id,
                runtime_files=runtime_files,
            )
        )
        if outcome.result is None or outcome.experiment.status not in {"success", "partial_success"}:
            return AudioLabOutcome(capability_outcome=outcome)
        try:
            metadata = outcome.result.metadata or {}
            provider = self.session.get(Provider, outcome.experiment.provider_id)
            if provider is None:
                raise VoiceProfileError("VOICE_PROFILE_PROVIDER_MISMATCH", "Provider not found for voice profile.")
            profile = VoiceProfileService(self.session).create_from_clone_result(
                provider=provider,
                provider_voice_id=metadata.get("provider_voice_id"),
                voice_name=metadata.get("voice_name") or payload.voice_name,
                display_name=payload.display_name or metadata.get("voice_name") or payload.voice_name,
                source_audio_asset_ids=payload.reference_audio_asset_ids,
                sample_asset_id=payload.reference_audio_asset_ids[0] if payload.reference_audio_asset_ids else None,
                consent_status=payload.consent_status,
                consent_type=payload.consent_type,
                consent_file_asset_id=payload.consent_file_asset_id,
                source_person_note=payload.source_person_note,
                usage_scope=payload.usage_scope,
                commercial_allowed=payload.commercial_allowed,
                allowed_platforms_json=payload.allowed_platforms_json,
                ai_disclosure_required=payload.ai_disclosure_required,
                risk_level=payload.risk_level,
                metadata_json={
                    "source_experiment_id": outcome.experiment.id,
                    "provider_voice_id": metadata.get("provider_voice_id"),
                },
            )
        except VoiceProfileError as exc:
            self._mark_voice_profile_save_failed(outcome.experiment.id, exc.message, code=exc.code)
            raise
        except Exception as exc:
            self._mark_voice_profile_save_failed(
                outcome.experiment.id,
                "VoiceProfile could not be saved.",
                code="VOICE_PROFILE_SAVE_FAILED",
            )
            raise VoiceProfileError("VOICE_PROFILE_SAVE_FAILED", "VoiceProfile could not be saved.") from exc

        outcome.experiment.metadata_json = {
            **(outcome.experiment.metadata_json or {}),
            "voice_profile_id": profile.id,
            "provider_voice_id": profile.voice_id,
        }
        self.session.commit()
        self.session.refresh(outcome.experiment)
        return AudioLabOutcome(capability_outcome=outcome, voice_profile=profile)

    def _runner(self) -> CapabilityRunService:
        return CapabilityRunService(
            self.session,
            self.adapter_registry,
            asset_processor=AssetService(self.session),
            cost_recorder=CostService(self.session),
        )

    def _runtime_file_ref(
        self,
        key: str,
        asset_id: str,
        filename: str | None,
        mime_type: str | None,
    ) -> RuntimeFileRef:
        path = AssetService(self.session).get_download_path(asset_id)
        return RuntimeFileRef(
            key=key,
            asset_id=asset_id,
            path=path,
            filename=filename or path.name,
            mime_type=mime_type,
        )

    def _mark_voice_profile_save_failed(self, experiment_id: str, message: str, *, code: str | None = None) -> None:
        self.session.rollback()
        experiment = self.session.get(Experiment, experiment_id)
        if experiment is None:
            return
        experiment.status = "failed"
        experiment.error_json = {
            "error_type": "voice_profile_save_failed",
            "message": message,
            "code": code,
        }
        self.session.commit()
        self.session.refresh(experiment)
