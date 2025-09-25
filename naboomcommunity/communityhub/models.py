"""Core data models for the community hub module."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connections, models, router
from django.db.models import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.models import TranslatableMixin

User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Channel(TranslatableMixin, ClusterableModel, TimeStampedModel):
    """Forum channel configuration exposed as a Wagtail snippet."""

    class Kind(models.TextChoices):
        EMERGENCY = "emergency", _("Emergency")
        MUNICIPAL = "municipal", _("Municipal")
        GENERAL = "general", _("General")
        EVENTS = "events", _("Events")
        FIRE = "fire", _("Fire")
        CUSTOM = "custom", _("Custom")

    class PostingPolicy(models.TextChoices):
        OPEN = "open", _("Open – anyone may post")
        MEMBERS = "members", _("Members only")
        MODERATED = "moderated", _("Moderated")

    class BroadcastScope(models.TextChoices):
        COMMUNITY = "community", _("Entire community")
        CHANNEL = "channel", _("Channel members")

    slug = models.SlugField(unique=True, help_text=_("Stable channel identifier used in URLs."))
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.GENERAL)
    posting_policy = models.CharField(
        max_length=16,
        choices=PostingPolicy.choices,
        default=PostingPolicy.MEMBERS,
    )
    is_private = models.BooleanField(
        default=True,
        help_text=_("Private channels require an invite or an approved join request."),
    )
    is_active = models.BooleanField(default=True)
    allow_alerts = models.BooleanField(
        default=True,
        help_text=_("Members may broadcast alerts that are teased to non-members."),
    )
    broadcast_scope = models.CharField(
        max_length=32,
        choices=BroadcastScope.choices,
        default=BroadcastScope.COMMUNITY,
        help_text=_("Determines how alerts fan out to the community."),
    )
    allow_join_requests = models.BooleanField(
        default=True,
        help_text=_("Allow residents to request access without a direct invite."),
    )
    default_alerts_enabled = models.BooleanField(
        default=True,
        help_text=_("Default per-member preference for receiving alerts."),
    )
    default_posts_enabled = models.BooleanField(
        default=True,
        help_text=_("Default per-member preference for regular thread notifications."),
    )
    teaser_character_limit = models.PositiveIntegerField(
        default=280,
        validators=[MinValueValidator(64), MaxValueValidator(1_000)],
        help_text=_("Maximum characters shown to non-members when teasing private alerts."),
    )

    panels = [
        FieldPanel("slug"),
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("kind"),
        FieldPanel("posting_policy"),
        FieldPanel("is_private"),
        FieldPanel("is_active"),
        FieldPanel("allow_alerts"),
        FieldPanel("broadcast_scope"),
        FieldPanel("allow_join_requests"),
        FieldPanel("default_alerts_enabled"),
        FieldPanel("default_posts_enabled"),
        FieldPanel("teaser_character_limit"),
    ]

    class Meta(TranslatableMixin.Meta):
        ordering = ("slug",)
        verbose_name = _("Channel")
        verbose_name_plural = _("Channels")

    def __str__(self) -> str:
        return self.name


class ChannelModerationPolicy(TranslatableMixin, TimeStampedModel):
    """Reusable moderation policies for channels."""

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    auto_approve_join_requests = models.BooleanField(default=False)
    require_alert_approval = models.BooleanField(
        default=False,
        help_text=_("Moderators must approve alerts before they go live."),
    )
    require_post_approval = models.BooleanField(
        default=False,
        help_text=_("Moderators must approve posts before they appear."),
    )
    escalation_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(720)],
        help_text=_("Escalate pending moderation items after N minutes."),
    )

    class Meta(TranslatableMixin.Meta):
        verbose_name = _("Moderation policy")
        verbose_name_plural = _("Moderation policies")

    def __str__(self) -> str:
        return self.name

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("auto_approve_join_requests"),
        FieldPanel("require_alert_approval"),
        FieldPanel("require_post_approval"),
        FieldPanel("escalation_minutes"),
    ]


class ChannelAlertPolicy(TranslatableMixin, TimeStampedModel):
    """Reusable alert distribution policies."""

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    cooldown_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(720)],
        help_text=_("Minimum spacing between alerts from the same user."),
    )
    duplicate_window_minutes = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text=_("Merge similar alerts raised within this window."),
    )
    duplicate_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text=_("Trigram similarity required to merge duplicate alerts."),
    )

    class Meta(TranslatableMixin.Meta):
        verbose_name = _("Alert policy")
        verbose_name_plural = _("Alert policies")

    def __str__(self) -> str:
        return self.name

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("cooldown_minutes"),
        FieldPanel("duplicate_window_minutes"),
        FieldPanel("duplicate_threshold"),
    ]


class ChannelConfiguration(TimeStampedModel):
    """Per-channel policy bindings."""

    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name="configuration")
    moderation_policy = models.ForeignKey(
        ChannelModerationPolicy,
        on_delete=models.PROTECT,
        related_name="channel_configurations",
    )
    alert_policy = models.ForeignKey(
        ChannelAlertPolicy,
        on_delete=models.PROTECT,
        related_name="channel_configurations",
    )

    class Meta:
        verbose_name = _("Channel configuration")
        verbose_name_plural = _("Channel configurations")

    def __str__(self) -> str:
        return _("Configuration for %(channel)s") % {"channel": self.channel}

    panels = [
        FieldPanel("channel"),
        FieldPanel("moderation_policy"),
        FieldPanel("alert_policy"),
    ]


class ChannelInvite(TimeStampedModel):
    """Invite-based onboarding for private channels."""

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="invites")
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="community_invites_sent",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_invites_accepted",
    )

    class Meta:
        verbose_name = _("Channel invite")
        verbose_name_plural = _("Channel invites")
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(("email__isnull", False), ("email__gt", ""))
                    | models.Q(("phone_number__isnull", False), ("phone_number__gt", ""))
                ),
                name="communityhub_invite_contact_required",
            )
        ]

    def mark_accepted(self, user: User) -> None:
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save(update_fields=["accepted_by", "accepted_at"])

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def __str__(self) -> str:
        return f"{self.channel.slug} invite"

    panels = [
        FieldPanel("channel"),
        FieldPanel("email"),
        FieldPanel("phone_number"),
        FieldPanel("expires_at"),
        FieldPanel("accepted_at"),
    ]


class ChannelJoinRequest(TimeStampedModel):
    """Resident requests to join a private channel."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        DECLINED = "declined", _("Declined")
        REVOKED = "revoked", _("Revoked")

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="join_requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_join_requests")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_join_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Join request")
        verbose_name_plural = _("Join requests")
        ordering = ("-created_at",)
        unique_together = ("channel", "requester")

    def review(self, reviewer: User, status: str) -> None:
        if status not in {self.Status.APPROVED, self.Status.DECLINED, self.Status.REVOKED}:
            raise ValueError("Invalid review status")
        self.status = status
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        if status == self.Status.APPROVED:
            membership, created = ChannelMembership.objects.get_or_create(
                user=self.requester,
                channel=self.channel,
                defaults={"role": ChannelMembership.Role.MEMBER},
            )
            if not created and not membership.is_active:
                membership.is_active = True
                membership.save(update_fields=["is_active"])

    def __str__(self) -> str:
        return f"{self.requester} → {self.channel} ({self.status})"

    panels = [
        FieldPanel("channel"),
        FieldPanel("requester"),
        FieldPanel("message"),
        FieldPanel("status"),
    ]


class ChannelMembership(TimeStampedModel):
    """Membership metadata for residents belonging to channels."""

    class Role(models.TextChoices):
        MEMBER = "member", _("Member")
        MODERATOR = "moderator", _("Moderator")
        MANAGER = "manager", _("Manager")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_memberships")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)
    notifications = JSONField(
        default=dict,
        blank=True,
        help_text=_("Per-user notification preferences."),
    )
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Channel membership")
        verbose_name_plural = _("Channel memberships")
        unique_together = ("user", "channel")
        indexes = [
            models.Index(fields=["channel", "role"], name="hub_member_chan_role"),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.channel.slug}"


class Thread(TimeStampedModel):
    """Forum discussion thread."""

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="threads")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_threads")
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    is_pinned = models.BooleanField(default=False)
    pinned_until = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    search_document = SearchVectorField(null=True, editable=False)
    last_post_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["channel", "-created_at"], name="hub_thread_chan_created"),
            GinIndex(
                fields=["search_document"],
                name="hub_thread_search_gin",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.channel.slug})"

    def save(self, *args, **kwargs):
        using = kwargs.get("using") or router.db_for_write(self.__class__, instance=self)
        super().save(*args, **kwargs)
        connection = connections[using]
        if connection.vendor != "postgresql":
            return
        Thread.objects.using(using).filter(pk=self.pk).update(
            search_document=(
                SearchVector("title", weight="A", config="simple")
                + SearchVector("summary", weight="B", config="simple")
            )
        )


class Post(TimeStampedModel):
    """Posts within a thread, including alerts."""

    class Kind(models.TextChoices):
        TEXT = "text", _("Text")
        ALERT = "alert", _("Alert")
        SYSTEM = "system", _("System")

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="posts")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_posts")
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.TEXT)
    body = models.TextField()
    metadata = JSONField(default=dict, blank=True)
    search_document = SearchVectorField(null=True, editable=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_posts_deleted",
    )

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=["channel", "-created_at"], name="hub_post_chan_created"),
            GinIndex(
                fields=["search_document"],
                name="hub_post_search_gin",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind}: {self.body[:40]}"

    def save(self, *args, **kwargs):
        using = kwargs.get("using") or router.db_for_write(self.__class__, instance=self)
        super().save(*args, **kwargs)
        connection = connections[using]
        if connection.vendor != "postgresql":
            return
        Post.objects.using(using).filter(pk=self.pk).update(
            search_document=SearchVector("body", weight="A", config="simple"),
        )

    def soft_delete(self, by: Optional[User] = None) -> None:
        self.is_deleted = True
        self.deleted_by = by
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_by", "deleted_at"])

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_by = None
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_by", "deleted_at"])


class EventMeta(TimeStampedModel):
    """Optional metadata that upgrades a thread into an event discussion."""

    thread = models.OneToOneField(Thread, on_delete=models.CASCADE, related_name="event")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    allow_rsvp = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    external_link = models.URLField(blank=True)

    class Meta:
        verbose_name = _("Event metadata")
        verbose_name_plural = _("Event metadata")

    def __str__(self) -> str:
        return f"Event for {self.thread}"


class EventRSVP(TimeStampedModel):
    """RSVP responses for event threads."""

    class Status(models.TextChoices):
        YES = "yes", _("Attending")
        NO = "no", _("Not attending")
        MAYBE = "maybe", _("Maybe")

    event = models.ForeignKey(EventMeta, on_delete=models.CASCADE, related_name="rsvps")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_event_rsvps")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.YES)
    guests = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(20)])
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ("event", "user")
        verbose_name = _("Event RSVP")
        verbose_name_plural = _("Event RSVPs")

    def __str__(self) -> str:
        return f"{self.user} → {self.event} ({self.status})"


class Device(TimeStampedModel):
    """Push notification device registration."""

    class Kind(models.TextChoices):
        EXPO = "expo", _("Expo push token")
        WEB = "web", _("Web Push subscription")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_devices")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    token = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("kind", "token")
        indexes = [
            models.Index(fields=["user", "kind"], name="hub_device_user_kind"),
        ]
        verbose_name = _("Notification device")
        verbose_name_plural = _("Notification devices")

    def mark_success(self) -> None:
        self.last_success_at = timezone.now()
        self.failure_reason = ""
        self.save(update_fields=["last_success_at", "failure_reason"])

    def mark_failure(self, reason: str) -> None:
        self.last_failure_at = timezone.now()
        self.failure_reason = reason[:250]
        self.save(update_fields=["last_failure_at", "failure_reason"])

    def __str__(self) -> str:
        return f"{self.kind} device for {self.user}"

    panels = [
        FieldPanel("user"),
        FieldPanel("kind"),
        FieldPanel("token"),
        FieldPanel("is_active"),
    ]


class CannedReportReason(TranslatableMixin, TimeStampedModel):
    """Reusable bilingual reasons for moderation reports."""

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta(TranslatableMixin.Meta):
        verbose_name = _("Canned report reason")
        verbose_name_plural = _("Canned report reasons")

    def __str__(self) -> str:
        return self.title

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
    ]


class Report(TimeStampedModel):
    """Moderation reports for posts or threads."""

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_reports")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="reports")
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)
    canned_reason = models.ForeignKey(
        CannedReportReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    reason = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_reports_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Moderation report")
        verbose_name_plural = _("Moderation reports")

    def resolve(self, moderator: User, notes: str = "") -> None:
        self.resolved_by = moderator
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=["resolved_by", "resolved_at", "resolution_notes"])

    def __str__(self) -> str:
        target = self.post or self.thread
        return f"Report on {target}"


class AuditLog(TimeStampedModel):
    """Simple audit log for compliance and accountability."""

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_audit_events",
    )
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    thread = models.ForeignKey(Thread, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    action = models.CharField(max_length=64)
    context = JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Audit event")
        verbose_name_plural = _("Audit events")
        indexes = [
            models.Index(fields=["channel", "created_at"], name="hub_audit_chan_created"),
        ]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.action}"


__all__ = [
    "AuditLog",
    "CannedReportReason",
    "Channel",
    "ChannelAlertPolicy",
    "ChannelConfiguration",
    "ChannelInvite",
    "ChannelJoinRequest",
    "ChannelMembership",
    "ChannelModerationPolicy",
    "Device",
    "EventMeta",
    "EventRSVP",
    "Post",
    "Report",
    "Thread",
]
