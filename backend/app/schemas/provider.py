from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ProviderCreate(BaseModel):
    name: str
    display_name: str | None = None
    provider_type: str = "cloud_api"
    api_base: str | None = None
    docker_service_name: str | None = None
    auth_type: str = "none"
    credential_source: str = "none"
    credential_ref: str | None = None
    credential_file: str | None = None
    enabled: bool = False
    status: str | None = None
    timeout_seconds: int | None = None
    retry_policy_json: dict[str, Any] | None = None
    rate_limit_note: str | None = None
    capability_summary_json: list[str] | None = None
    adapter_name: str | None = None
    sdk_package: str | None = None
    sdk_version_constraint: str | None = None
    metadata_json: dict[str, Any] | None = None


class ProviderUpdate(BaseModel):
    display_name: str | None = None
    provider_type: str | None = None
    api_base: str | None = None
    docker_service_name: str | None = None
    auth_type: str | None = None
    credential_source: str | None = None
    credential_ref: str | None = None
    credential_file: str | None = None
    enabled: bool | None = None
    status: str | None = None
    timeout_seconds: int | None = None
    retry_policy_json: dict[str, Any] | None = None
    rate_limit_note: str | None = None
    capability_summary_json: list[str] | None = None
    adapter_name: str | None = None
    sdk_package: str | None = None
    sdk_version_constraint: str | None = None
    metadata_json: dict[str, Any] | None = None


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str | None
    provider_type: str
    api_base: str | None
    docker_service_name: str | None
    auth_type: str
    credential_source: str
    credential_ref: str | None
    credential_file: str | None
    masked_credential: str | None
    enabled: bool
    status: str
    timeout_seconds: int | None
    retry_policy_json: dict[str, Any] | None
    rate_limit_note: str | None
    capability_summary_json: list[str] | None
    adapter_name: str | None
    sdk_package: str | None
    sdk_version_constraint: str | None
    metadata_json: dict[str, Any] | None
    last_health_status: str | None
    last_health_error: str | None


class ProviderTestRead(BaseModel):
    ok: bool
    status: str
    message: str
    code: str | None = None
