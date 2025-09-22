from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from .models import PatrolWaypoint


@require_GET
def list_waypoints(request: HttpRequest) -> JsonResponse:
    province = request.GET.get("province")
    queryset = PatrolWaypoint.objects.filter(is_active=True)
    if province:
        queryset = queryset.filter(province=province)

    waypoints = [
        {
            "id": waypoint.id,
            "name": waypoint.name,
            "lat": waypoint.point.y,
            "lng": waypoint.point.x,
            "radius_m": waypoint.radius_m,
            "province": waypoint.province,
        }
        for waypoint in queryset.order_by("name")
    ]
    return JsonResponse({"waypoints": waypoints})
