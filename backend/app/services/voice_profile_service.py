"""VoiceProfile creation, governance, and TTS usage validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Model, Project, Provider, VoiceProfile
from backend.app.utils.ids import new_id


VOICE_PROFILE_STATUSES = {"active", "testing", "disabled", "revoked", "expired", "draft"}
VOICE_PROFILE_CONSENT_STATUSES = {"pending", "granted", "revoked", "expired", "unknown"}
VOICE_PROFILE_RISK_LEVELS = {"low", "medium", "high"}


class VoiceProfileError(ValueError):
    def __init__(self, code: str, message: str, *, warning: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.warning = warning


@dataclass(frozen=True)
class VoiceProfileValidation:
    voice_profile: VoiceProfile
    warnings: list[str]


class VoiceProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_from_clone_result(
        self,
        *,
        provider: Provider,
        provider_voice_id: str | None,
        voice_name: str | None,
        display_name: str | None = None,
        source_audio_asset_ids: list[str] | None = None,
        sample_asset_id: str | None = None,
        consent_status: str = "granted",
        consent_type: str | None = "self_attested",
        consent_file_asset_id: str | None = None,
        source_person_note: str | None = None,
        usage_scope: str | None = "personal",
        commercial_allowed: bool = False,
        allowed_platforms_json: list[str] | None = None,
        expires_at: datetime | None = None,
        ai_disclosure_required: bool = True,
        risk_level: str = "medium",
        status: str = "active",
        metadata_json: dict[str, Any] | None = None,
    ) -> VoiceProfile:
        self._validate_status_values(
            {
                "status": status,
                "consent_status": consent_status,
                "risk_level": risk_level,
            }
        )
        if not provider_voice_id:
            raise VoiceProfileError("VOICE_PROFILE_MISSING_VOICE_ID", "Provider voice_id is required.")
        name = display_name or voice_name or provider_voice_id
        profile = VoiceProfile(
            id=new_id("vprof"),
            provider_id=provider.id,
            provider=provider.name,
            voice_id=provider_voice_id,
            voice_name=voice_name or name,
            display_name=name,
            source_type="cloned",
            consent_status=consent_status,
            consent_type=consent_type,
            consent_file_asset_id=consent_file_asset_id,
            sample_asset_id=sample_asset_id,
            source_audio_asset_ids_json=source_audio_asset_ids or [],
            source_person_note=source_person_note,
            usage_scope=usage_scope,
            commercial_allowed=commercial_allowed,
            allowed_platforms_json=allowed_platforms_json or [],
            expires_at=expires_at,
            ai_disclosure_required=ai_disclosure_required,
            risk_level=risk_level,
            status=status,
            metadata_json=metadata_json or {},
            name=name,
            external_voice_id=provider_voice_id,
            source_asset_id=sample_asset_id,
            authorization_status=self._legacy_authorization_status(consent_status, status),
            consent_reference=consent_file_asset_id,
            consent_expires_at=expires_at,
        )
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_voice_profile(self, voice_profile_id: str) -> VoiceProfile:
        profile = self.session.get(VoiceProfile, voice_profile_id)
        if profile is None or profile.deleted_at is not None:
            raise KeyError("voice_profile_not_found")
        return profile

    def list_active_voice_profiles(self, provider_id: str | None = None) -> list[VoiceProfile]:
        stmt = (
            select(VoiceProfile)
            .where(VoiceProfile.deleted_at.is_(None))
            .where(VoiceProfile.status.in_(("active", "testing")))
            .order_by(VoiceProfile.updated_at.desc())
        )
        if provider_id:
            stmt = stmt.where(VoiceProfile.provider_id == provider_id)
        return list(self.session.scalars(stmt).all())

    def list_voice_profiles(
        self,
        *,
        provider_id: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ) -> list[VoiceProfile]:
        stmt = select(VoiceProfile).order_by(VoiceProfile.updated_at.desc())
        if not include_deleted:
            stmt = stmt.where(VoiceProfile.deleted_at.is_(None))
        if provider_id:
            stmt = stmt.where(VoiceProfile.provider_id == provider_id)
        if status:
            stmt = stmt.where(VoiceProfile.status == status)
        return list(self.session.scalars(stmt).all())

    def update_voice_profile(self, voice_profile_id: str, data: dict[str, Any]) -> VoiceProfile:
        profile = self.get_voice_profile(voice_profile_id)
        self._validate_status_values(data)
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        if "display_name" in data:
            profile.name = data["display_name"]
        if "voice_id" in data:
            profile.external_voice_id = data["voice_id"]
        if "status" in data or "consent_status" in data:
            profile.authorization_status = self._legacy_authorization_status(
                profile.consent_status,
                profile.status,
            )
        if "expires_at" in data:
            profile.consent_expires_at = data["expires_at"]
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def disable_voice_profile(self, voice_profile_id: str) -> VoiceProfile:
        return self.update_voice_profile(voice_profile_id, {"status": "disabled"})

    def mark_revoked(self, voice_profile_id: str) -> VoiceProfile:
        return self.update_voice_profile(voice_profile_id, {"status": "revoked", "consent_status": "revoked"})

    def mark_expired(self, voice_profile_id: str) -> VoiceProfile:
        return self.update_voice_profile(voice_profile_id, {"status": "expired", "consent_status": "expired"})

    def set_project_default_voice_profile(self, project_id: str, voice_profile_id: str) -> Project:
        project = self.session.get(Project, project_id)
        if project is None or project.deleted_at is not None:
            raise KeyError("project_not_found")
        profile = self.get_voice_profile(voice_profile_id)
        self._validate_default_voice_profile(profile)
        metadata = dict(project.metadata_json or {})
        metadata["default_voice_profile_id"] = voice_profile_id
        project.metadata_json = metadata
        self.session.commit()
        self.session.refresh(project)
        return project

    def validate_voice_profile_for_tts(
        self,
        *,
        voice_profile_id: str,
        model: Model,
        commercial_use: bool = False,
        explicit_confirm: bool = False,
    ) -> VoiceProfileValidation:
        profile = self.get_voice_profile(voice_profile_id)
        if profile.status in {"revoked"} or profile.consent_status == "revoked":
            raise VoiceProfileError("VOICE_PROFILE_REVOKED", "VoiceProfile has been revoked.")
        if profile.status == "expired" or profile.consent_status == "expired":
            raise VoiceProfileError("VOICE_PROFILE_EXPIRED", "VoiceProfile has expired.")
        if profile.status not in {"active", "testing"}:
            raise VoiceProfileError("VOICE_PROFILE_STATUS_INVALID", "VoiceProfile is not active for TTS.")
        if profile.consent_status in {"revoked", "expired"}:
            raise VoiceProfileError("VOICE_PROFILE_CONSENT_INVALID", "VoiceProfile consent is invalid.")
        if self._is_expired(profile.expires_at):
            raise VoiceProfileError("VOICE_PROFILE_EXPIRED", "VoiceProfile has expired.")
        if not profile.voice_id:
            raise VoiceProfileError("VOICE_PROFILE_MISSING_VOICE_ID", "VoiceProfile has no provider voice_id.")
        if profile.provider_id and profile.provider_id != model.provider_id:
            raise VoiceProfileError("VOICE_PROFILE_PROVIDER_MISMATCH", "VoiceProfile provider does not match TTS model.")
        if commercial_use and not profile.commercial_allowed:
            raise VoiceProfileError("VOICE_PROFILE_COMMERCIAL_NOT_ALLOWED", "VoiceProfile is not allowed for commercial use.")
        if profile.risk_level == "high" and not explicit_confirm:
            raise VoiceProfileError("VOICE_PROFILE_EXPLICIT_CONFIRM_REQUIRED", "High-risk VoiceProfile requires explicit confirmation.")

        warnings: list[str] = []
        if profile.status == "testing":
            warnings.append("voice_profile_testing")
        if profile.ai_disclosure_required:
            warnings.append("ai_disclosure_required")
        return VoiceProfileValidation(voice_profile=profile, warnings=warnings)

    def _legacy_authorization_status(self, consent_status: str | None, status: str | None) -> str:
        if status in {"revoked", "expired"}:
            return status
        if consent_status == "granted" and status in {"active", "testing"}:
            return "authorized"
        return consent_status or status or "draft"

    def _validate_status_values(self, data: dict[str, Any]) -> None:
        checks = (
            ("status", VOICE_PROFILE_STATUSES, "VOICE_PROFILE_STATUS_INVALID"),
            ("consent_status", VOICE_PROFILE_CONSENT_STATUSES, "VOICE_PROFILE_CONSENT_INVALID"),
            ("risk_level", VOICE_PROFILE_RISK_LEVELS, "VOICE_PROFILE_RISK_LEVEL_INVALID"),
        )
        for field, allowed_values, code in checks:
            value = data.get(field)
            if value is not None and value not in allowed_values:
                raise VoiceProfileError(code, f"VoiceProfile {field} is invalid.")

    def _validate_default_voice_profile(self, profile: VoiceProfile) -> None:
        if profile.status in {"disabled", "revoked", "expired"} or profile.status not in {"active", "testing"}:
            raise VoiceProfileError("VOICE_PROFILE_STATUS_INVALID", "VoiceProfile cannot be used as a project default.")
        if profile.consent_status in {"revoked", "expired"}:
            raise VoiceProfileError("VOICE_PROFILE_CONSENT_INVALID", "VoiceProfile consent is invalid.")
        if self._is_expired(profile.expires_at):
            raise VoiceProfileError("VOICE_PROFILE_EXPIRED", "VoiceProfile has expired.")
        if not profile.voice_id:
            raise VoiceProfileError("VOICE_PROFILE_MISSING_VOICE_ID", "VoiceProfile has no provider voice_id.")

    def _is_expired(self, expires_at: datetime | None) -> bool:
        if expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            return expires_at <= now.replace(tzinfo=None)
        return expires_at <= now
