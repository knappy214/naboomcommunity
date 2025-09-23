from __future__ import annotations

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import (
    ClientProfile,
    EmergencyContact,
    EscalationRule,
    EscalationTarget,
    Incident,
    IncidentEvent,
    InboundMessage,
    OutboundMessage,
    PatrolAlert,
    PatrolRoute,
    PatrolShift,
    PatrolWaypoint,
    PushDevice,
    Responder,
    Vehicle,
    VehiclePosition,
)


# ========================================
# Client & Contact Management Snippets
# ========================================

class ClientProfileViewSet(SnippetViewSet):
    model = ClientProfile
    menu_label = "Client Profiles"
    icon = "user"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ["full_name", "phone_number", "email", "province", "is_active", "created_at"]
    list_filter = ["province", "is_active", "created_at"]
    search_fields = ["full_name", "phone_number", "email", "address"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("full_name"),
            FieldPanel("phone_number"),
            FieldPanel("email"),
        ], heading="Contact Information"),
        MultiFieldPanel([
            FieldPanel("address"),
            FieldPanel("province"),
            FieldPanel("location"),
        ], heading="Location & Identity"),
        FieldPanel("is_active"),
    ]


class ResponderViewSet(SnippetViewSet):
    model = Responder
    menu_label = "Responders"
    icon = "group"
    menu_order = 101
    add_to_settings_menu = False
    list_display = ["full_name", "phone_number", "responder_type", "province", "is_active"]
    list_filter = ["responder_type", "province", "is_active"]
    search_fields = ["full_name", "phone_number", "email"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("full_name"),
            FieldPanel("phone_number"),
            FieldPanel("email"),
        ], heading="Contact Information"),
        MultiFieldPanel([
            FieldPanel("responder_type"),
            FieldPanel("province"),
        ], heading="Role & Location"),
        FieldPanel("is_active"),
    ]


class EmergencyContactViewSet(SnippetViewSet):
    model = EmergencyContact
    menu_label = "Emergency Contacts"
    icon = "phone"
    menu_order = 102
    add_to_settings_menu = False
    list_display = ["full_name", "phone_number", "client", "relationship", "priority", "is_active"]
    list_filter = ["relationship", "priority", "is_active"]
    search_fields = ["full_name", "phone_number", "client__full_name"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("client"),
            FieldPanel("full_name"),
            FieldPanel("phone_number"),
        ], heading="Contact Details"),
        MultiFieldPanel([
            FieldPanel("relationship"),
            FieldPanel("priority"),
            FieldPanel("is_active"),
        ], heading="Contact Settings"),
    ]


# ========================================
# Vehicle & Patrol Management Snippets
# ========================================

class VehicleViewSet(SnippetViewSet):
    model = Vehicle
    menu_label = "Vehicles"
    icon = "pick"
    menu_order = 200
    add_to_settings_menu = False
    list_display = ["name", "is_active", "last_seen_at", "created_at"]
    list_filter = ["is_active", "last_seen_at"]
    search_fields = ["name", "token"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("token"),
        ], heading="Vehicle Information"),
        MultiFieldPanel([
            FieldPanel("is_active"),
            FieldPanel("last_seen_at"),
        ], heading="Status"),
    ]


class PatrolWaypointViewSet(SnippetViewSet):
    model = PatrolWaypoint
    menu_label = "Patrol Waypoints"
    icon = "radio-full"
    menu_order = 201
    add_to_settings_menu = False
    list_display = ["name", "province", "radius_m", "is_active"]
    list_filter = ["province", "is_active"]
    search_fields = ["name"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("province"),
        ], heading="Waypoint Information"),
        MultiFieldPanel([
            FieldPanel("point"),
            FieldPanel("radius_m"),
        ], heading="Location Settings"),
        FieldPanel("is_active"),
    ]


class PatrolRouteViewSet(SnippetViewSet):
    model = PatrolRoute
    menu_label = "Patrol Routes"
    icon = "redirect"
    menu_order = 202
    add_to_settings_menu = False
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    
    panels = [
        FieldPanel("name"),
        FieldPanel("waypoints"),
        FieldPanel("is_active"),
    ]


class PatrolShiftViewSet(SnippetViewSet):
    model = PatrolShift
    menu_label = "Patrol Shifts"
    icon = "date"
    menu_order = 203
    add_to_settings_menu = False
    list_display = ["name", "vehicle", "route", "started_at", "ended_at", "is_active"]
    list_filter = ["vehicle", "route", "is_active", "started_at"]
    search_fields = ["name", "vehicle__name", "route__name"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("vehicle"),
            FieldPanel("route"),
        ], heading="Shift Configuration"),
        MultiFieldPanel([
            FieldPanel("started_at"),
            FieldPanel("ended_at"),
        ], heading="Schedule"),
        FieldPanel("is_active"),
    ]


class VehiclePositionViewSet(SnippetViewSet):
    model = VehiclePosition
    menu_label = "Vehicle Positions"
    icon = "location"
    menu_order = 204
    add_to_settings_menu = False
    list_display = ["vehicle", "recorded_at", "speed_kph", "heading_deg"]
    list_filter = ["vehicle", "recorded_at"]
    search_fields = ["vehicle__name"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("vehicle"),
            FieldPanel("position"),
        ], heading="Location Information"),
        MultiFieldPanel([
            FieldPanel("speed_kph"),
            FieldPanel("heading_deg"),
            FieldPanel("recorded_at"),
        ], heading="Movement Data"),
    ]


# ========================================
# Incident Management Snippets
# ========================================

class IncidentViewSet(SnippetViewSet):
    model = Incident
    menu_label = "Incidents"
    icon = "warning"
    menu_order = 300
    add_to_settings_menu = False
    list_display = ["reference", "status", "priority", "client", "province", "source", "created_at"]
    list_filter = ["status", "priority", "province", "source", "created_at"]
    search_fields = ["reference", "description", "client__full_name", "address"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("reference"),
            FieldPanel("status"),
            FieldPanel("priority"),
        ], heading="Incident Details"),
        MultiFieldPanel([
            FieldPanel("client"),
            FieldPanel("description"),
            FieldPanel("source"),
        ], heading="Source Information"),
        MultiFieldPanel([
            FieldPanel("address"),
            FieldPanel("province"),
            FieldPanel("location"),
        ], heading="Location"),
        MultiFieldPanel([
            FieldPanel("context"),
            FieldPanel("acknowledged_at"),
            FieldPanel("resolved_at"),
        ], heading="Status & Context"),
    ]


class IncidentEventViewSet(SnippetViewSet):
    model = IncidentEvent
    menu_label = "Incident Events"
    icon = "list-ul"
    menu_order = 300
    add_to_settings_menu = False
    list_display = ["incident", "kind", "created_at"]
    list_filter = ["kind", "created_at"]
    search_fields = ["incident__reference", "description"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("incident"),
            FieldPanel("kind"),
        ], heading="Event Details"),
        MultiFieldPanel([
            FieldPanel("description"),
            FieldPanel("metadata"),
        ], heading="Event Information"),
    ]


class PatrolAlertViewSet(SnippetViewSet):
    model = PatrolAlert
    menu_label = "Patrol Alerts"
    icon = "warning"
    menu_order = 301
    add_to_settings_menu = False
    list_display = ["shift", "kind", "waypoint", "created_at", "acknowledged_at"]
    list_filter = ["kind", "shift__vehicle", "acknowledged_at", "created_at"]
    search_fields = ["shift__name", "waypoint__name", "details"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("shift"),
            FieldPanel("kind"),
            FieldPanel("waypoint"),
        ], heading="Alert Details"),
        MultiFieldPanel([
            FieldPanel("details"),
            FieldPanel("acknowledged_at"),
        ], heading="Alert Information"),
    ]


# ========================================
# System Configuration Snippets  
# ========================================

class EscalationRuleViewSet(SnippetViewSet):
    model = EscalationRule
    menu_label = "Escalation Rules"
    icon = "cogs"
    menu_order = 400
    add_to_settings_menu = False
    list_display = ["name", "province", "delay_seconds", "active"]
    list_filter = ["province", "active"]
    search_fields = ["name"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("province"),
        ], heading="Rule Configuration"),
        MultiFieldPanel([
            FieldPanel("delay_seconds"),
            FieldPanel("active"),
        ], heading="Timing & Status"),
    ]


class EscalationTargetViewSet(SnippetViewSet):
    model = EscalationTarget
    menu_label = "Escalation Targets"
    icon = "crosshairs"
    menu_order = 401
    add_to_settings_menu = False
    list_display = ["rule", "target_type", "channel", "active"]
    list_filter = ["target_type", "channel", "active"]
    search_fields = ["destination", "responder__full_name", "contact__full_name"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("rule"),
            FieldPanel("target_type"),
            FieldPanel("channel"),
        ], heading="Target Configuration"),
        MultiFieldPanel([
            FieldPanel("destination"),
            FieldPanel("responder"),
            FieldPanel("contact"),
        ], heading="Destination Settings"),
        FieldPanel("active"),
    ]


# ========================================
# Message Management Snippets
# ========================================

class InboundMessageViewSet(SnippetViewSet):
    model = InboundMessage
    menu_label = "Inbound Messages"
    icon = "mail"
    menu_order = 500
    add_to_settings_menu = False
    list_display = ["provider", "incident", "from_number", "received_at"]
    list_filter = ["provider", "received_at"]
    search_fields = ["from_number", "to_number", "body"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("provider"),
            FieldPanel("incident"),
            FieldPanel("from_number"),
            FieldPanel("to_number"),
        ], heading="Message Details"),
        FieldPanel("body"),
        MultiFieldPanel([
            FieldPanel("message_id"),
            FieldPanel("metadata"),
        ], heading="Tracking Information"),
    ]


class OutboundMessageViewSet(SnippetViewSet):
    model = OutboundMessage
    menu_label = "Outbound Messages"
    icon = "mail"
    menu_order = 501
    add_to_settings_menu = False
    list_display = ["provider", "incident", "to_number", "status", "sent_at"]
    list_filter = ["provider", "status", "sent_at"]
    search_fields = ["to_number", "body"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("provider"),
            FieldPanel("incident"),
            FieldPanel("to_number"),
            FieldPanel("status"),
        ], heading="Message Details"),
        FieldPanel("body"),
        MultiFieldPanel([
            FieldPanel("message_id"),
            FieldPanel("metadata"),
        ], heading="Tracking Information"),
    ]


class PushDeviceViewSet(SnippetViewSet):
    model = PushDevice
    menu_label = "Push Devices"
    icon = "mobile-alt"
    menu_order = 502
    add_to_settings_menu = False
    list_display = ["client", "platform", "app_version", "last_seen_at"]
    list_filter = ["platform", "last_seen_at"]
    search_fields = ["client__full_name", "token"]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("user"),
            FieldPanel("client"),
            FieldPanel("token"),
        ], heading="Device Information"),
        MultiFieldPanel([
            FieldPanel("platform"),
            FieldPanel("app_version"),
        ], heading="Device Details"),
    ]


# ========================================
# Register all ViewSets
# ========================================

# Register all ViewSets as snippets
register_snippet(ClientProfile, viewset=ClientProfileViewSet)
register_snippet(Responder, viewset=ResponderViewSet)
register_snippet(EmergencyContact, viewset=EmergencyContactViewSet)
register_snippet(Vehicle, viewset=VehicleViewSet)
register_snippet(VehiclePosition, viewset=VehiclePositionViewSet)
register_snippet(PatrolWaypoint, viewset=PatrolWaypointViewSet)
register_snippet(PatrolRoute, viewset=PatrolRouteViewSet)
register_snippet(PatrolShift, viewset=PatrolShiftViewSet)
register_snippet(Incident, viewset=IncidentViewSet)
register_snippet(IncidentEvent, viewset=IncidentEventViewSet)
register_snippet(PatrolAlert, viewset=PatrolAlertViewSet)
register_snippet(EscalationRule, viewset=EscalationRuleViewSet)
register_snippet(EscalationTarget, viewset=EscalationTargetViewSet)
register_snippet(InboundMessage, viewset=InboundMessageViewSet)
register_snippet(OutboundMessage, viewset=OutboundMessageViewSet)
register_snippet(PushDevice, viewset=PushDeviceViewSet)
