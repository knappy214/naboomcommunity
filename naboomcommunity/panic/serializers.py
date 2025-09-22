from __future__ import annotations

from rest_framework import serializers

from . import models


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmergencyContact
        fields = [
            "id",
            "full_name",
            "phone_number",
            "relationship",
            "priority",
            "is_active",
        ]


class ClientProfileSerializer(serializers.ModelSerializer):
    contacts = EmergencyContactSerializer(many=True, read_only=True)

    class Meta:
        model = models.ClientProfile
        fields = [
            "id",
            "external_id",
            "full_name",
            "phone_number",
            "email",
            "address",
            "province",
            "location",
            "contacts",
        ]


class IncidentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IncidentEvent
        fields = ["id", "kind", "description", "metadata", "created_at"]


class IncidentSerializer(serializers.ModelSerializer):
    client = ClientProfileSerializer(read_only=True)
    events = IncidentEventSerializer(many=True, read_only=True)

    class Meta:
        model = models.Incident
        fields = [
            "id",
            "reference",
            "status",
            "priority",
            "description",
            "source",
            "address",
            "province",
            "context",
            "acknowledged_at",
            "resolved_at",
            "created_at",
            "updated_at",
            "location",
            "client",
            "events",
        ]


class ResponderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Responder
        fields = [
            "id",
            "full_name",
            "phone_number",
            "email",
            "responder_type",
            "province",
            "is_active",
        ]


class PatrolWaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatrolWaypoint
        fields = ["id", "name", "radius_m", "province", "point", "is_active"]


class PatrolAlertSerializer(serializers.ModelSerializer):
    waypoint = PatrolWaypointSerializer(read_only=True)

    class Meta:
        model = models.PatrolAlert
        fields = [
            "id",
            "kind",
            "details",
            "created_at",
            "acknowledged_at",
            "shift_id",
            "waypoint",
        ]
