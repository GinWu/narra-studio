from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    metadata_json: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    metadata_json: dict[str, Any] | None = None
    cover_asset_id: str | None = None
    final_asset_id: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    status: str
    metadata_json: dict[str, Any] | None = None
    cover_asset_id: str | None = None
    final_asset_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectItemCreate(BaseModel):
    item_type: str
    target_id: str
    role: str | None = None
    sort_order: int = 0
    metadata_json: dict[str, Any] | None = None


class ProjectItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    item_type: str
    target_id: str
    role: str | None = None
    sort_order: int
    metadata_json: dict[str, Any] | None = None


class ScriptVersionCreate(BaseModel):
    title: str | None = None
    content: str
    metadata_json: dict[str, Any] | None = None


class ScriptVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    version: int
    title: str | None = None
    content: str
    status: str
    metadata_json: dict[str, Any] | None = None


class ShotCreate(BaseModel):
    name: str
    description: str | None = None
    script_version_id: str | None = None
    voiceover_text: str | None = None
    prompt_json: dict[str, Any] | None = None


class ShotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    script_version_id: str | None = None
    name: str
    description: str | None = None
    status: str
    prompt_json: dict[str, Any] | None = None
    selected_image_asset_id: str | None = None
    selected_audio_asset_id: str | None = None
    selected_video_asset_id: str | None = None
    voiceover_text: str | None = None
    metadata_json: dict[str, Any] | None = None


class ShotAssetSelect(BaseModel):
    asset_type: str
    asset_id: str


class ScriptFromTranscriptCreate(BaseModel):
    transcript_asset_id: str
    title: str | None = None
    metadata_json: dict[str, Any] | None = None


class ShotVoiceoverGenerateCreate(BaseModel):
    model_id: str | None = None
    voice_profile_id: str | None = None
    voice: str | None = None
    voice_id: str | None = None
    params_json: dict[str, Any] | None = None
    commercial_use: bool = False
    explicit_confirm: bool = False


class ShotUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    prompt_json: dict[str, Any] | None = None
    voiceover_text: str | None = None
    metadata_json: dict[str, Any] | None = None
