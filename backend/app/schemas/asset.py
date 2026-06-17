from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_type: str
    status: str
    relative_path: str
    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    source_experiment_id: str | None = None
    project_id: str | None = None
    rating: float | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class UploadAssetCreate(BaseModel):
    asset_type: str
    filename: str
    content_base64: str
    mime_type: str | None = None
    project_id: str | None = None
