from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SttRunCreate(BaseModel):
    audio_asset_id: str
    model_id: str | None = None
    language: str | None = None
    params_json: dict[str, Any] | None = None
    project_id: str | None = None
    shot_id: str | None = None


class VoiceCloneRunCreate(BaseModel):
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


class AudioRunRead(BaseModel):
    experiment_id: str
    status: str
    result_mode: str
    output_text: str | None = None
    output_asset_refs_json: list[Any] | None = None
    voice_profile_id: str | None = None
    error_json: dict[str, Any] | None = None
