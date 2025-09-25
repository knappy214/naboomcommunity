"""Django Channels consumers for realtime updates."""
from __future__ import annotations

from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .models import ChannelMembership, Post, Thread


class ChannelConsumer(AsyncJsonWebsocketConsumer):
    """Realtime updates for a specific forum channel."""

    async def connect(self) -> None:  # pragma: no cover - exercised by runtime
        user = self.scope.get("user")
        channel_id = self.scope["url_route"]["kwargs"].get("channel_id")
        self.channel_group_name = f"community.channel.{channel_id}"
        if isinstance(user, AnonymousUser):
            await self.close(code=4401)
            return
        has_access = await self._user_in_channel(user.id, channel_id)
        if not has_access:
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.channel_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:  # pragma: no cover
        await self.channel_layer.group_discard(self.channel_group_name, self.channel_name)

    async def receive_json(self, content: Any, **kwargs) -> None:
        # Realtime API is currently read-only; clients receive broadcast events
        await self.send_json({"type": "noop"})

    async def new_thread(self, event: dict[str, Any]) -> None:
        await self.send_json(event)

    async def new_post(self, event: dict[str, Any]) -> None:
        await self.send_json(event)

    @database_sync_to_async
    def _user_in_channel(self, user_id: int, channel_id: str) -> bool:
        return ChannelMembership.objects.filter(
            user_id=user_id,
            channel_id=channel_id,
            is_active=True,
        ).exists()


async def broadcast_new_thread(thread: Thread) -> None:
    from channels.layers import get_channel_layer

    layer = get_channel_layer()
    payload = {
        "type": "new_thread",
        "threadId": thread.pk,
        "channelId": thread.channel_id,
        "title": thread.title,
        "summary": thread.summary,
    }
    await layer.group_send(f"community.channel.{thread.channel_id}", payload)


async def broadcast_new_post(post: Post) -> None:
    from channels.layers import get_channel_layer

    layer = get_channel_layer()
    payload = {
        "type": "new_post",
        "postId": post.pk,
        "threadId": post.thread_id,
        "channelId": post.channel_id,
        "kind": post.kind,
        "body": post.body,
    }
    await layer.group_send(f"community.channel.{post.channel_id}", payload)
