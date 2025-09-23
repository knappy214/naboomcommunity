from __future__ import annotations

import uuid
from typing import Optional

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.indexes import GistIndex
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ProvinceChoices(models.TextChoices):
    LIMPOPO = "limpopo", _("Limpopo")
    GAUTENG = "gauteng", _("Gauteng")
    MPUMALANGA = "mpumalanga", _("Mpumalanga")
    NORTH_WEST = "north_west", _("North West")
    FREE_STATE = "free_state", _("Free State")
    NORTHERN_CAPE = "northern_cape", _("Northern Cape")
    KWAZULU_NATAL = "kwazulu_natal", _("KwaZulu-Natal")
    EASTERN_CAPE = "eastern_cape", _("Eastern Cape")
    WESTERN_CAPE = "western_cape", _("Western Cape")


class ClientProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="panic_client_profiles",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    province = models.CharField(
        max_length=32, choices=ProvinceChoices.choices, default=ProvinceChoices.LIMPOPO
    )
    location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [
            GistIndex(fields=["location"], name="panic_client_location_gix"),
            models.Index(fields=["province"], name="panic_client_province_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.full_name


class EmergencyContact(models.Model):
    client = models.ForeignKey(
        ClientProfile,
        related_name="contacts",
        on_delete=models.CASCADE,
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=32)
    relationship = models.CharField(max_length=120, blank=True)
    priority = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    last_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("client", "phone_number")
        ordering = ["priority", "full_name"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.full_name} ({self.phone_number})"


class Responder(models.Model):
    class ResponderType(models.TextChoices):
        INDIVIDUAL = "individual", _("Individual")
        COMPANY = "company", _("Company")
        SERVICE = "service", _("Service Provider")

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    responder_type = models.CharField(
        max_length=32, choices=ResponderType.choices, default=ResponderType.INDIVIDUAL
    )
    province = models.CharField(
        max_length=32, choices=ProvinceChoices.choices, default=ProvinceChoices.LIMPOPO
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["province"], name="panic_responder_province_idx")]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.full_name


class PushDevice(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", _("Android")
        IOS = "ios", _("iOS")
        WEB = "web", _("Web")
        UNKNOWN = "unknown", _("Unknown")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="panic_push_devices",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    client = models.ForeignKey(
        ClientProfile,
        related_name="push_devices",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=16, choices=Platform.choices, default=Platform.UNKNOWN)
    app_version = models.CharField(max_length=32, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.token} ({self.platform})"


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        ACKNOWLEDGED = "acknowledged", _("Acknowledged")
        RESOLVED = "resolved", _("Resolved")
        CANCELLED = "cancelled", _("Cancelled")

    class Priority(models.IntegerChoices):
        LOW = 1, _("Low")
        MEDIUM = 2, _("Medium")
        HIGH = 3, _("High")
        CRITICAL = 4, _("Critical")

    client = models.ForeignKey(
        ClientProfile,
        related_name="incidents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reported_incidents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reference = models.CharField(max_length=32, unique=True, default="", blank=True)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=64, blank=True)
    priority = models.PositiveSmallIntegerField(
        choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    province = models.CharField(
        max_length=32, choices=ProvinceChoices.choices, default=ProvinceChoices.LIMPOPO
    )
    context = models.JSONField(default=dict, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            GistIndex(fields=["location"], name="panic_incident_location_gix"),
            models.Index(fields=["status"], name="panic_incident_status_idx"),
            models.Index(fields=["province", "status"], name="panic_incident_province_idx"),
        ]

    def save(self, *args, **kwargs):  # pragma: no cover - trivial wrapper
        if not self.reference:
            self.reference = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"Incident {self.reference}"


class IncidentEvent(models.Model):
    class Kind(models.TextChoices):
        CREATED = "created", _("Created")
        UPDATED = "updated", _("Updated")
        ESCALATED = "escalated", _("Escalated")
        ACKNOWLEDGED = "acknowledged", _("Acknowledged")
        RESOLVED = "resolved", _("Resolved")
        MESSAGE_INBOUND = "message_inbound", _("Inbound Message")
        MESSAGE_OUTBOUND = "message_outbound", _("Outbound Message")

    incident = models.ForeignKey(
        Incident,
        related_name="events",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="panic_events",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.incident.reference}: {self.kind}"


class InboundMessage(models.Model):
    incident = models.ForeignKey(
        Incident,
        related_name="inbound_messages",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    message_id = models.CharField(max_length=128, blank=True)
    from_number = models.CharField(max_length=32)
    to_number = models.CharField(max_length=32)
    body = models.TextField()
    received_at = models.DateTimeField(default=timezone.now)
    provider = models.CharField(max_length=32, default="clickatell")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-received_at"]


class OutboundMessage(models.Model):
    incident = models.ForeignKey(
        Incident,
        related_name="outbound_messages",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    message_id = models.CharField(max_length=128, blank=True)
    to_number = models.CharField(max_length=32)
    body = models.TextField()
    status = models.CharField(max_length=32, default="queued")
    sent_at = models.DateTimeField(default=timezone.now)
    provider = models.CharField(max_length=32, default="clickatell")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-sent_at"]


class EscalationRule(models.Model):
    name = models.CharField(max_length=255)
    province = models.CharField(
        max_length=32, choices=ProvinceChoices.choices, default=ProvinceChoices.LIMPOPO
    )
    delay_seconds = models.PositiveIntegerField(default=120)
    active = models.BooleanField(default=True)
    only_for_priority = models.PositiveSmallIntegerField(
        choices=Incident.Priority.choices,
        null=True,
        blank=True,
        help_text="Limit to incidents with the specified minimum priority.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["province", "delay_seconds"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.name


class EscalationTarget(models.Model):
    class TargetType(models.TextChoices):
        RESPONDER = "responder", _("Responder")
        CONTACT = "contact", _("Emergency Contact")
        PHONE_NUMBER = "phone", _("Phone Number")
        WEBHOOK = "webhook", _("Webhook")

    class Channel(models.TextChoices):
        SMS = "sms", _("SMS")
        PUSH = "push", _("Push Notification")
        EMAIL = "email", _("Email")
        CALL = "call", _("Phone Call")

    rule = models.ForeignKey(
        EscalationRule,
        related_name="targets",
        on_delete=models.CASCADE,
    )
    target_type = models.CharField(max_length=16, choices=TargetType.choices)
    channel = models.CharField(max_length=16, choices=Channel.choices, default=Channel.SMS)
    responder = models.ForeignKey(
        Responder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="escalation_targets",
    )
    contact = models.ForeignKey(
        EmergencyContact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="escalation_targets",
    )
    destination = models.CharField(
        max_length=255,
        blank=True,
        help_text="Fallback destination when a responder/contact is not provided.",
    )
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def resolve_destination(self) -> Optional[str]:
        if self.responder and self.responder.phone_number:
            return self.responder.phone_number
        if self.contact and self.contact.phone_number:
            return self.contact.phone_number
        return self.destination or None

    def __str__(self) -> str:  # pragma: no cover - display helper
        dest = self.resolve_destination() or "unknown"
        return f"{self.get_channel_display()} -> {dest}"


class Vehicle(models.Model):
    name = models.CharField(max_length=120)
    token = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    last_position = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    speed_kph = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    heading_deg = models.SmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(359)],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.name


class VehiclePosition(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="positions")
    position = gis_models.PointField(geography=True, srid=4326)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    speed_kph = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    heading_deg = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["vehicle", "-recorded_at"], name="panic_vehicle_track_idx"),
            GistIndex(fields=["position"], name="panic_vehicle_position_gix"),
        ]


class PatrolWaypoint(models.Model):
    name = models.CharField(max_length=120)
    point = gis_models.PointField(geography=True, srid=4326)
    radius_m = models.PositiveIntegerField(default=100)
    province = models.CharField(
        max_length=32, choices=ProvinceChoices.choices, default=ProvinceChoices.LIMPOPO
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [GistIndex(fields=["point"], name="panic_waypoint_point_gix")]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.name


class PatrolRoute(models.Model):
    name = models.CharField(max_length=120)
    waypoints = models.ManyToManyField(
        "PatrolWaypoint", through="PatrolRouteWaypoint", related_name="routes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.name


class PatrolRouteWaypoint(models.Model):
    route = models.ForeignKey("PatrolRoute", on_delete=models.CASCADE)
    waypoint = models.ForeignKey(PatrolWaypoint, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("route", "waypoint")
        ordering = ["order"]


class PatrolShift(models.Model):
    name = models.CharField(max_length=120)
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="shifts"
    )
    route = models.ForeignKey(
        "PatrolRoute", on_delete=models.SET_NULL, null=True, blank=True, related_name="shifts"
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.name


class PatrolAlert(models.Model):
    class Kind(models.TextChoices):
        MISSED = "missed", _("Missed Waypoint")
        CHECK_IN = "check_in", _("Check-in")
        INCIDENT = "incident", _("Incident")

    shift = models.ForeignKey(
        "PatrolShift", on_delete=models.CASCADE, related_name="alerts"
    )
    waypoint = models.ForeignKey(
        PatrolWaypoint, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts"
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def acknowledge(self) -> None:
        self.acknowledged_at = timezone.now()
        self.save(update_fields=["acknowledged_at"])


# Import Wagtail admin configuration to register snippets
from . import wagtail_admin  # noqa: E402
