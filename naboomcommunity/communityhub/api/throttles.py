"""Throttling rules for community hub endpoints."""
from rest_framework.throttling import ScopedRateThrottle


class PostBurstRateThrottle(ScopedRateThrottle):
    scope = "community_post_burst"


class AlertRateThrottle(ScopedRateThrottle):
    scope = "community_alert"
