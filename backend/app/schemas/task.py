from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    task_type: str
    experiment_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    request_json: dict[str, Any] | None = None
    queue_name: str = "default"
    priority: int = 0
    timeout_seconds: int | None = None
    max_retries: int = 0


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_type: str
    status: str
    progress: float | None = None
    experiment_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    provider_task_id: str | None = None
    provider_status: str | None = None
    cancel_requested: bool
    request_json: dict[str, Any] | None = None
    result_json: dict[str, Any] | None = None
    error_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
