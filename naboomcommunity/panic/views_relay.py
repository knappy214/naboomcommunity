from __future__ import annotations

import json

from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Incident, IncidentEvent, InboundMessage


@csrf_exempt
@require_POST
def relay_submit(request: HttpRequest) -> JsonResponse:
    if not request.body:
        return HttpResponseBadRequest("missing payload")
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")

    frames = payload.get("frames", [])
    if not isinstance(frames, list):
        return HttpResponseBadRequest("frames must be a list")

    saved = 0
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        incident_ref = frame.get("incident_reference")
        incident = None
        if incident_ref:
            incident = Incident.objects.filter(reference=incident_ref).first()
        InboundMessage.objects.create(
            incident=incident,
            message_id=str(frame.get("id") or ""),
            from_number=str(frame.get("from", "relay")),
            to_number=str(frame.get("to", "dispatcher")),
            body=str(frame.get("body", "")),
            metadata=frame,
        )
        if incident:
            IncidentEvent.objects.create(
                incident=incident,
                kind=IncidentEvent.Kind.UPDATED,
                description="Offline relay frame received",
                metadata=frame,
            )
        saved += 1

    return JsonResponse({"ok": True, "frames_saved": saved})
