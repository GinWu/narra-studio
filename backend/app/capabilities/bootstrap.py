"""Shared adapter registry bootstrap for API and worker processes."""

from __future__ import annotations

from backend.app.capabilities.adapters import BailianAdapter, ElevenLabsAdapter, FalAdapter, MockAdapter, OpenAIAdapter, ReplicateAdapter
from backend.app.capabilities.registry import AdapterRegistry


def build_default_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register(MockAdapter())
    registry.register(OpenAIAdapter())
    registry.register(ElevenLabsAdapter())
    registry.register(BailianAdapter())
    registry.register(FalAdapter())
    registry.register(ReplicateAdapter())
    return registry
