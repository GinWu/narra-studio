from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PromptTemplateCreate(BaseModel):
    name: str
    capability_type: str
    content: str
    variables_schema_json: dict[str, Any] | None = None
    default_values_json: dict[str, Any] | None = None
    description: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None


class PromptTemplateUpdate(BaseModel):
    name: str | None = None
    capability_type: str | None = None
    content: str | None = None
    variables_schema_json: dict[str, Any] | None = None
    default_values_json: dict[str, Any] | None = None
    status: str | None = None
    rating: float | None = None
    is_favorite: bool | None = None
    description: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None


class PromptTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    capability_type: str
    content: str
    variables_schema_json: dict[str, Any] | None = None
    default_values_json: dict[str, Any] | None = None
    version: int
    version_group_id: str
    parent_template_id: str | None = None
    content_hash: str
    is_latest: bool
    status: str
    rating: float | None = None
    usage_count: int
    success_count: int
    failure_count: int
    is_favorite: bool
    notes: str | None = None
    description: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class PromptAssembleCreate(BaseModel):
    variables: dict[str, Any] | None = None


class PromptAssembleRead(BaseModel):
    prompt: str
