from __future__ import annotations

import json
import time
from typing import Iterable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse

from .models import Incident, PatrolAlert
from .serializers import IncidentSerializer, PatrolAlertSerializer


def _poll_interval() -> float:
    return float(getattr(settings, "PANIC_SSE_POLL_INTERVAL", 5))


def sse_stream(request: HttpRequest) -> HttpResponse:
    if not getattr(settings, "ENABLE_SSE", False):
        return HttpResponse(status=404)

    try:
        last_alert_id = int(request.GET.get("last_alert_id", 0))
    except (TypeError, ValueError):
        last_alert_id = 0

    try:
        last_incident_id = int(request.GET.get("last_incident_id", 0))
    except (TypeError, ValueError):
        last_incident_id = 0

    poll_interval = max(_poll_interval(), 1)

    def event_stream() -> Iterable[str]:
        nonlocal last_alert_id, last_incident_id
        while True:
            incidents = (
                Incident.objects.filter(id__gt=last_incident_id)
                .select_related("client")
                .order_by("id")[:100]
            )
            for incident in incidents:
                payload = IncidentSerializer(incident).data
                last_incident_id = incident.id
                yield "event: incident\n"
                yield f"data: {json.dumps(payload, default=str)}\n\n"

            alerts = (
                PatrolAlert.objects.select_related("waypoint")
                .filter(id__gt=last_alert_id)
                .order_by("id")[:100]
            )
            for alert in alerts:
                payload = PatrolAlertSerializer(alert).data
                last_alert_id = alert.id
                yield "event: patrol_alert\n"
                yield f"data: {json.dumps(payload, default=str)}\n\n"

            # Heartbeat keepalive
            yield ": keepalive\n\n"
            time.sleep(poll_interval)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response
