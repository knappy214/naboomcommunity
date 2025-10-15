"""Django Channels consumers for realtime updates."""
from __future__ import annotations

from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

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
            
        # Cache user permissions to avoid repeated DB queries
        has_access = await self._get_cached_user_access(user.id, channel_id)
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

    async def _get_cached_user_access(self, user_id: int, channel_id: str) -> bool:
        """Get user channel access with Redis caching and error handling"""
        try:
            cache_key = f"user_channel_access:{user_id}:{channel_id}"
            has_access = cache.get(cache_key)
            
            if has_access is None:
                has_access = await self._user_in_channel(user_id, channel_id)
                cache.set(cache_key, has_access, 300)  # Cache for 5 minutes
                
            return has_access
        except Exception as e:
            # Fallback to database query if cache fails
            return await self._user_in_channel(user_id, channel_id)

    @database_sync_to_async
    def _user_in_channel(self, user_id: int, channel_id: str) -> bool:
        return ChannelMembership.objects.filter(
            user_id=user_id,
            channel_id=channel_id,
            is_active=True,
        ).exists()


async def broadcast_new_thread(thread: Thread) -> None:
    from channels.layers import get_channel_layer

    try:
        layer = get_channel_layer()
        
        # Cache thread data to avoid repeated serialization
        cache_key = f"thread_broadcast:{thread.pk}"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            payload = {
                "type": "new_thread",
                "threadId": thread.pk,
                "channelId": thread.channel_id,
                "title": thread.title,
                "summary": thread.summary,
            }
            cache.set(cache_key, payload, 60)  # Cache for 1 minute
        else:
            payload = cached_data
            
        await layer.group_send(f"community.channel.{thread.channel_id}", payload)
    except Exception as e:
        # Log error but don't fail the thread creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to broadcast new thread {thread.pk}: {e}")


async def broadcast_new_post(post: Post) -> None:
    from channels.layers import get_channel_layer

    try:
        layer = get_channel_layer()
        
        # Cache post data to avoid repeated serialization
        cache_key = f"post_broadcast:{post.pk}"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            payload = {
                "type": "new_post",
                "postId": post.pk,
                "threadId": post.thread_id,
                "channelId": post.channel_id,
                "kind": post.kind,
                "body": post.body,
            }
            cache.set(cache_key, payload, 60)  # Cache for 1 minute
        else:
            payload = cached_data
            
        await layer.group_send(f"community.channel.{post.channel_id}", payload)
    except Exception as e:
        # Log error but don't fail the post creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to broadcast new post {post.pk}: {e}")
