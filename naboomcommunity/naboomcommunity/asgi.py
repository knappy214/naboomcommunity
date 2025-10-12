"""ASGI entrypoint supporting Django Channels."""
from __future__ import annotations

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naboomcommunity.settings.production")

# Initialize Django ASGI application early to ensure the AppRegistry is populated
# This must be done before importing anything that touches models
django_asgi_app = get_asgi_application()

# Now we can safely import routing
try:
    from .routing import websocket_urlpatterns
except ImportError:  # pragma: no cover - routing optional during bootstrap
    websocket_urlpatterns = []

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
