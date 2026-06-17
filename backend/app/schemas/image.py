from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from backend.app.schemas.voice import LabRunRead


class ImageGenerationCreate(BaseModel):
    prompt: str | None = None
    negative_prompt: str | None = None
    prompt_template_id: str | None = None
    variables: dict[str, Any] | None = None
    model_id: str | None = None
    size: str | None = None
    aspect_ratio: str | None = None
    n: int = 1
    params_json: dict[str, Any] | None = None
    project_id: str | None = None
    shot_id: str | None = None
