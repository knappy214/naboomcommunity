from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Incident, IncidentEvent


def _change_status(incident: Incident, status: str, event_kind: str) -> None:
    timestamp = timezone.now()
    updates = {"status": status}
    if status == Incident.Status.ACKNOWLEDGED and not incident.acknowledged_at:
        updates["acknowledged_at"] = timestamp
        incident.acknowledged_at = timestamp
    if status == Incident.Status.RESOLVED:
        updates["resolved_at"] = timestamp
        incident.resolved_at = timestamp
    incident.updated_at = timestamp
    incident.status = status
    incident.save(update_fields=[*updates.keys(), "updated_at"])

    IncidentEvent.objects.create(
        incident=incident,
        kind=event_kind,
        description=f"Incident marked as {status}",
        metadata={"status": status},
    )


@csrf_exempt
@require_POST
def ack(request: HttpRequest, pk: int) -> JsonResponse:
    incident = get_object_or_404(Incident, pk=pk)
    if incident.status != Incident.Status.ACKNOWLEDGED:
        _change_status(incident, Incident.Status.ACKNOWLEDGED, IncidentEvent.Kind.ACKNOWLEDGED)
    return JsonResponse({"ok": True, "status": incident.status})


@csrf_exempt
@require_POST
def resolve(request: HttpRequest, pk: int) -> JsonResponse:
    incident = get_object_or_404(Incident, pk=pk)
    if incident.status != Incident.Status.RESOLVED:
        _change_status(incident, Incident.Status.RESOLVED, IncidentEvent.Kind.RESOLVED)
    return JsonResponse({"ok": True, "status": incident.status})
