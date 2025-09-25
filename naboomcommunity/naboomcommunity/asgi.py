"""ASGI entrypoint supporting Django Channels."""
from __future__ import annotations

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naboomcommunity.settings.dev")

try:
    from .routing import websocket_urlpatterns
except ImportError:  # pragma: no cover - routing optional during bootstrap
    websocket_urlpatterns = []

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
