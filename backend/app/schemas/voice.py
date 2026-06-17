from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TtsRunCreate(BaseModel):
    text: str | None = None
    prompt_template_id: str | None = None
    variables: dict[str, Any] | None = None
    model_id: str | None = None
    voice: str | None = None
    voice_id: str | None = None
    voice_config: dict[str, Any] | None = None
    speed: float | None = None
    response_format: str | None = None
    params_json: dict[str, Any] | None = None
    commercial_use: bool = False
    explicit_confirm: bool = False
    project_id: str | None = None
    shot_id: str | None = None


class LabRunRead(BaseModel):
    experiment_id: str
    status: str
    result_mode: str
    output_asset_refs_json: list[Any] | None = None
    error_json: dict[str, Any] | None = None
