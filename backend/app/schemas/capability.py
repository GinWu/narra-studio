from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CapabilityRunCreate(BaseModel):
    capability_type: str
    input_json: dict[str, Any]
    params_json: dict[str, Any] | None = None
    model_id: str | None = None
    prompt_template_id: str | None = None
    parent_experiment_id: str | None = None
    project_id: str | None = None
    shot_id: str | None = None
    result_mode: str = "sync"


class CapabilityRunRead(BaseModel):
    experiment_id: str
    status: str
    result_mode: str
    output_asset_refs_json: list[Any] | None = None
    error_json: dict[str, Any] | None = None
