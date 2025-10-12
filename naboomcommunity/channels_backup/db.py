"""Stub database helpers for Channels."""
from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable


def database_sync_to_async(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """Execute the wrapped function synchronously within async contexts."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
