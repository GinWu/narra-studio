from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ModelCreate(BaseModel):
    provider_id: str
    name: str
    display_name: str | None = None
    external_model_id: str | None = None
    capability_type: str
    adapter_key: str | None = None
    status: str = "active"
    enabled: bool = True
    is_default: bool = False
    api_base_override: str | None = None
    input_schema_json: dict[str, Any] | None = None
    output_schema_json: dict[str, Any] | None = None
    default_params_json: dict[str, Any] | None = None
    pricing_json: dict[str, Any] | None = None
    limits_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class ModelUpdate(BaseModel):
    provider_id: str | None = None
    name: str | None = None
    display_name: str | None = None
    external_model_id: str | None = None
    capability_type: str | None = None
    adapter_key: str | None = None
    status: str | None = None
    enabled: bool | None = None
    is_default: bool | None = None
    api_base_override: str | None = None
    input_schema_json: dict[str, Any] | None = None
    output_schema_json: dict[str, Any] | None = None
    default_params_json: dict[str, Any] | None = None
    pricing_json: dict[str, Any] | None = None
    limits_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class ModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    name: str
    display_name: str | None
    external_model_id: str | None
    capability_type: str
    adapter_key: str
    status: str
    enabled: bool
    is_default: bool
    api_base_override: str | None
    input_schema_json: dict[str, Any] | None
    output_schema_json: dict[str, Any] | None
    default_params_json: dict[str, Any] | None
    pricing_json: dict[str, Any] | None
    limits_json: dict[str, Any] | None
    metadata_json: dict[str, Any] | None
