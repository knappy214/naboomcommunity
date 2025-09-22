from __future__ import annotations

import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ClientProfile, Incident, Vehicle


class SubmitIncidentViewTests(TestCase):
    def test_submit_incident_creates_new_record(self):
        client_profile = ClientProfile.objects.create(
            full_name="Jane Doe",
            phone_number="0123456789",
        )

        client = Client()
        payload = {
            "client_id": client_profile.id,
            "description": "Help needed",
            "lat": -24.5,
            "lng": 28.7,
        }
        response = client.post(
            reverse("panic_submit"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        incident = Incident.objects.get(pk=data["id"])
        self.assertEqual(incident.client, client_profile)
        self.assertEqual(incident.description, "Help needed")
        self.assertIsNotNone(incident.location)


class VehiclePingMiddlewareTests(TestCase):
    @override_settings(PANIC_VEHICLE_PING_RATE_LIMIT_PER_MINUTE=2)
    def test_vehicle_ping_rate_limited(self):
        vehicle = Vehicle.objects.create(name="Unit 1", token="secret-token")
        client = Client()
        payload = {"lat": -24.5, "lng": 28.7}

        for _ in range(2):
            response = client.post(
                reverse("panic_vehicle_ping"),
                data=json.dumps(payload),
                content_type="application/json",
                HTTP_X_VEHICLE_TOKEN="secret-token",
            )
            self.assertEqual(response.status_code, 200)

        response = client.post(
            reverse("panic_vehicle_ping"),
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_VEHICLE_TOKEN="secret-token",
        )
        self.assertEqual(response.status_code, 429)
