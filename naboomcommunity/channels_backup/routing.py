"""Stub routing primitives for Channels."""
from __future__ import annotations


class ProtocolTypeRouter(dict):
    """Simple dict-based router placeholder."""

    def __init__(self, routes):
        super().__init__(routes)

    def __call__(self, scope):  # pragma: no cover - ASGI shim
        protocol = scope.get("type")
        application = self.get(protocol)
        if application is None:
            raise ValueError(f"Unsupported protocol: {protocol}")
        return application(scope)


class URLRouter(list):
    """Placeholder URLRouter that simply stores URL patterns."""

    def __init__(self, routes):
        super().__init__(routes)

    def __call__(self, scope):  # pragma: no cover - ASGI shim
        raise NotImplementedError("URLRouter is not supported in the stub environment")
