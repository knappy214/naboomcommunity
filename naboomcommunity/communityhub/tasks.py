"""Celery tasks for the community hub."""
from __future__ import annotations

import logging
from typing import Iterable

try:
    from celery import shared_task
except ImportError:  # pragma: no cover - fallback when Celery unavailable
    def shared_task(*decorator_args, **decorator_kwargs):
        def decorator(func):
            def delay(*args, **kwargs):
                return func(*args, **kwargs)

            func.delay = delay
            return func

        return decorator

from django.conf import settings

from .models import Device, Post

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def fan_out_alert(self, post_id: int) -> None:
    """Distribute alerts to registered devices."""

    try:
        post = Post.objects.select_related("channel", "author").get(pk=post_id)
    except Post.DoesNotExist:  # pragma: no cover - guard against race conditions
        logger.warning("Alert fan-out skipped; post %s missing", post_id)
        return

    devices: Iterable[Device] = Device.objects.filter(user__community_memberships__channel=post.channel).distinct()
    for device in devices:
        try:
            if device.kind == Device.Kind.EXPO:
                _send_expo_notification(device, post)
            else:
                _send_webpush_notification(device, post)
            device.mark_success()
        except Exception as exc:  # pragma: no cover - network dependent
            logger.exception("Failed sending notification to %s", device.pk)
            device.mark_failure(str(exc))


def _alert_payload(post: Post) -> dict[str, str]:
    teaser = post.body[: post.channel.teaser_character_limit]
    return {
        "title": post.thread.title if post.thread_id else post.channel.name,
        "body": teaser,
        "channel": post.channel.slug,
        "postId": str(post.pk),
        "threadId": str(post.thread_id),
    }


def _send_expo_notification(device: Device, post: Post) -> None:
    try:
        from exponent_server_sdk import PushClient, PushMessage
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Expo push dependencies missing") from exc

    message = PushMessage(to=device.token, title=_alert_payload(post)["title"], body=_alert_payload(post)["body"], data=_alert_payload(post))
    PushClient().publish(message)


def _send_webpush_notification(device: Device, post: Post) -> None:
    try:
        from pywebpush import webpush  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("pywebpush dependency missing") from exc

    payload = _alert_payload(post)
    webpush(
        subscription_info=device.token,
        data=str(payload),
        vapid_private_key=getattr(settings, "WEBPUSH_VAPID_PRIVATE_KEY", ""),
        vapid_claims={"sub": getattr(settings, "WEBPUSH_VAPID_CLAIM_SUBJECT", "mailto:admin@example.com")},
    )
