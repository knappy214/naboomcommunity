from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from wagtail.models import Locale

from communityhub.models import (
    Channel,
    ChannelAlertPolicy,
    ChannelConfiguration,
    ChannelInvite,
    ChannelJoinRequest,
    ChannelMembership,
    ChannelModerationPolicy,
    EventMeta,
    EventRSVP,
    Thread,
)

User = get_user_model()


class ChannelModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="moderator", password="test")
        self.locale = Locale.objects.get_or_create(language_code="en")[0]
        self.channel = Channel.objects.create(slug="general", name="General", locale=self.locale)
        self.moderation_policy = ChannelModerationPolicy.objects.create(name="Default", locale=self.locale)
        self.alert_policy = ChannelAlertPolicy.objects.create(name="Default", locale=self.locale)
        ChannelConfiguration.objects.create(
            channel=self.channel,
            moderation_policy=self.moderation_policy,
            alert_policy=self.alert_policy,
        )

    def test_membership_creation(self):
        membership = ChannelMembership.objects.create(
            user=self.user,
            channel=self.channel,
            role=ChannelMembership.Role.MODERATOR,
        )
        self.assertTrue(membership.is_active)
        self.assertEqual(str(membership), f"{self.user} @ {self.channel.slug}")

    def test_join_request_flow(self):
        requester = User.objects.create_user(username="resident", password="test")
        join_request = ChannelJoinRequest.objects.create(channel=self.channel, requester=requester)
        join_request.review(self.user, join_request.Status.APPROVED)
        membership = ChannelMembership.objects.get(channel=self.channel, user=requester)
        self.assertEqual(join_request.status, join_request.Status.APPROVED)
        self.assertEqual(membership.role, ChannelMembership.Role.MEMBER)

    def test_event_metadata(self):
        thread = Thread.objects.create(channel=self.channel, author=self.user, title="Town Hall")
        event = EventMeta.objects.create(
            thread=thread,
            starts_at=timezone.now(),
            ends_at=timezone.now(),
        )
        rsvp = EventRSVP.objects.create(event=event, user=self.user)
        self.assertEqual(str(event), f"Event for {thread}")
        self.assertEqual(str(rsvp), f"{self.user} → {event} ({rsvp.status})")

    def test_invite_accept(self):
        invite = ChannelInvite.objects.create(
            channel=self.channel,
            email="resident@example.com",
            invited_by=self.user,
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )
        invite.mark_accepted(self.user)
        self.assertIsNotNone(invite.accepted_at)
