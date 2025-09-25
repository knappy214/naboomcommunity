"""Stub auth middleware for Channels."""
from __future__ import annotations


class AuthMiddlewareStack:
    """Return the inner ASGI application unchanged."""

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):  # pragma: no cover - ASGI shim
        return self.inner(scope)
