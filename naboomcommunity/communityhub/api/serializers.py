"""Serializers for the community hub REST API."""
from __future__ import annotations

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from wagtail.models import Locale
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

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


class TranslationField(serializers.DictField):
    """Expose available translations for a translatable model field."""

    def __init__(self, field_name: str, **kwargs):
        self._field_name = field_name
        kwargs.setdefault("source", "*")
        kwargs.setdefault("child", serializers.CharField())
        super().__init__(**kwargs)

    def to_representation(self, value):  # type: ignore[override]
        translations: dict[str, str] = {}
        base_locale = getattr(getattr(value, "locale", None), "language_code", None)
        base_value = getattr(value, self._field_name)
        if base_locale:
            translations[base_locale] = base_value
        else:
            default_code = settings.LANGUAGE_CODE.split("-")[0]
            translations[default_code] = base_value
        for code, _label in settings.LANGUAGES:
            if code == base_locale:
                continue
            locale = Locale.objects.filter(language_code=code).first()
            if not locale:
                continue
            try:
                translation = value.get_translation(locale)
            except (AttributeError, value.__class__.DoesNotExist):  # type: ignore[attr-defined]
                continue
            translations[code] = getattr(translation, self._field_name)
        return translations


class ChannelSerializer(serializers.ModelSerializer):
    name_translations = TranslationField("name")
    description_translations = TranslationField("description")
    
    class Meta:
        model = Channel
        fields = [
            "id",
            "slug",
            "name",
            "name_translations",
            "description",
            "description_translations",
            "kind",
            "posting_policy",
            "is_private",
            "is_active",
            "allow_alerts",
            "broadcast_scope",
            "allow_join_requests",
            "default_alerts_enabled",
            "default_posts_enabled",
            "teaser_character_limit",
            "created_at",
            "updated_at",
            "is_member",
            "membership_role",
        ]
    
    is_member = serializers.SerializerMethodField()
    membership_role = serializers.SerializerMethodField()

    def get_is_member(self, obj: Channel) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return ChannelMembership.objects.filter(
            channel=obj, user=request.user, is_active=True
        ).exists()

    def get_membership_role(self, obj: Channel) -> str | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = (
            ChannelMembership.objects.filter(channel=obj, user=request.user, is_active=True)
            .values_list("role", flat=True)
            .first()
        )
        return membership


class ChannelMembershipSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = ChannelMembership
        fields = ["id", "channel", "role", "is_active", "notifications", "created_at", "updated_at"]
        read_only_fields = fields


class ChannelInviteSerializer(serializers.ModelSerializer):
    channel = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.all())

    class Meta:
        model = ChannelInvite
        fields = [
            "id",
            "channel",
            "email",
            "phone_number",
            "token",
            "expires_at",
            "accepted_at",
            "created_at",
        ]
        read_only_fields = ("token", "expires_at", "accepted_at", "created_at")


class ChannelJoinRequestSerializer(serializers.ModelSerializer):
    channel = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.all())
    requester_display = serializers.SerializerMethodField()

    class Meta:
        model = ChannelJoinRequest
        fields = [
            "id",
            "channel",
            "requester",
            "requester_display",
            "message",
            "status",
            "created_at",
            "reviewed_at",
            "reviewed_by",
        ]
        read_only_fields = ("requester", "requester_display", "status", "reviewed_at", "reviewed_by")

    def get_requester_display(self, obj: ChannelJoinRequest) -> str:
        return obj.requester.get_full_name() or obj.requester.get_username()


class ThreadSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    channel_id = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all(), source="channel", write_only=True
    )

    class Meta:
        model = Thread
        fields = [
            "id",
            "channel",
            "channel_id",
            "author",
            "title",
            "summary",
            "is_pinned",
            "pinned_until",
            "is_locked",
            "last_post_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("author", "last_post_at", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["author"] = request.user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    thread_id = serializers.PrimaryKeyRelatedField(
        queryset=Thread.objects.all(), source="thread", write_only=True
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "thread",
            "thread_id",
            "channel",
            "author",
            "kind",
            "body",
            "metadata",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("thread", "channel", "author", "is_deleted", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context["request"]
        thread = validated_data["thread"]
        validated_data["channel"] = thread.channel
        validated_data["author"] = request.user
        post = super().create(validated_data)
        Thread.objects.filter(pk=thread.pk).update(last_post_at=post.created_at)
        return post


class AlertSerializer(PostSerializer):
    """Serializer for alert posts with teaser metadata."""

    teaser = serializers.SerializerMethodField()

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ["teaser"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs["kind"] = Post.Kind.ALERT
        return attrs

    def create(self, validated_data):
        validated_data["kind"] = Post.Kind.ALERT
        return super().create(validated_data)

    def get_teaser(self, obj: Post) -> str:
        limit = obj.channel.teaser_character_limit
        return obj.body[:limit]


class EventMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMeta
        fields = [
            "id",
            "thread",
            "starts_at",
            "ends_at",
            "location",
            "allow_rsvp",
            "capacity",
            "external_link",
            "created_at",
            "updated_at",
        ]


class EventRSVPSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRSVP
        fields = [
            "id",
            "event",
            "user",
            "status",
            "guests",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("user",)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "id",
            "user",
            "kind",
            "token",
            "is_active",
            "last_success_at",
            "last_failure_at",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("user", "last_success_at", "last_failure_at", "failure_reason")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "channel",
            "thread",
            "post",
            "canned_reason",
            "reason",
            "created_at",
            "resolved_at",
            "resolved_by",
            "resolution_notes",
        ]
        read_only_fields = ("reporter", "resolved_at", "resolved_by", "resolution_notes")

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    actor_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_display",
            "channel",
            "thread",
            "post",
            "action",
            "context",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_display(self, obj: AuditLog) -> str | None:
        if obj.actor:
            return obj.actor.get_full_name() or obj.actor.get_username()
        return None
