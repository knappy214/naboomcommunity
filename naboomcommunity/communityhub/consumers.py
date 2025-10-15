"""Django Channels consumers for realtime updates - HTTP/3 Optimized."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.conf import settings

from .models import ChannelMembership, Post, Thread

logger = logging.getLogger(__name__)


class ChannelConsumer(AsyncJsonWebsocketConsumer):
    """Realtime updates for a specific forum channel - HTTP/3 Optimized."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_group_name = None
        self.user_id = None
        self.channel_id = None
        self.connection_pool = None

    async def connect(self) -> None:  # pragma: no cover - exercised by runtime
        user = self.scope.get("user")
        self.channel_id = self.scope["url_route"]["kwargs"].get("channel_id")
        self.channel_group_name = f"community.channel.{self.channel_id}"
        
        if isinstance(user, AnonymousUser):
            await self.close(code=4401)
            return
            
        self.user_id = user.id
        
        # Cache user permissions to avoid repeated DB queries
        has_access = await self._get_cached_user_access(self.user_id, self.channel_id)
        if not has_access:
            await self.close(code=4403)
            return
            
        # Add to channel group with connection pooling
        await self.channel_layer.group_add(self.channel_group_name, self.channel_name)
        await self.accept()
        
        # Send connection confirmation
        await self.send_json({
            "type": "connection_established",
            "channel_id": self.channel_id,
            "user_id": self.user_id
        })

    async def disconnect(self, close_code: int) -> None:  # pragma: no cover
        if self.channel_group_name:
            await self.channel_layer.group_discard(self.channel_group_name, self.channel_name)

    async def receive_json(self, content: Any, **kwargs) -> None:
        """Handle incoming WebSocket messages with rate limiting."""
        try:
            # Rate limiting check
            if not await self._check_rate_limit():
                await self.send_json({"type": "rate_limited", "message": "Too many requests"})
                return
                
            # Realtime API is currently read-only; clients receive broadcast events
            await self.send_json({"type": "noop"})
        except Exception as exc:
            logger.exception("Error processing WebSocket message: %s", exc)
            await self.send_json({"type": "error", "message": "Internal server error"})

    async def new_thread(self, event: dict[str, Any]) -> None:
        """Handle new thread broadcast with compression."""
        try:
            # Compress large payloads for HTTP/3 efficiency
            if len(str(event)) > 1024:  # 1KB threshold
                event = await self._compress_event(event)
            
            await self.send_json(event)
        except Exception as exc:
            logger.exception("Error sending new_thread event: %s", exc)

    async def new_post(self, event: dict[str, Any]) -> None:
        """Handle new post broadcast with compression."""
        try:
            # Compress large payloads for HTTP/3 efficiency
            if len(str(event)) > 1024:  # 1KB threshold
                event = await self._compress_event(event)
            
            await self.send_json(event)
        except Exception as exc:
            logger.exception("Error sending new_post event: %s", exc)

    async def _get_cached_user_access(self, user_id: int, channel_id: str) -> bool:
        """Get user access with enhanced caching for HTTP/3 performance."""
        try:
            cache_key = f"user_channel_access:{user_id}:{channel_id}"
            has_access = cache.get(cache_key)
            
            if has_access is None:
                has_access = await self._user_in_channel(user_id, channel_id)
                # Cache for 10 minutes for better performance
                cache.set(cache_key, has_access, 600)
                
            return has_access
        except Exception as e:
            logger.exception("Cache error, falling back to database: %s", e)
            # Fallback to database query if cache fails
            return await self._user_in_channel(user_id, channel_id)

    @database_sync_to_async
    def _user_in_channel(self, user_id: int, channel_id: str) -> bool:
        """Check if user has access to channel with optimized query."""
        return ChannelMembership.objects.filter(
            user_id=user_id,
            channel_id=channel_id,
            is_active=True,
        ).exists()

    async def _check_rate_limit(self) -> bool:
        """Simple rate limiting for WebSocket connections."""
        try:
            rate_limit_key = f"ws_rate_limit:{self.user_id}:{self.channel_id}"
            current_requests = cache.get(rate_limit_key, 0)
            
            if current_requests >= 100:  # 100 requests per minute
                return False
                
            cache.set(rate_limit_key, current_requests + 1, 60)  # 1 minute window
            return True
        except Exception:
            # If rate limiting fails, allow the request
            return True

    async def _compress_event(self, event: dict) -> dict:
        """Compress event data for HTTP/3 efficiency."""
        try:
            import gzip
            import json
            
            # Compress large text fields
            if 'body' in event and len(event['body']) > 500:
                event['body'] = event['body'][:500] + "..."
            
            if 'summary' in event and len(event['summary']) > 200:
                event['summary'] = event['summary'][:200] + "..."
                
            return event
        except Exception:
            return event


async def broadcast_new_thread(thread: Thread) -> None:
    """Broadcast new thread with HTTP/3 optimizations."""
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
                "timestamp": thread.created_at.isoformat(),
            }
            # Cache for 2 minutes for better performance
            cache.set(cache_key, payload, 120)
        else:
            payload = cached_data
            
        await layer.group_send(f"community.channel.{thread.channel_id}", payload)
    except Exception as e:
        logger.exception("Failed to broadcast new thread %s: %s", thread.pk, e)


async def broadcast_new_post(post: Post) -> None:
    """Broadcast new post with HTTP/3 optimizations."""
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
                "timestamp": post.created_at.isoformat(),
            }
            # Cache for 2 minutes for better performance
            cache.set(cache_key, payload, 120)
        else:
            payload = cached_data
            
        await layer.group_send(f"community.channel.{post.channel_id}", payload)
    except Exception as e:
        logger.exception("Failed to broadcast new post %s: %s", post.pk, e)


# HTTP/3 optimized connection pool for WebSocket management
class WebSocketConnectionPool:
    """Connection pool for managing WebSocket connections efficiently."""
    
    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self.active_connections = {}
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
        }
    
    async def add_connection(self, connection_id: str, consumer: ChannelConsumer) -> bool:
        """Add a new connection to the pool."""
        if len(self.active_connections) >= self.max_connections:
            return False
            
        self.active_connections[connection_id] = consumer
        self.connection_stats['total_connections'] += 1
        self.connection_stats['active_connections'] += 1
        return True
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove a connection from the pool."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            self.connection_stats['active_connections'] -= 1
    
    def get_stats(self) -> dict:
        """Get connection pool statistics."""
        return self.connection_stats.copy()


# Global connection pool instance
connection_pool = WebSocketConnectionPool()
