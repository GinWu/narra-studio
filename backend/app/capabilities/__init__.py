"""Capability adapter protocol and orchestration package."""

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.capabilities.types import (
    AdapterHealthResult,
    BaseAdapter,
    CapabilityError,
    CapabilityRequest,
    CapabilityResult,
    OutputFile,
)

__all__ = [
    "AdapterHealthResult",
    "AdapterRegistry",
    "BaseAdapter",
    "CapabilityError",
    "CapabilityRequest",
    "CapabilityResult",
    "OutputFile",
]
