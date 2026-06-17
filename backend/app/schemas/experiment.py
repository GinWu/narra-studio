from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    capability_type: str
    status: str
    result_mode: str
    provider_id: str | None = None
    model_id: str | None = None
    adapter_name: str | None = None
    adapter_version: str | None = None
    parent_experiment_id: str | None = None
    prompt_template_id: str | None = None
    project_id: str | None = None
    shot_id: str | None = None
    input_json: dict[str, Any]
    normalized_params_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    output_text: str | None = None
    output_asset_refs_json: list[Any] | None = None
    usage_json: dict[str, Any] | None = None
    cost_usage_json: dict[str, Any] | None = None
    error_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    duration_ms: int | None = None
    is_best: bool
    is_failed_case: bool
    failed_reason: str | None = None
    notes: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExperimentPatch(BaseModel):
    title: str | None = None
    notes: str | None = None
    is_best: bool | None = None
    is_failed_case: bool | None = None
    failed_reason: str | None = None
    metadata_json: dict[str, Any] | None = None


class MarkFailedCaseCreate(BaseModel):
    failed_reason: str | None = None


class RerunCommandRead(BaseModel):
    capability_type: str
    input_json: dict[str, Any]
    params_json: dict[str, Any] | None = None
    model_id: str | None = None
    prompt_template_id: str | None = None
    parent_experiment_id: str
    project_id: str | None = None
    shot_id: str | None = None
    result_mode: str
