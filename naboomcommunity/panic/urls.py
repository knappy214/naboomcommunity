from __future__ import annotations

from django.urls import path

from . import (
    views,
    views_actions,
    views_push,
    views_relay,
    views_stream,
    views_ussd,
    views_vehicle,
    views_waypoints,
    security_views,
)
from .api import (
    enhanced_views,
    websocket_views,
    offline_views,
    family_views,
    integration_views,
)

urlpatterns = [
    # Primary URLs with trailing slashes (recommended)
    path("api/submit/", views.submit_incident, name="panic_submit"),
    path("api/contacts/bulk_upsert/", views.bulk_upsert_contacts, name="panic_contacts_upsert"),
    path("api/push/register/", views_push.register_push, name="panic_push_register"),
    path("api/relay_submit/", views_relay.relay_submit, name="panic_relay_submit"),
    path("api/vehicle/ping/", views_vehicle.ping, name="panic_vehicle_ping"),
    path("api/vehicle/live/", views_vehicle.live, name="panic_vehicle_live"),
    path("api/vehicle/tracks/", views_vehicle.tracks, name="panic_vehicle_tracks"),
    path("api/waypoints/", views_waypoints.list_waypoints, name="panic_waypoints"),
    path("api/stream/", views_stream.sse_stream, name="panic_sse_stream"),
    path("api/incidents/", views.list_incidents, name="panic_incidents_list"),
    path("api/incidents/<int:pk>/ack/", views_actions.ack, name="panic_ack"),
    path("api/incidents/<int:pk>/resolve/", views_actions.resolve, name="panic_resolve"),
    path("api/alerts/", views.list_patrol_alerts, name="panic_alerts_list"),
    path("api/responders/", views.list_responders, name="panic_responders_list"),
    path("webhooks/clickatell/inbound/", views.clickatell_inbound, name="panic_clickatell_inbound"),
    path("webhooks/clickatell/status/", views.clickatell_status, name="panic_clickatell_status"),
    path("ussd/handle/", views_ussd.ussd_handle, name="panic_ussd_handle"),
    
    # Enhanced Emergency Response API endpoints
    path("api/enhanced/panic/", enhanced_views.enhanced_panic_button, name="enhanced_panic_button"),
    path("api/websocket/status/", websocket_views.websocket_status, name="websocket_status"),
    path("api/offline/panic/", offline_views.offline_panic_button, name="offline_panic_button"),
    path("api/offline/sync/", offline_views.sync_offline_data, name="offline_sync"),
    path("api/family/notify/", family_views.send_family_notification, name="family_notify"),
    path("api/family/contacts/", family_views.get_emergency_contacts, name="family_contacts"),
    path("api/integration/dispatch/", integration_views.dispatch_emergency_service, name="dispatch_service"),
    path("api/integration/status/<str:dispatch_id>/", integration_views.get_service_status, name="service_status"),
    
    # Backward compatibility URLs without trailing slashes (for existing clients)
    path("api/submit", views.submit_incident, name="panic_submit_no_slash"),
    path("api/contacts/bulk_upsert", views.bulk_upsert_contacts, name="panic_contacts_upsert_no_slash"),
    path("api/push/register", views_push.register_push, name="panic_push_register_no_slash"),
    path("api/relay_submit", views_relay.relay_submit, name="panic_relay_submit_no_slash"),
    path("api/vehicle/ping", views_vehicle.ping, name="panic_vehicle_ping_no_slash"),
    path("api/vehicle/live", views_vehicle.live, name="panic_vehicle_live_no_slash"),
    path("api/vehicle/tracks", views_vehicle.tracks, name="panic_vehicle_tracks_no_slash"),
    path("api/waypoints", views_waypoints.list_waypoints, name="panic_waypoints_no_slash"),
    path("api/stream", views_stream.sse_stream, name="panic_sse_stream_no_slash"),
    path("api/incidents/<int:pk>/ack", views_actions.ack, name="panic_ack_no_slash"),
    path("api/incidents/<int:pk>/resolve", views_actions.resolve, name="panic_resolve_no_slash"),
    path("api/responders", views.list_responders, name="panic_responders_list_no_slash"),
    path("ussd/handle", views_ussd.ussd_handle, name="panic_ussd_handle_no_slash"),
    
    # Security: Block common attack patterns
    path(".git/", security_views.block_common_attacks, name="panic_block_git"),
    path("geoserver/", security_views.block_common_attacks, name="panic_block_geoserver"),
    path("wp-admin/", security_views.block_common_attacks, name="panic_block_wpadmin"),
    path("phpmyadmin/", security_views.block_common_attacks, name="panic_block_phpmyadmin"),
]
