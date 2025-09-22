from __future__ import annotations

import json
from typing import Dict

from django.contrib.gis.geos import Point
from django.db import transaction
from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    ClientProfile,
    EmergencyContact,
    Incident,
    IncidentEvent,
    InboundMessage,
    OutboundMessage,
)
from .security import verify_clickatell_signature


def _json_from_request(request: HttpRequest) -> Dict[str, object]:
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - handled in calling view
            raise ValueError("invalid json") from exc
    return {**request.POST.dict(), **request.GET.dict()}


@csrf_exempt
@require_http_methods(["POST"])
def submit_incident(request: HttpRequest) -> JsonResponse:
    """Create an incident entry from panic app clients."""

    try:
        payload = _json_from_request(request)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    client: ClientProfile | None = None
    client_id = payload.get("client_id")
    if client_id:
        client = ClientProfile.objects.filter(id=client_id).first()

    lat = payload.get("lat")
    lng = payload.get("lng")
    point = None
    if lat is not None and lng is not None:
        try:
            point = Point(float(lng), float(lat))
        except (TypeError, ValueError):
            return HttpResponseBadRequest("invalid coordinates")

    default_province = (
        client.province
        if client
        else Incident._meta.get_field("province").get_default()
    )

    with transaction.atomic():
        incident = Incident.objects.create(
            client=client,
            description=str(payload.get("description", "")),
            source=str(payload.get("source", "app")),
            address=str(payload.get("address", "")),
            priority=int(payload.get("priority", Incident.Priority.MEDIUM)),
            province=str(payload.get("province", default_province)),
            location=point,
            context=payload.get("context", {}),
        )

        IncidentEvent.objects.create(
            incident=incident,
            kind=IncidentEvent.Kind.CREATED,
            description=payload.get("event_description", "Panic button activation"),
            metadata={"raw": payload},
        )

    response = {
        "id": incident.id,
        "reference": incident.reference,
        "status": incident.status,
        "created_at": incident.created_at.isoformat(),
    }
    return JsonResponse(response, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def bulk_upsert_contacts(request: HttpRequest) -> JsonResponse:
    try:
        payload = _json_from_request(request)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    client_id = payload.get("client_id")
    if not client_id:
        return HttpResponseBadRequest("client_id required")

    client = ClientProfile.objects.filter(id=client_id).first()
    if not client:
        return HttpResponseBadRequest("invalid client")

    contacts = payload.get("contacts", [])
    if not isinstance(contacts, list):
        return HttpResponseBadRequest("contacts must be a list")

    created = 0
    updated = 0
    for entry in contacts:
        if not isinstance(entry, dict):
            continue
        phone = str(entry.get("phone_number") or "").strip()
        if not phone:
            continue
        defaults = {
            "full_name": entry.get("full_name", ""),
            "relationship": entry.get("relationship", ""),
            "priority": entry.get("priority", 1),
            "is_active": bool(entry.get("is_active", True)),
        }
        obj, was_created = EmergencyContact.objects.update_or_create(
            client=client,
            phone_number=phone,
            defaults=defaults,
        )
        created += int(was_created)
        updated += int(not was_created)

    return JsonResponse({"ok": True, "created": created, "updated": updated})


def _record_message(
    *,
    incident: Incident | None,
    from_number: str,
    to_number: str,
    body: str,
    payload: Dict[str, object],
) -> InboundMessage:
    return InboundMessage.objects.create(
        incident=incident,
        message_id=str(payload.get("message_id") or payload.get("id") or ""),
        from_number=from_number,
        to_number=to_number,
        body=body,
        metadata=payload,
    )


@csrf_exempt
@require_http_methods(["POST"])
def clickatell_inbound(request: HttpRequest) -> JsonResponse:
    if not verify_clickatell_signature(request):
        return JsonResponse({"detail": "unauthorised"}, status=403)

    try:
        payload = _json_from_request(request)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    incident_ref = payload.get("incident_reference")
    incident = None
    if incident_ref:
        incident = Incident.objects.filter(reference=incident_ref).first()

    message = _record_message(
        incident=incident,
        from_number=str(payload.get("from") or payload.get("msisdn") or "unknown"),
        to_number=str(payload.get("to") or payload.get("channel") or "unknown"),
        body=str(payload.get("text", "")),
        payload=payload,
    )

    if incident:
        IncidentEvent.objects.create(
            incident=incident,
            kind=IncidentEvent.Kind.MESSAGE_INBOUND,
            description="Inbound SMS received",
            metadata={"message_id": message.message_id, "payload": payload},
        )

    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST", "GET"])
def clickatell_status(request: HttpRequest) -> JsonResponse:
    # Shared secret validation
    if not verify_clickatell_signature(request):
        return JsonResponse({"detail": "unauthorised"}, status=403)

    payload = _json_from_request(request)
    message_id = payload.get("messageId") or payload.get("message_id")
    status = payload.get("status")

    if not message_id:
        return HttpResponseBadRequest("missing message id")

    OutboundMessage.objects.filter(message_id=message_id).update(
        status=status or "unknown",
        metadata=payload,
    )

    return JsonResponse({"ok": True})
