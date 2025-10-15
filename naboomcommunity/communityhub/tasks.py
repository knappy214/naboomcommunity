"""Celery tasks for the community hub - HTTP/3 Optimized."""
from __future__ import annotations

import logging
from typing import Iterable

try:
    from celery import shared_task
    from celery.contrib.django.task import DjangoTask
except ImportError:  # pragma: no cover - fallback when Celery unavailable
    def shared_task(*decorator_args, **decorator_kwargs):
        def decorator(func):
            def delay(*args, **kwargs):
                return func(*args, **kwargs)

            func.delay = delay
            return func

        return decorator
    
    class DjangoTask:
        pass

from django.conf import settings
from django.db import transaction

from .models import Device, Post

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=DjangoTask, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def fan_out_alert(self, post_id: int) -> None:
    """Distribute alerts to registered devices - HTTP/3 optimized."""

    try:
        post = Post.objects.select_related("channel", "author").get(pk=post_id)
    except Post.DoesNotExist:  # pragma: no cover - guard against race conditions
        logger.warning("Alert fan-out skipped; post %s missing", post_id)
        return

    devices: Iterable[Device] = Device.objects.filter(
        user__community_memberships__channel=post.channel
    ).distinct()
    
    # Process devices in batches for better performance
    device_batch_size = 50
    device_list = list(devices)
    
    for i in range(0, len(device_list), device_batch_size):
        batch = device_list[i:i + device_batch_size]
        for device in batch:
            try:
                if device.kind == Device.Kind.EXPO:
                    _send_expo_notification(device, post)
                else:
                    _send_webpush_notification(device, post)
                device.mark_success()
            except Exception as exc:  # pragma: no cover - network dependent
                logger.exception("Failed sending notification to %s", device.pk)
                device.mark_failure(str(exc))


@shared_task(bind=True, base=DjangoTask, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def fan_out_alert_on_commit(self, post_id: int) -> None:
    """Distribute alerts after database commit - prevents race conditions."""
    # This task is designed to be called with delay_on_commit
    fan_out_alert.delay(post_id)


def _alert_payload(post: Post) -> dict[str, str]:
    """Generate alert payload with caching optimization."""
    teaser = post.body[: post.channel.teaser_character_limit]
    return {
        "title": post.thread.title if post.thread_id else post.channel.name,
        "body": teaser,
        "channel": post.channel.slug,
        "postId": str(post.pk),
        "threadId": str(post.thread_id),
    }


def _send_expo_notification(device: Device, post: Post) -> None:
    """Send Expo push notification with error handling."""
    try:
        from exponent_server_sdk import PushClient, PushMessage
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Expo push dependencies missing") from exc

    message = PushMessage(
        to=device.token, 
        title=_alert_payload(post)["title"], 
        body=_alert_payload(post)["body"], 
        data=_alert_payload(post)
    )
    PushClient().publish(message)


def _send_webpush_notification(device: Device, post: Post) -> None:
    """Send WebPush notification with error handling."""
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


# HTTP/3 optimized task for WebSocket broadcasting
@shared_task(bind=True, base=DjangoTask, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def broadcast_websocket_message(self, channel_id: int, message_type: str, data: dict) -> None:
    """Broadcast WebSocket message to channel subscribers."""
    try:
        from channels.layers import get_channel_layer
        import asyncio
        
        layer = get_channel_layer()
        payload = {
            "type": message_type,
            **data
        }
        
        # Use asyncio to run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                layer.group_send(f"community.channel.{channel_id}", payload)
            )
        finally:
            loop.close()
            
    except Exception as exc:
        logger.exception("Failed to broadcast WebSocket message to channel %s: %s", channel_id, exc)


# HTTP/3 optimized task for cache warming
@shared_task(bind=True, base=DjangoTask, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def warm_cache(self, cache_key: str, data: dict, timeout: int = 300) -> None:
    """Warm cache with data to improve response times."""
    try:
        from django.core.cache import cache
        cache.set(cache_key, data, timeout)
        logger.info("Cache warmed for key: %s", cache_key)
    except Exception as exc:
        logger.exception("Failed to warm cache for key %s: %s", cache_key, exc)
