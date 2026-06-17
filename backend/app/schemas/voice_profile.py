from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class VoiceProfileUpdate(BaseModel):
    display_name: str | None = None
    voice_name: str | None = None
    consent_status: Literal["pending", "granted", "revoked", "expired", "unknown"] | None = None
    consent_type: str | None = None
    consent_file_asset_id: str | None = None
    sample_asset_id: str | None = None
    source_person_note: str | None = None
    usage_scope: str | None = None
    commercial_allowed: bool | None = None
    allowed_platforms_json: list[str] | None = None
    expires_at: datetime | None = None
    ai_disclosure_required: bool | None = None
    risk_level: Literal["low", "medium", "high"] | None = None
    status: Literal["active", "testing", "disabled", "revoked", "expired", "draft"] | None = None
    metadata_json: dict[str, Any] | None = None


class VoiceProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str | None = None
    provider: str | None = None
    voice_id: str | None = None
    voice_name: str | None = None
    display_name: str
    source_type: str
    consent_status: str
    consent_type: str | None = None
    consent_file_asset_id: str | None = None
    sample_asset_id: str | None = None
    source_audio_asset_ids_json: list[Any] | None = None
    source_person_note: str | None = None
    usage_scope: str | None = None
    commercial_allowed: bool
    allowed_platforms_json: list[str] | None = None
    expires_at: datetime | None = None
    ai_disclosure_required: bool
    risk_level: str
    status: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SetProjectDefaultVoiceProfile(BaseModel):
    project_id: str
