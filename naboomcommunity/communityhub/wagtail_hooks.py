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

# Import the custom menu configuration
from . import admin_menu


class CommunityHubSnippetViewSet(SnippetViewSet):
    """Base snippet viewset for Community Hub with grouped menu."""
    
    list_per_page = 50
    inspect_view_enabled = True
    add_to_admin_menu = False  # Disable individual menu items - we'll use custom grouped menu


class TranslatableSnippetViewSet(CommunityHubSnippetViewSet):
    """Base snippet viewset that enables locale switching."""
    pass


class ChannelViewSet(TranslatableSnippetViewSet):
    model = Channel
    icon = "site"
    menu_label = _("Channels")
    menu_order = 1
    list_display = ("name", "slug", "kind", "is_private", "is_active")
    list_filter = ("kind", "is_private", "is_active")
    search_fields = ("name", "description")


class ChannelModerationPolicyViewSet(TranslatableSnippetViewSet):
    model = ChannelModerationPolicy
    icon = "warning"
    menu_label = _("Moderation policies")
    menu_order = 2
    list_display = ("name", "auto_approve_join_requests", "require_post_approval")
    search_fields = ("name", "description")


class ChannelAlertPolicyViewSet(TranslatableSnippetViewSet):
    model = ChannelAlertPolicy
    icon = "warning-inverse"
    menu_label = _("Alert policies")
    menu_order = 3
    list_display = ("name", "cooldown_minutes", "duplicate_window_minutes")
    search_fields = ("name", "description")


class ChannelInviteViewSet(TranslatableSnippetViewSet):
    model = ChannelInvite
    icon = "mail"
    menu_label = _("Invites")
    menu_order = 4
    list_display = ("channel", "email", "phone_number", "expires_at", "accepted_at")
    list_filter = ("channel",)
    search_fields = ("email", "phone_number", "channel__name")


class ChannelJoinRequestViewSet(TranslatableSnippetViewSet):
    model = ChannelJoinRequest
    icon = "user"
    menu_label = _("Join requests")
    menu_order = 5
    list_display = ("channel", "requester", "status", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("requester__username", "requester__email")


class CannedReasonViewSet(TranslatableSnippetViewSet):
    model = CannedReportReason
    icon = "help"
    menu_label = _("Canned reasons")
    menu_order = 6
    list_display = ("title", "created_at")
    search_fields = ("title", "description")


class ChannelConfigurationViewSet(CommunityHubSnippetViewSet):
    """Configuration viewset uses generic snippet behaviour without translation."""

    model = ChannelConfiguration
    icon = "cog"
    menu_label = _("Channel configs")
    menu_order = 7
    list_display = ("channel", "moderation_policy", "alert_policy")
    list_filter = ("moderation_policy", "alert_policy")
    
    def get_form_class(self, for_update=False):
        """Override form to add validation for OneToOneField constraint."""
        from django import forms
        from .models import ChannelConfiguration
        
        class ChannelConfigurationForm(forms.ModelForm):
            class Meta:
                model = ChannelConfiguration
                fields = "__all__"
            
            def clean_channel(self):
                channel = self.cleaned_data.get('channel')
                if channel and ChannelConfiguration.objects.filter(channel=channel).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(
                        f"A configuration already exists for the channel '{channel.name}'. "
                        "Each channel can only have one configuration."
                    )
                return channel
        
        return ChannelConfigurationForm


register_snippet(ChannelViewSet)
register_snippet(ChannelModerationPolicyViewSet)
register_snippet(ChannelAlertPolicyViewSet)
register_snippet(ChannelInviteViewSet)
register_snippet(ChannelJoinRequestViewSet)
register_snippet(CannedReasonViewSet)
register_snippet(ChannelConfigurationViewSet)