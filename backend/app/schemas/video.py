from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class VideoGenerationCreate(BaseModel):
    prompt: str | None = None
    negative_prompt: str | None = None
    prompt_template_id: str | None = None
    variables: dict[str, Any] | None = None
    model_id: str | None = None
    duration_seconds: int | None = None
    aspect_ratio: str | None = None
    params_json: dict[str, Any] | None = None
    project_id: str | None = None
    shot_id: str | None = None
    run_immediately: bool = False


class VideoTaskRead(BaseModel):
    task_id: str
    experiment_id: str
    status: str
