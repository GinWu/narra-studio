from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class EvaluationUpsert(BaseModel):
    target_type: str
    target_id: str
    dimension: str
    score: float | None = None
    label: str | None = None
    comment: str | None = None
    evaluator_id: str = "local"
    compare_group_id: str | None = None
    is_best: bool = False
    is_failed_case: bool = False
    metadata_json: dict[str, Any] | None = None


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_type: str
    target_id: str
    experiment_id: str | None = None
    asset_id: str | None = None
    prompt_template_id: str | None = None
    dimension: str
    score: float | None = None
    label: str | None = None
    comment: str | None = None
    evaluator_id: str
    is_best: bool
    is_failed_case: bool
    is_active: bool
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class CompareConclusionCreate(BaseModel):
    target_ids: list[str]
    comment: str
    compare_group_id: str | None = None
    evaluator_id: str = "local"


class CompareItemsCreate(BaseModel):
    experiment_ids: list[str]
