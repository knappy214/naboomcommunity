from django.contrib import admin

from . import models


@admin.register(models.ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "province", "created_at")
    search_fields = ("full_name", "phone_number", "email")
    list_filter = ("province", "is_active")


@admin.register(models.EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "client", "priority", "is_active")
    search_fields = ("full_name", "phone_number")
    list_filter = ("is_active",)


@admin.register(models.Responder)
class ResponderAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "province", "responder_type", "is_active")
    search_fields = ("full_name", "phone_number", "email")
    list_filter = ("province", "responder_type", "is_active")


@admin.register(models.Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "status",
        "priority",
        "province",
        "client",
        "created_at",
        "acknowledged_at",
        "resolved_at",
    )
    search_fields = ("reference", "description", "client__full_name")
    list_filter = ("status", "province", "priority")
    date_hierarchy = "created_at"


@admin.register(models.IncidentEvent)
class IncidentEventAdmin(admin.ModelAdmin):
    list_display = ("incident", "kind", "created_at")
    search_fields = ("incident__reference", "description")
    list_filter = ("kind",)
    date_hierarchy = "created_at"


@admin.register(models.Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("name", "token", "is_active", "last_seen_at")
    search_fields = ("name", "token")
    list_filter = ("is_active",)


@admin.register(models.VehiclePosition)
class VehiclePositionAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "recorded_at", "speed_kph", "heading_deg")
    search_fields = ("vehicle__name",)
    list_filter = ("vehicle",)
    date_hierarchy = "recorded_at"


@admin.register(models.PatrolWaypoint)
class PatrolWaypointAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "radius_m", "is_active")
    search_fields = ("name",)
    list_filter = ("province", "is_active")


@admin.register(models.PatrolRoute)
class PatrolRouteAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(models.PatrolShift)
class PatrolShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "vehicle", "route", "started_at", "ended_at", "is_active")
    search_fields = ("name", "vehicle__name")
    list_filter = ("is_active",)
    date_hierarchy = "started_at"


@admin.register(models.PatrolAlert)
class PatrolAlertAdmin(admin.ModelAdmin):
    list_display = ("shift", "kind", "waypoint", "created_at", "acknowledged_at")
    search_fields = ("shift__name", "details")
    list_filter = ("kind", "shift__vehicle")


@admin.register(models.PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = ("token", "platform", "last_seen_at")
    search_fields = ("token",)
    list_filter = ("platform",)


@admin.register(models.EscalationRule)
class EscalationRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "delay_seconds", "active")
    list_filter = ("province", "active")
    search_fields = ("name",)


@admin.register(models.EscalationTarget)
class EscalationTargetAdmin(admin.ModelAdmin):
    @admin.display(description="Destination")
    def destination_display(self, obj: models.EscalationTarget) -> str:
        return obj.resolve_destination() or "–"

    list_display = ("rule", "target_type", "channel", "destination_display", "active")
    list_filter = ("target_type", "channel", "active")
    search_fields = ("destination", "responder__full_name", "contact__full_name")
