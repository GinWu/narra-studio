"""Adapter lookup by adapter key and capability."""

from __future__ import annotations

from backend.app.capabilities.types import BaseAdapter, CapabilityError


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter) -> None:
        self._adapters[adapter.name] = adapter

    def get(self, adapter_name: str) -> BaseAdapter:
        adapter = self._adapters.get(adapter_name)
        if adapter is None:
            raise CapabilityError("adapter_not_found", "Adapter is not registered.")
        return adapter

    def resolve(self, adapter_name: str, capability_type: str) -> BaseAdapter:
        adapter = self.get(adapter_name)
        if not adapter.supports(capability_type):
            raise CapabilityError("adapter_unsupported_capability", "Adapter does not support this capability.")
        return adapter

    def list_adapters(self) -> list[str]:
        return sorted(self._adapters)
