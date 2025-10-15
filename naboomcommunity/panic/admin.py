from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from . import models

# Register existing models if they exist
try:
    @admin.register(models.ClientProfile)
    class ClientProfileAdmin(admin.ModelAdmin):
        list_display = ("full_name", "phone_number", "province", "created_at")
        search_fields = ("full_name", "phone_number", "email")
        list_filter = ("province", "is_active")
except AttributeError:
    pass  # Model doesn't exist yet


# Register existing models if they exist
try:
    @admin.register(models.EmergencyContact)
    class EmergencyContactAdmin(admin.ModelAdmin):
        list_display = ("full_name", "phone_number", "client", "priority", "is_active")
        search_fields = ("full_name", "phone_number")
        list_filter = ("is_active",)
except AttributeError:
    pass

try:
    @admin.register(models.Responder)
    class ResponderAdmin(admin.ModelAdmin):
        list_display = ("full_name", "phone_number", "province", "responder_type", "is_active")
        search_fields = ("full_name", "phone_number", "email")
        list_filter = ("province", "responder_type", "is_active")
except AttributeError:
    pass

try:
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
except AttributeError:
    pass

try:
    @admin.register(models.IncidentEvent)
    class IncidentEventAdmin(admin.ModelAdmin):
        list_display = ("incident", "kind", "created_at")
        search_fields = ("incident__reference", "description")
        list_filter = ("kind",)
        date_hierarchy = "created_at"
except AttributeError:
    pass

try:
    @admin.register(models.Vehicle)
    class VehicleAdmin(admin.ModelAdmin):
        list_display = ("name", "token", "is_active", "last_seen_at")
        search_fields = ("name", "token")
        list_filter = ("is_active",)
except AttributeError:
    pass

try:
    @admin.register(models.VehiclePosition)
    class VehiclePositionAdmin(admin.ModelAdmin):
        list_display = ("vehicle", "recorded_at", "speed_kph", "heading_deg")
        search_fields = ("vehicle__name",)
        list_filter = ("vehicle",)
        date_hierarchy = "recorded_at"
except AttributeError:
    pass

try:
    @admin.register(models.PatrolWaypoint)
    class PatrolWaypointAdmin(admin.ModelAdmin):
        list_display = ("name", "province", "radius_m", "is_active")
        search_fields = ("name",)
        list_filter = ("province", "is_active")
except AttributeError:
    pass

try:
    @admin.register(models.PatrolRoute)
    class PatrolRouteAdmin(admin.ModelAdmin):
        list_display = ("name", "is_active")
        search_fields = ("name",)
        list_filter = ("is_active",)
except AttributeError:
    pass

try:
    @admin.register(models.PatrolShift)
    class PatrolShiftAdmin(admin.ModelAdmin):
        list_display = ("name", "vehicle", "route", "started_at", "ended_at", "is_active")
        search_fields = ("name", "vehicle__name")
        list_filter = ("is_active",)
        date_hierarchy = "started_at"
except AttributeError:
    pass

try:
    @admin.register(models.PatrolAlert)
    class PatrolAlertAdmin(admin.ModelAdmin):
        list_display = ("shift", "kind", "waypoint", "created_at", "acknowledged_at")
        search_fields = ("shift__name", "details")
        list_filter = ("kind", "shift__vehicle")
except AttributeError:
    pass

try:
    @admin.register(models.PushDevice)
    class PushDeviceAdmin(admin.ModelAdmin):
        list_display = ("token", "platform", "last_seen_at")
        search_fields = ("token",)
        list_filter = ("platform",)
except AttributeError:
    pass

try:
    @admin.register(models.EscalationRule)
    class EscalationRuleAdmin(admin.ModelAdmin):
        list_display = ("name", "province", "delay_seconds", "active")
        list_filter = ("province", "active")
        search_fields = ("name",)
except AttributeError:
    pass

try:
    @admin.register(models.EscalationTarget)
    class EscalationTargetAdmin(admin.ModelAdmin):
        @admin.display(description="Destination")
        def destination_display(self, obj: models.EscalationTarget) -> str:
            return obj.resolve_destination() or "–"

        list_display = ("rule", "target_type", "channel", "destination_display", "active")
        list_filter = ("target_type", "channel", "active")
        search_fields = ("destination", "responder__full_name", "contact__full_name")
except AttributeError:
    pass

# Register new emergency response models
@admin.register(models.EmergencyLocation)
class EmergencyLocationAdmin(GISModelAdmin):
    list_display = ("user", "emergency_type", "accuracy_level", "is_active", "created_at")
    search_fields = ("user__username", "description", "device_id")
    list_filter = ("emergency_type", "accuracy_level", "is_active", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)


@admin.register(models.EmergencyZone)
class EmergencyZoneAdmin(GISModelAdmin):
    list_display = ("name", "zone_type", "priority", "is_active", "created_at")
    search_fields = ("name", "description", "contact_phone", "contact_email")
    list_filter = ("zone_type", "is_active", "priority")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.EmergencyMedical)
class EmergencyMedicalAdmin(admin.ModelAdmin):
    list_display = ("user", "consent_level", "is_encrypted", "last_verified_at", "created_at")
    search_fields = ("user__username", "emergency_contact_name", "emergency_contact_phone")
    list_filter = ("consent_level", "is_encrypted", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "consent_given_at")
    raw_id_fields = ("user",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user",)
        }),
        ("Medical Information", {
            "fields": ("blood_type", "allergies", "medications", "medical_conditions")
        }),
        ("Emergency Contact", {
            "fields": ("emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship")
        }),
        ("Consent & Privacy", {
            "fields": ("consent_level", "consent_given_at", "consent_expires_at", "is_encrypted", "encryption_key_id")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "last_verified_at"),
            "classes": ("collapse",)
        })
    )


@admin.register(models.MedicalCondition)
class MedicalConditionAdmin(admin.ModelAdmin):
    list_display = ("name", "severity_level", "requires_immediate_attention", "created_at")
    search_fields = ("name", "description", "icd10_code", "snomed_code")
    list_filter = ("severity_level", "requires_immediate_attention")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "generic_name", "medication_type", "created_at")
    search_fields = ("name", "generic_name", "ndc_code", "rxnorm_code")
    list_filter = ("medication_type",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ("name", "severity_level", "requires_immediate_attention", "created_at")
    search_fields = ("name", "description", "snomed_code")
    list_filter = ("severity_level", "requires_immediate_attention")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.EmergencyAuditLog)
class EmergencyAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action_type", "user", "severity", "timestamp", "ip_address")
    search_fields = ("user__username", "description", "ip_address", "session_id")
    list_filter = ("action_type", "severity", "timestamp")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp",)
    raw_id_fields = ("user", "content_type")
    
    fieldsets = (
        ("Action Details", {
            "fields": ("action_type", "severity", "description", "timestamp")
        }),
        ("User & Session", {
            "fields": ("user", "session_id", "ip_address", "user_agent")
        }),
        ("Object Information", {
            "fields": ("content_type", "object_id")
        }),
        ("Request/Response", {
            "fields": ("request_method", "request_path", "response_status")
        }),
        ("Data Changes", {
            "fields": ("old_values", "new_values"),
            "classes": ("collapse",)
        }),
        ("Additional Data", {
            "fields": ("metadata", "error_message", "stack_trace"),
            "classes": ("collapse",)
        })
    )


@admin.register(models.EmergencyAuditConfig)
class EmergencyAuditConfigAdmin(admin.ModelAdmin):
    list_display = ("audit_level", "retention_days", "archive_after_days", "is_default")
    list_filter = ("audit_level", "log_reads", "log_medical_access", "log_location_updates")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
    
    def is_default(self, obj):
        return obj.is_default
    is_default.boolean = True
    is_default.short_description = "Default Config"
