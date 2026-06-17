from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class CostRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    provider_id: str | None = None
    model_id: str | None = None
    capability_type: str
    usage_json: dict[str, Any] | None = None
    normalized_usage_json: dict[str, Any] | None = None
    pricing_snapshot_json: dict[str, Any] | None = None
    estimated_cost: Decimal | None = None
    currency: str | None = None
    created_at: datetime


class InvocationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str | None = None
    task_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    capability_type: str | None = None
    status: str
    request_summary_json: dict[str, Any] | None = None
    response_summary_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    error_json: dict[str, Any] | None = None
    created_at: datetime
