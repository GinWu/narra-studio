"""Shared database-facing Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class DbReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class ProviderRead(DbReadModel):
    name: str
    status: str
    credential_source: str
    credential_ref: str | None = None
    masked_credential: str | None = None


class ModelRead(DbReadModel):
    provider_id: str
    name: str
    capability_type: str
    adapter_key: str
    status: str


class ExperimentRead(DbReadModel):
    capability_type: str
    status: str
    result_mode: str
    input_json: dict[str, Any]
    output_asset_refs_json: list[Any] | None = None


class AssetRead(DbReadModel):
    asset_type: str
    status: str
    relative_path: str
    mime_type: str | None = None
    source_experiment_id: str | None = None


class CostRecordRead(DbReadModel):
    experiment_id: str
    capability_type: str
    estimated_cost: Decimal | None = None
    currency: str | None = None
