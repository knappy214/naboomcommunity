from __future__ import annotations

import json

from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ClientProfile, PushDevice


def _payload(request: HttpRequest) -> dict:
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - handled upstream
            raise ValueError("invalid json") from exc
    return request.POST.dict()


@csrf_exempt
@require_POST
def register_push(request: HttpRequest) -> JsonResponse:
    try:
        payload = _payload(request)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    token = payload.get("token")
    if not token:
        return HttpResponseBadRequest("token required")

    client = None
    client_id = payload.get("client_id")
    if client_id:
        client = ClientProfile.objects.filter(id=client_id).first()

    defaults = {
        "platform": payload.get("platform", PushDevice.Platform.UNKNOWN),
        "app_version": payload.get("app_version", ""),
        "client": client,
    }

    PushDevice.objects.update_or_create(
        token=token,
        defaults=defaults,
    )

    return JsonResponse({"ok": True})
