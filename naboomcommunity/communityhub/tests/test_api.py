from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from wagtail.models import Locale

from communityhub.models import Channel, ChannelMembership

User = get_user_model()


class CommunityHubAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="resident", password="secret")
        self.locale = Locale.objects.get_or_create(language_code="en")[0]
        self.channel = Channel.objects.create(slug="general", name="General", locale=self.locale)
        ChannelMembership.objects.create(user=self.user, channel=self.channel)
        self.client.force_authenticate(self.user)

    def test_list_channels(self):
        response = self.client.get(reverse("community-channel-list"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["slug"], "general")

    def test_create_thread(self):
        response = self.client.post(
            reverse("community-thread-list"),
            {"channel_id": self.channel.pk, "title": "Welcome", "summary": "Intro"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        thread_id = response.json()["id"]
        post_response = self.client.post(
            reverse("community-post-list"),
            {"thread_id": thread_id, "body": "Hello", "kind": "text"},
            format="json",
        )
        self.assertEqual(post_response.status_code, 201)
