"""Django signals for the community hub."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Channel, ChannelConfiguration, ChannelModerationPolicy, ChannelAlertPolicy


@receiver(post_save, sender=Channel)
def create_channel_configuration(sender, instance, created, **kwargs):
    """Automatically create a ChannelConfiguration when a Channel is created."""
    if created:
        # Get default policies (create them if they don't exist)
        default_moderation_policy, _ = ChannelModerationPolicy.objects.get_or_create(
            name="Default Moderation Policy",
            defaults={
                "description": "Default moderation policy for new channels",
                "auto_approve_join_requests": False,
                "require_alert_approval": True,
                "require_post_approval": False,
                "escalation_minutes": 30,
            }
        )
        
        default_alert_policy, _ = ChannelAlertPolicy.objects.get_or_create(
            name="Default Alert Policy",
            defaults={
                "description": "Default alert policy for new channels",
                "cooldown_minutes": 30,
                "duplicate_window_minutes": 15,
                "duplicate_threshold": 0.7,
            }
        )
        
        # Create the configuration
        ChannelConfiguration.objects.create(
            channel=instance,
            moderation_policy=default_moderation_policy,
            alert_policy=default_alert_policy,
        )
