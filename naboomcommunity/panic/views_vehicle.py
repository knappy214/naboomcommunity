from __future__ import annotations

import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.gis.geos import Point
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Vehicle, VehiclePosition


def _vehicle_payload(request: HttpRequest) -> dict:
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - upstream
            raise ValueError("invalid json") from exc
    return request.GET.dict()


@csrf_exempt
@require_POST
def ping(request: HttpRequest) -> JsonResponse:
    try:
        data = _vehicle_payload(request)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    token = request.headers.get("X-Vehicle-Token") or data.get("token")
    if not token:
        return HttpResponseForbidden("missing token")

    try:
        vehicle = Vehicle.objects.get(token=token, is_active=True)
    except Vehicle.DoesNotExist:
        return HttpResponseForbidden("invalid token")

    try:
        lat, lng = float(data["lat"]), float(data["lng"])
    except (KeyError, TypeError, ValueError):
        return HttpResponseBadRequest("lat/lng required")

    recorded_at = timezone.now()
    ts = data.get("ts")
    if ts:
        try:
            recorded_at = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            recorded_at = timezone.now()

    point = Point(float(lng), float(lat))
    speed_value = None
    if "speed_kph" in data:
        try:
            speed_value = float(data["speed_kph"])
        except (TypeError, ValueError):
            speed_value = None

    heading_value = None
    if "heading_deg" in data:
        try:
            heading_value = int(float(data["heading_deg"])) % 360
        except (TypeError, ValueError):
            heading_value = None

    VehiclePosition.objects.create(
        vehicle=vehicle,
        position=point,
        recorded_at=recorded_at,
        speed_kph=speed_value,
        heading_deg=heading_value,
    )

    vehicle.last_position = point
    vehicle.last_seen_at = recorded_at
    vehicle.speed_kph = speed_value
    vehicle.heading_deg = heading_value
    vehicle.save(update_fields=["last_position", "last_seen_at", "speed_kph", "heading_deg"])

    return JsonResponse({"ok": True})


@require_GET
def live(request: HttpRequest) -> JsonResponse:
    vehicles = Vehicle.objects.filter(is_active=True, last_position__isnull=False)
    features = []
    for vehicle in vehicles:
        point = vehicle.last_position
        if not point:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [point.x, point.y]},
                "properties": {
                    "id": vehicle.id,
                    "name": vehicle.name,
                    "last_seen_at": vehicle.last_seen_at.isoformat() if vehicle.last_seen_at else None,
                    "speed_kph": float(vehicle.speed_kph) if vehicle.speed_kph is not None else None,
                    "heading_deg": vehicle.heading_deg,
                },
            }
        )
    return JsonResponse({"type": "FeatureCollection", "features": features})


@require_GET
def tracks(request: HttpRequest) -> JsonResponse:
    default_minutes = int(getattr(settings, "PANIC_TRACK_HISTORY_MINUTES", 60))
    try:
        minutes = int(request.GET.get("minutes", default_minutes))
    except (TypeError, ValueError):
        minutes = default_minutes
    vehicle_id = request.GET.get("vehicle")
    cutoff = timezone.now() - timedelta(minutes=max(minutes, 1))

    queryset = VehiclePosition.objects.filter(recorded_at__gte=cutoff).select_related("vehicle")
    if vehicle_id:
        queryset = queryset.filter(vehicle_id=vehicle_id)

    history: dict[int, list[dict[str, object]]] = {}
    for position in queryset.order_by("vehicle_id", "-recorded_at")[:1000]:
        history.setdefault(position.vehicle_id, []).append(
            {
                "lat": position.position.y,
                "lng": position.position.x,
                "recorded_at": position.recorded_at.isoformat(),
                "speed_kph": float(position.speed_kph) if position.speed_kph is not None else None,
                "heading_deg": position.heading_deg,
            }
        )

    return JsonResponse({"vehicles": history})
