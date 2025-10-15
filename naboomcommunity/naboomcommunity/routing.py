"""Aggregate ASGI routing configuration."""
from communityhub.routing import websocket_urlpatterns as communityhub_ws
from panic.websocket.routing import websocket_urlpatterns as emergency_ws

websocket_urlpatterns = [*communityhub_ws, *emergency_ws]
