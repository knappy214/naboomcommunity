"""URL routing for the community hub API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    AlertViewSet,
    AuditLogViewSet,
    ChannelInviteViewSet,
    ChannelJoinRequestViewSet,
    ChannelViewSet,
    DeviceViewSet,
    EventMetaViewSet,
    EventRSVPViewSet,
    PostViewSet,
    ReportViewSet,
    ThreadSearchView,
    ThreadViewSet,
    VapidPublicKeyView,
)

router = DefaultRouter()
router.register(r"channels", ChannelViewSet, basename="community-channel")
router.register(r"invites", ChannelInviteViewSet, basename="community-invite")
router.register(r"join-requests", ChannelJoinRequestViewSet, basename="community-join-request")
router.register(r"threads", ThreadViewSet, basename="community-thread")
router.register(r"posts", PostViewSet, basename="community-post")
router.register(r"alerts", AlertViewSet, basename="community-alert")
router.register(r"events", EventMetaViewSet, basename="community-event")
router.register(r"event-rsvps", EventRSVPViewSet, basename="community-event-rsvp")
router.register(r"devices", DeviceViewSet, basename="community-device")
router.register(r"reports", ReportViewSet, basename="community-report")
router.register(r"audit-log", AuditLogViewSet, basename="community-audit")

urlpatterns = [
    path("", include(router.urls)),
    path("search/threads/", ThreadSearchView.as_view(), name="community-thread-search"),
    path("vapid-key/", VapidPublicKeyView.as_view(), name="community-vapid-key"),
]
