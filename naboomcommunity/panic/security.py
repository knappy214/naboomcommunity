from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from django.conf import settings
from django.http import HttpRequest


def _body_bytes(request: HttpRequest) -> bytes:
    return request.body or b""


def _header(request: HttpRequest, name: str) -> Optional[str]:
    return request.headers.get(name) or request.META.get(name)


def verify_clickatell_signature(request: HttpRequest) -> bool:
    """Validate webhook signatures from Clickatell.

    The webhook supports either an HMAC SHA256 signature when
    ``PANIC_WEBHOOK_SECRET`` is configured, or a token fallback using the
    ``CLICKATELL_API_KEY`` value. This keeps development environments easy
    while production can enforce signed payloads.
    """

    secret = getattr(settings, "PANIC_WEBHOOK_SECRET", "")
    if secret:
        provided = _header(request, "X-Clickatell-Signature") or _header(
            request, "X-Hub-Signature-256"
        )
        if not provided:
            return False
        digest = hmac.new(secret.encode("utf-8"), _body_bytes(request), hashlib.sha256).hexdigest()
        return hmac.compare_digest(provided.lower(), digest.lower())

    token = request.GET.get("token") or request.headers.get("X-Auth-Token")
    expected = getattr(settings, "CLICKATELL_API_KEY", "")
    if expected:
        return hmac.compare_digest(str(token or ""), expected)

    # As a final fallback allow unsigned requests (primarily for tests)
    return True
