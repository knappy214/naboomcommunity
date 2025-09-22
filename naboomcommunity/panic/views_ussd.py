from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Incident


@csrf_exempt
@require_POST
def ussd_handle(request: HttpRequest) -> HttpResponse:
    session_id = request.POST.get("sessionId") or request.POST.get("session_id")
    text = request.POST.get("text", "").strip()

    if not text:
        body = "CON Naboom Panic\n1. Trigger SOS\n2. Request callback"
    elif text.endswith("1"):
        Incident.objects.create(description="USSD SOS activation", source="ussd")
        body = "END Panic team notified. Stay safe."
    elif text.endswith("2"):
        Incident.objects.create(description="USSD callback request", source="ussd")
        body = "END A responder will call you shortly."
    else:
        body = "END Thank you."

    response = HttpResponse(body, content_type="text/plain")
    if session_id:
        response["X-USSD-Session"] = session_id
    return response
