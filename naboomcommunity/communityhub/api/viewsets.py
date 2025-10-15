"""REST API endpoints for the community hub."""
from __future__ import annotations

from datetime import timedelta

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consumers import broadcast_new_post, broadcast_new_thread
from ..models import (
    AuditLog,
    Channel,
    ChannelInvite,
    ChannelJoinRequest,
    ChannelMembership,
    Device,
    EventMeta,
    EventRSVP,
    Post,
    Report,
    Thread,
)
from .permissions import IsAuthenticatedAndActive, IsChannelMember, IsChannelModeratorOrReadOnly
from .serializers import (
    AuditLogSerializer,
    AlertSerializer,
    ChannelInviteSerializer,
    ChannelJoinRequestSerializer,
    ChannelMembershipSerializer,
    ChannelSerializer,
    DeviceSerializer,
    EventMetaSerializer,
    EventRSVPSerializer,
    PostSerializer,
    ReportSerializer,
    ThreadSerializer,
)
from .throttles import AlertRateThrottle, PostBurstRateThrottle


class ChannelViewSet(viewsets.ModelViewSet):
    """Expose channels with membership awareness."""

    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Channel.objects.filter(is_active=True, is_private=False)
        
        # Optimized query with select_related and prefetch_related
        return Channel.objects.select_related().prefetch_related(
            "memberships",
            "memberships__user",
            "memberships__user__profile"
        ).filter(
            is_active=True
        ).filter(
            Q(is_private=False) | Q(memberships__user=user, memberships__is_active=True)
        ).distinct()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedAndActive])
    def join(self, request, pk=None):
        channel = self.get_object()
        membership, created = ChannelMembership.objects.get_or_create(
            user=request.user,
            channel=channel,
            defaults={"role": ChannelMembership.Role.MEMBER},
        )
        if not created and membership.is_active:
            return Response({"detail": _("Already a member.")}, status=status.HTTP_200_OK)
        membership.is_active = True
        membership.save(update_fields=["is_active"])
        return Response(ChannelMembershipSerializer(membership, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedAndActive])
    def leave(self, request, pk=None):
        channel = self.get_object()
        try:
            membership = ChannelMembership.objects.get(user=request.user, channel=channel)
        except ChannelMembership.DoesNotExist:
            return Response({"detail": _("Not a member.")}, status=status.HTTP_400_BAD_REQUEST)
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelInviteViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelInviteSerializer
    permission_classes = [IsChannelModeratorOrReadOnly]

    def get_queryset(self):
        return ChannelInvite.objects.select_related("channel")

    def perform_create(self, serializer):
        expires_at = timezone.now() + timedelta(days=7)
        channel = serializer.validated_data["channel"]
        if not ChannelMembership.objects.filter(
            user=self.request.user,
            channel=channel,
            role__in=[ChannelMembership.Role.MODERATOR, ChannelMembership.Role.MANAGER],
            is_active=True,
        ).exists():
            raise PermissionDenied("Only moderators may invite members.")
        serializer.save(invited_by=self.request.user, expires_at=expires_at)


class ChannelJoinRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelJoinRequestSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        if self.request.method in SAFE_METHODS:
            member_channel_ids = ChannelMembership.objects.filter(
                user=user, is_active=True
            ).values_list("channel_id", flat=True)
            return ChannelJoinRequest.objects.select_related("channel", "requester").filter(
                Q(requester=user) | Q(channel_id__in=member_channel_ids)
            )
        # Moderators see their channels' requests
        moderator_channel_ids = ChannelMembership.objects.filter(
            user=user,
            role__in=[ChannelMembership.Role.MODERATOR, ChannelMembership.Role.MANAGER],
            is_active=True,
        ).values_list("channel_id", flat=True)
        return ChannelJoinRequest.objects.filter(channel_id__in=moderator_channel_ids)

    def perform_create(self, serializer):
        channel = serializer.validated_data["channel"]
        if not channel.allow_join_requests:
            raise PermissionDenied("Join requests are disabled for this channel.")
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsChannelModeratorOrReadOnly])
    def approve(self, request, pk=None):
        join_request = self.get_object()
        join_request.review(request.user, join_request.Status.APPROVED)
        ChannelMembership.objects.update_or_create(
            user=join_request.requester,
            channel=join_request.channel,
            defaults={"role": ChannelMembership.Role.MEMBER, "is_active": True},
        )
        return Response(ChannelJoinRequestSerializer(join_request, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsChannelModeratorOrReadOnly])
    def decline(self, request, pk=None):
        join_request = self.get_object()
        join_request.review(request.user, join_request.Status.DECLINED)
        return Response(ChannelJoinRequestSerializer(join_request, context={"request": request}).data)


class ThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticatedAndActive, IsChannelMember]
    throttle_classes = [PostBurstRateThrottle]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Thread.objects.none()
        
        # Optimized query with select_related and prefetch_related to avoid N+1 queries
        return Thread.objects.select_related(
            "channel", 
            "author",
            "author__profile"  # Include user profile for author
        ).prefetch_related(
            "posts",
            "posts__author",  # Prefetch post authors
            "channel__memberships"  # Prefetch channel memberships
        ).filter(
            channel__memberships__user=user,
            channel__memberships__is_active=True
        ).distinct().order_by("-created_at")

    def perform_create(self, serializer):
        channel = serializer.validated_data["channel"]
        if not ChannelMembership.objects.filter(
            user=self.request.user, channel=channel, is_active=True
        ).exists():
            raise PermissionDenied("User must belong to the channel to create a thread.")
        thread = serializer.save()
        AuditLog.objects.create(
            actor=self.request.user,
            channel=channel,
            thread=thread,
            action="thread.created",
            context={"title": thread.title},
        )
        try:
            async_to_sync(broadcast_new_thread)(thread)
        except Exception:  # pragma: no cover - channel layer misconfiguration
            AuditLog.objects.create(
                actor=self.request.user,
                channel=channel,
                thread=thread,
                action="thread.broadcast_failed",
            )


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedAndActive, IsChannelMember]
    throttle_classes = [PostBurstRateThrottle]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Post.objects.none()
        
        # Optimized query with select_related and prefetch_related to avoid N+1 queries
        return Post.objects.select_related(
            "thread", 
            "channel", 
            "author", 
            "author__profile"  # Include user profile for author
        ).prefetch_related(
            "thread__posts",  # Prefetch related posts in thread
            "channel__memberships"  # Prefetch channel memberships
        ).filter(
            channel__memberships__user=user,
            channel__memberships__is_active=True
        ).distinct()

    def perform_create(self, serializer):
        with transaction.atomic():
            post = serializer.save()
            AuditLog.objects.create(
                actor=self.request.user,
                channel=post.channel,
                thread=post.thread,
                post=post,
                action="post.created",
            )
            try:
                async_to_sync(broadcast_new_post)(post)
            except Exception:  # pragma: no cover - channel layer misconfiguration
                AuditLog.objects.create(
                    actor=self.request.user,
                    channel=post.channel,
                    thread=post.thread,
                    post=post,
                    action="post.broadcast_failed",
                )
            return post

    @action(detail=True, methods=["post"], permission_classes=[IsChannelModeratorOrReadOnly])
    def soft_delete(self, request, pk=None):
        post = self.get_object()
        post.soft_delete(by=request.user)
        AuditLog.objects.create(
            actor=request.user,
            channel=post.channel,
            thread=post.thread,
            post=post,
            action="post.deleted",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsChannelModeratorOrReadOnly])
    def restore(self, request, pk=None):
        post = self.get_object()
        post.restore()
        AuditLog.objects.create(
            actor=request.user,
            channel=post.channel,
            thread=post.thread,
            post=post,
            action="post.restored",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlertViewSet(PostViewSet):
    serializer_class = AlertSerializer
    throttle_classes = [AlertRateThrottle]

    def get_queryset(self):
        return super().get_queryset().filter(kind=Post.Kind.ALERT)

    def perform_create(self, serializer):
        serializer.validated_data["kind"] = Post.Kind.ALERT
        thread = serializer.validated_data["thread"]
        if not thread.channel.allow_alerts:
            raise PermissionDenied("Alerts are disabled for this channel.")
        post = super().perform_create(serializer)
        # Kick off async fan-out placeholder
        from ..tasks import fan_out_alert  # imported lazily

        try:
            fan_out_alert.delay(post.pk)
        except Exception:  # pragma: no cover - broker connectivity issues
            # Defer retry to audit logs; realtime clients will still receive websocket events.
            AuditLog.objects.create(
                actor=self.request.user,
                channel=post.channel,
                thread=post.thread,
                post=post,
                action="alert.enqueue_failed",
            )
        return post


class EventMetaViewSet(viewsets.ModelViewSet):
    serializer_class = EventMetaSerializer
    permission_classes = [IsAuthenticatedAndActive, IsChannelModeratorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        channel_ids = ChannelMembership.objects.filter(user=user, is_active=True).values_list(
            "channel_id", flat=True
        )
        return EventMeta.objects.select_related("thread", "thread__channel").filter(
            thread__channel_id__in=channel_ids
        )

    def perform_create(self, serializer):
        thread = serializer.validated_data["thread"]
        if not ChannelMembership.objects.filter(
            user=self.request.user,
            channel=thread.channel,
            role__in=[ChannelMembership.Role.MODERATOR, ChannelMembership.Role.MANAGER],
            is_active=True,
        ).exists():
            raise PermissionDenied("Only moderators may create event metadata.")
        serializer.save()


class EventRSVPViewSet(viewsets.ModelViewSet):
    serializer_class = EventRSVPSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        channel_ids = ChannelMembership.objects.filter(user=user, is_active=True).values_list(
            "channel_id", flat=True
        )
        return EventRSVP.objects.select_related("event", "event__thread", "user").filter(
            event__thread__channel_id__in=channel_ids
        )

    def perform_create(self, serializer):
        event = serializer.validated_data["event"]
        if not ChannelMembership.objects.filter(
            user=self.request.user,
            channel=event.thread.channel,
            is_active=True,
        ).exists():
            raise PermissionDenied("Membership required to RSVP.")
        serializer.save(user=self.request.user)


class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticatedAndActive, IsChannelMember]

    def get_queryset(self):
        user = self.request.user
        channel_ids = ChannelMembership.objects.filter(user=user, is_active=True).values_list(
            "channel_id", flat=True
        )
        return Report.objects.select_related("channel", "thread", "post").filter(
            channel_id__in=channel_ids
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        channels = ChannelMembership.objects.filter(user=user, is_active=True).values_list(
            "channel_id", flat=True
        )
        return AuditLog.objects.filter(channel_id__in=channels).select_related(
            "actor", "channel", "thread", "post"
        )


class ThreadSearchView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        channel_id = request.query_params.get("channel")
        member_channel_ids = ChannelMembership.objects.filter(
            user=request.user, is_active=True
        ).values_list("channel_id", flat=True)
        qs = Thread.objects.select_related("channel").filter(channel_id__in=member_channel_ids)
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        if not query:
            results = qs.order_by("-created_at")[:25]
        else:
            search_query = SearchQuery(query, config="simple")
            results = (
                qs.annotate(
                    rank=SearchRank("search_document", search_query),
                    similarity=TrigramSimilarity("title", query),
                )
                .filter(Q(rank__gt=0.1) | Q(similarity__gt=0.2))
                .order_by("-rank", "-similarity")[:25]
            )
        serializer = ThreadSerializer(results, many=True, context={"request": request})
        return Response(serializer.data)


class VapidPublicKeyView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request, *args, **kwargs):
        return Response({"publicKey": settings.WEBPUSH_VAPID_PUBLIC_KEY})
