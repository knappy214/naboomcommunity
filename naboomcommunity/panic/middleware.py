from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


class VehiclePingRateLimitMiddleware:
    """Limit tracker update frequency to protect the API."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.limit_per_minute = int(
            getattr(settings, "PANIC_VEHICLE_PING_RATE_LIMIT_PER_MINUTE", 120)
        )

    def __call__(self, request):
        if request.path.rstrip("/").endswith("/panic/api/vehicle/ping"):
            token = request.headers.get("X-Vehicle-Token") or request.GET.get("token")
            if token:
                cache_key = f"panic:vehicle:{token}:count"
                count = cache.get(cache_key, 0) + 1
                if count > self.limit_per_minute:
                    return JsonResponse({"detail": "rate limit exceeded"}, status=429)
                cache.set(cache_key, count, timeout=60)
        return self.get_response(request)
