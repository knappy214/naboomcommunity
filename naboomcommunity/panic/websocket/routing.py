"""
WebSocket Routing for Emergency Response
Defines URL patterns for WebSocket consumers.
"""

from django.urls import re_path
from . import emergency_consumers, location_consumers

websocket_urlpatterns = [
    # Emergency updates WebSocket
    re_path(r'ws/emergency/(?P<room_name>\w+)/$', 
            emergency_consumers.EmergencyConsumer.as_asgi()),
    
    # Location updates WebSocket
    re_path(r'ws/location/(?P<user_id>\w+)/$', 
            location_consumers.LocationConsumer.as_asgi()),
]
