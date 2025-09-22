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
)

urlpatterns = [
    path("api/submit/", views.submit_incident, name="panic_submit"),
    path("api/contacts/bulk_upsert", views.bulk_upsert_contacts, name="panic_contacts_upsert"),
    path("api/push/register", views_push.register_push, name="panic_push_register"),
    path("api/relay_submit", views_relay.relay_submit, name="panic_relay_submit"),
    path("api/vehicle/ping", views_vehicle.ping, name="panic_vehicle_ping"),
    path("api/vehicle/live", views_vehicle.live, name="panic_vehicle_live"),
    path("api/vehicle/tracks", views_vehicle.tracks, name="panic_vehicle_tracks"),
    path("api/waypoints", views_waypoints.list_waypoints, name="panic_waypoints"),
    path("api/stream", views_stream.sse_stream, name="panic_sse_stream"),
    path("api/incidents/<int:pk>/ack", views_actions.ack, name="panic_ack"),
    path("api/incidents/<int:pk>/resolve", views_actions.resolve, name="panic_resolve"),
    path("webhooks/clickatell/inbound/", views.clickatell_inbound, name="panic_clickatell_inbound"),
    path("webhooks/clickatell/status/", views.clickatell_status, name="panic_clickatell_status"),
    path("ussd/handle", views_ussd.ussd_handle, name="panic_ussd_handle"),
]
