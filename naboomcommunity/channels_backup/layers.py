"""Stub channel layer implementation."""
from __future__ import annotations

from typing import Any


class InMemoryChannelLayer:
    """Extremely small in-memory channel layer for tests."""

    def __init__(self):
        self.store: dict[str, list[Any]] = {}

    async def group_add(self, group: str, channel: str):  # pragma: no cover - stub behaviour
        self.store.setdefault(group, [])

    async def group_discard(self, group: str, channel: str):  # pragma: no cover - stub behaviour
        self.store.pop(group, None)

    async def group_send(self, group: str, message: dict[str, Any]):  # pragma: no cover - stub behaviour
        self.store.setdefault(group, []).append(message)


_layer = InMemoryChannelLayer()


def get_channel_layer() -> InMemoryChannelLayer:
    return _layer
