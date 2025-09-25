"""Permission helpers for the community hub API."""
from __future__ import annotations

from rest_framework import permissions

from ..models import ChannelMembership, Post, Thread


class IsAuthenticatedAndActive(permissions.IsAuthenticated):
    """Ensure authenticated users only."""

    def has_permission(self, request, view):  # type: ignore[override]
        if not super().has_permission(request, view):
            return False
        return request.user.is_active


class IsChannelMember(permissions.BasePermission):
    """Allow access when the user belongs to the channel."""

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        if isinstance(obj, Thread):
            channel = obj.channel
        elif isinstance(obj, Post):
            channel = obj.channel
        else:
            channel = getattr(obj, "channel", None)
        if channel is None:
            return False
        if not request.user.is_authenticated:
            return False
        return ChannelMembership.objects.filter(
            user=request.user, channel=channel, is_active=True
        ).exists()


class IsChannelModeratorOrReadOnly(IsChannelMember):
    """Allow safe methods to members, writes to moderators/managers."""

    def has_permission(self, request, view):  # type: ignore[override]
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        if request.method in permissions.SAFE_METHODS:
            return super().has_object_permission(request, view, obj)
        if not request.user.is_authenticated:
            return False
        if isinstance(obj, Thread):
            channel = obj.channel
        elif isinstance(obj, Post):
            channel = obj.channel
        else:
            channel = getattr(obj, "channel", None)
        if channel is None:
            return False
        return ChannelMembership.objects.filter(
            user=request.user,
            channel=channel,
            role__in=[ChannelMembership.Role.MODERATOR, ChannelMembership.Role.MANAGER],
            is_active=True,
        ).exists()
