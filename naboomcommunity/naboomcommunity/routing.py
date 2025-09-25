"""Aggregate ASGI routing configuration."""
from communityhub.routing import websocket_urlpatterns as communityhub_ws

websocket_urlpatterns = [*communityhub_ws]
