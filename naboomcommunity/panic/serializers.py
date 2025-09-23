from __future__ import annotations

from rest_framework import serializers

from . import models


class EmergencyContactSerializer(serializers.ModelSerializer):
    priority = serializers.SerializerMethodField()

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

    def get_priority(self, obj):
        """Return priority as string value for frontend compatibility."""
        priority_mapping = {
            1: "low",
            2: "medium", 
            3: "high",
            4: "critical"
        }
        return priority_mapping.get(obj.priority, "medium")


class ClientProfileSerializer(serializers.ModelSerializer):
    contacts = EmergencyContactSerializer(many=True, read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

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
            "latitude",
            "longitude",
            "contacts",
        ]

    def get_latitude(self, obj):
        """Extract latitude from PostGIS Point field."""
        if obj.location and hasattr(obj.location, 'y'):
            return obj.location.y
        return None

    def get_longitude(self, obj):
        """Extract longitude from PostGIS Point field."""
        if obj.location and hasattr(obj.location, 'x'):
            return obj.location.x
        return None


class IncidentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IncidentEvent
        fields = ["id", "kind", "description", "metadata", "created_at"]


class IncidentSerializer(serializers.ModelSerializer):
    client = ClientProfileSerializer(read_only=True)
    events = IncidentEventSerializer(many=True, read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

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
            "latitude",
            "longitude",
            "client",
            "events",
        ]

    def get_latitude(self, obj):
        """Extract latitude from PostGIS Point field."""
        if obj.location and hasattr(obj.location, 'y'):
            return obj.location.y
        return None

    def get_longitude(self, obj):
        """Extract longitude from PostGIS Point field."""
        if obj.location and hasattr(obj.location, 'x'):
            return obj.location.x
        return None

    def get_priority(self, obj):
        """Return priority as string value for frontend compatibility."""
        priority_mapping = {
            1: "low",
            2: "medium", 
            3: "high",
            4: "critical"
        }
        return priority_mapping.get(obj.priority, "medium")

    def get_status(self, obj):
        """Return status as string value for frontend compatibility."""
        return obj.status


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
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = models.PatrolWaypoint
        fields = ["id", "name", "radius_m", "province", "point", "latitude", "longitude", "is_active"]

    def get_latitude(self, obj):
        """Extract latitude from PostGIS Point field."""
        if obj.point and hasattr(obj.point, 'y'):
            return obj.point.y
        return None

    def get_longitude(self, obj):
        """Extract longitude from PostGIS Point field."""
        if obj.point and hasattr(obj.point, 'x'):
            return obj.point.x
        return None


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
