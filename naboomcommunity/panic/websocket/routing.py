"""
Emergency WebSocket Routing
URL routing for emergency response WebSocket connections.
"""

from django.urls import re_path
from . import emergency_consumers as consumers
from . import location_consumers

# Emergency WebSocket URL patterns
websocket_urlpatterns = [
    # Emergency updates and notifications
    re_path(r'^ws/emergency/(?P<room_name>\w+)/$', consumers.EmergencyConsumer.as_asgi()),
    re_path(r'^ws/emergency/$', consumers.EmergencyConsumer.as_asgi()),
    
    # Location tracking and updates
    re_path(r'^ws/location/(?P<user_id>[0-9a-f-]+)/$', consumers.LocationConsumer.as_asgi()),
    re_path(r'^ws/location/$', consumers.LocationConsumer.as_asgi()),
    
    # Medical information updates
    re_path(r'^ws/medical/(?P<user_id>[0-9a-f-]+)/$', consumers.MedicalConsumer.as_asgi()),
    re_path(r'^ws/medical/$', consumers.MedicalConsumer.as_asgi()),
    
    # Family notifications
    re_path(r'^ws/family/(?P<user_id>[0-9a-f-]+)/$', location_consumers.FamilyConsumer.as_asgi()),
    re_path(r'^ws/family/$', location_consumers.FamilyConsumer.as_asgi()),
    
    # External service integration
    re_path(r'^ws/integration/(?P<service_type>\w+)/$', location_consumers.IntegrationConsumer.as_asgi()),
    re_path(r'^ws/integration/$', location_consumers.IntegrationConsumer.as_asgi()),
    
    # Offline sync status
    re_path(r'^ws/offline/(?P<user_id>[0-9a-f-]+)/$', location_consumers.OfflineConsumer.as_asgi()),
    re_path(r'^ws/offline/$', location_consumers.OfflineConsumer.as_asgi()),
    
    # General emergency status
    re_path(r'^ws/status/(?P<incident_id>[0-9a-f-]+)/$', location_consumers.StatusConsumer.as_asgi()),
    re_path(r'^ws/status/$', location_consumers.StatusConsumer.as_asgi()),
]