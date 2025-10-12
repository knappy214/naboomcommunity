"""Stub AsyncJsonWebsocketConsumer implementation."""
from __future__ import annotations

from typing import Any

from ..layers import get_channel_layer


class AsyncJsonWebsocketConsumer:
    """Minimal async consumer that stores messages for testing."""

    def __init__(self):
        self.scope = {"user": None, "url_route": {"kwargs": {}}}
        self.channel_name = "test-channel"
        self.channel_layer = get_channel_layer()
        self._accepted = False
        self._messages: list[Any] = []

    async def accept(self):  # pragma: no cover - stub behaviour
        self._accepted = True

    async def close(self, code: int = 1000):  # pragma: no cover - stub behaviour
        self._accepted = False

    async def send_json(self, content: Any):  # pragma: no cover - stub behaviour
        self._messages.append(content)

    async def receive_json(self, content: Any, **kwargs):  # pragma: no cover - stub behaviour
        return None

    # Group management hooks provided for API compatibility
    async def connect(self):  # pragma: no cover - stub behaviour
        await self.accept()

    async def disconnect(self, close_code: int):  # pragma: no cover - stub behaviour
        await self.close(close_code)
