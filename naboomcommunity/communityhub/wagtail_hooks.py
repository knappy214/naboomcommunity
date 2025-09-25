"""Wagtail admin integration for the community hub."""
from django.utils.translation import gettext_lazy as _
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import (
    CannedReportReason,
    Channel,
    ChannelAlertPolicy,
    ChannelConfiguration,
    ChannelInvite,
    ChannelJoinRequest,
    ChannelModerationPolicy,
)


class TranslatableSnippetViewSet(SnippetViewSet):
    """Base snippet viewset that enables locale switching."""

    list_per_page = 50
    inspect_view_enabled = True
    add_to_admin_menu = True


class ChannelViewSet(TranslatableSnippetViewSet):
    model = Channel
    icon = "site"
    menu_label = _("Channels")
    menu_order = 200
    list_display = ("name", "slug", "kind", "is_private", "is_active")
    list_filter = ("kind", "is_private", "is_active")
    search_fields = ("name", "description")


class ChannelModerationPolicyViewSet(TranslatableSnippetViewSet):
    model = ChannelModerationPolicy
    icon = "warning"
    menu_label = _("Moderation policies")
    menu_order = 210
    list_display = ("name", "auto_approve_join_requests", "require_post_approval")
    search_fields = ("name", "description")


class ChannelAlertPolicyViewSet(TranslatableSnippetViewSet):
    model = ChannelAlertPolicy
    icon = "warning-inverse"
    menu_label = _("Alert policies")
    menu_order = 220
    list_display = ("name", "cooldown_minutes", "duplicate_window_minutes")
    search_fields = ("name", "description")


class ChannelInviteViewSet(TranslatableSnippetViewSet):
    model = ChannelInvite
    icon = "mail"
    menu_label = _("Invites")
    menu_order = 230
    list_display = ("channel", "email", "phone_number", "expires_at", "accepted_at")
    list_filter = ("channel",)
    search_fields = ("email", "phone_number", "channel__name")


class ChannelJoinRequestViewSet(TranslatableSnippetViewSet):
    model = ChannelJoinRequest
    icon = "user"
    menu_label = _("Join requests")
    menu_order = 240
    list_display = ("channel", "requester", "status", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("requester__username", "requester__email")


class CannedReasonViewSet(TranslatableSnippetViewSet):
    model = CannedReportReason
    icon = "help"
    menu_label = _("Canned reasons")
    menu_order = 250
    list_display = ("title", "created_at")
    search_fields = ("title", "description")


class ChannelConfigurationViewSet(SnippetViewSet):
    """Configuration viewset uses generic snippet behaviour without translation."""

    model = ChannelConfiguration
    icon = "cog"
    menu_label = _("Channel configs")
    menu_order = 260
    list_display = ("channel", "moderation_policy", "alert_policy")
    list_filter = ("moderation_policy", "alert_policy")


register_snippet(ChannelViewSet)
register_snippet(ChannelModerationPolicyViewSet)
register_snippet(ChannelAlertPolicyViewSet)
register_snippet(ChannelInviteViewSet)
register_snippet(ChannelJoinRequestViewSet)
register_snippet(CannedReasonViewSet)
register_snippet(ChannelConfigurationViewSet)
