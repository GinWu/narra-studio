"""Canonical capability request/result objects shared by services and adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from backend.app.db.models import Model, Provider
from backend.app.services.credential_resolver import ResolvedCredential


@dataclass(frozen=True)
class OutputFile:
    file_role: str
    file_type: str
    mime_type: str | None = None
    extension: str | None = None
    temp_path: str | None = None
    source_url: str | None = None
    size_bytes: int | None = None
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    sha256: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeFileRef:
    key: str
    asset_id: str
    path: Path
    filename: str
    mime_type: str | None = None


@dataclass(frozen=True)
class CapabilityRequest:
    request_id: str
    experiment_id: str
    capability_type: str
    provider: Provider
    model: Model
    credential: ResolvedCredential
    input_json: dict[str, Any]
    params_json: dict[str, Any]
    runtime_files: dict[str, RuntimeFileRef] = field(default_factory=dict)
    timeout_seconds: int | None = None


@dataclass(frozen=True)
class CapabilityResult:
    status: str
    result_mode: str = "sync"
    output_text: str | None = None
    output_files: list[OutputFile] = field(default_factory=list)
    provider_task_id: str | None = None
    usage: dict[str, Any] | None = None
    cost_usage: dict[str, Any] | None = None
    raw_response: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class AdapterHealthResult:
    ok: bool
    message: str
    status: str = "active"
    metadata: dict[str, Any] | None = None


class CapabilityError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: str = "failed",
        retryable: bool = False,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds

    def to_error_json(self) -> dict[str, Any]:
        return {
            "error_type": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "retry_after_seconds": self.retry_after_seconds,
        }


class BaseAdapter(Protocol):
    name: str
    version: str
    supported_capabilities: list[str]

    def supports(self, capability_type: str) -> bool:
        ...

    def health_check(self, provider: Provider, credential: ResolvedCredential) -> AdapterHealthResult:
        ...

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        ...

    def run_tts(self, request: CapabilityRequest) -> CapabilityResult:
        ...

    def run_stt(self, request: CapabilityRequest) -> CapabilityResult:
        ...

    def run_voice_clone(self, request: CapabilityRequest) -> CapabilityResult:
        ...

    def map_error(self, exc: Exception) -> CapabilityError:
        ...
