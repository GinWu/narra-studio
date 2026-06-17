"""Concrete capability adapters."""

from backend.app.capabilities.adapters.http_adapters import (
    BailianAdapter,
    ElevenLabsAdapter,
    FalAdapter,
    OpenAIAdapter,
    ReplicateAdapter,
)
from backend.app.capabilities.adapters.mock_adapter import MockAdapter

__all__ = ["BailianAdapter", "ElevenLabsAdapter", "FalAdapter", "MockAdapter", "OpenAIAdapter", "ReplicateAdapter"]
