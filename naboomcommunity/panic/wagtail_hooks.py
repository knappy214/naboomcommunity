from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.decorators import permission_required
from django.urls import path, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets import ViewSetGroup
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

# Import models if they exist
try:
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
        PatrolRouteWaypoint,
        PatrolShift,
        PatrolWaypoint,
        PushDevice,
        Responder,
        Vehicle,
        VehiclePosition,
    )
    MODELS_AVAILABLE = True
except ImportError:
    # Models don't exist yet, skip wagtail hooks
    MODELS_AVAILABLE = False


# Ensure custom submenu registration is imported (mirrors Community Hub pattern)
from . import admin_menu  # noqa: F401

# PanicDashboardView removed - now using ViewSetGroup with sub-items

if MODELS_AVAILABLE:

    class PatrolCoverageReportView(TemplateView):
        template_name = "panic/admin/patrol_coverage_report.html"

        @method_decorator(permission_required("panic.view_patrolalert"))
        def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
            return super().dispatch(request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            days = self._days()
            since = timezone.now() - timedelta(days=days)
            shifts = (
                PatrolShift.objects.filter(started_at__gte=since)
                .select_related("vehicle", "route")
                .prefetch_related("alerts", "route__waypoints")
                .order_by("-started_at")
            )

            results = []
            for shift in shifts:
                waypoints = shift.route.waypoints.filter(is_active=True) if shift.route else []
                waypoint_count = waypoints.count() if hasattr(waypoints, "count") else len(waypoints)
                visited = (
                    shift.alerts.filter(kind=PatrolAlert.Kind.CHECK_IN)
                    .values_list("waypoint_id", flat=True)
                    .distinct()
                )
                visited_count = visited.count()
                coverage = 0.0
                if waypoint_count:
                    coverage = min(visited_count / waypoint_count, 1) * 100
                gap_count = max(waypoint_count - visited_count, 0)
                results.append(
                    {
                        "shift": shift,
                        "vehicle": shift.vehicle,
                        "route": shift.route,
                        "coverage": round(coverage, 2),
                        "waypoint_total": waypoint_count,
                        "visited": visited_count,
                        "gaps": gap_count,
                    }
                )

            context.update({"results": results, "days": days})
            return context

        def _days(self) -> int:
            try:
                return max(1, int(self.request.GET.get("days", 7)))
            except (TypeError, ValueError):
                return 7


    # ======================================================================
    # Enhanced Wagtail Admin Menu Integration for Panic Models
    # ======================================================================

    def get_wagtail_snippet_urls():
        """Generate Wagtail snippet admin URLs for all Panic models"""
        
        # All models are now managed as Wagtail snippets
        # The correct namespace pattern is wagtailsnippets:app_label.model_name:action
        return {
            'incident': [
                ('wagtailsnippets:panic.incident:list', _('Incidents')),
                ('wagtailsnippets:panic.patrolalert:list', _('Patrol Alerts')),
                ('wagtailsnippets:panic.inboundmessage:list', _('Inbound Messages')),
                ('wagtailsnippets:panic.outboundmessage:list', _('Outbound Messages')),
            ],
            'client': [
                ('wagtailsnippets:panic.clientprofile:list', _('Client Profiles')),
                ('wagtailsnippets:panic.emergencycontact:list', _('Emergency Contacts')),
                ('wagtailsnippets:panic.responder:list', _('Responders')),
                ('wagtailsnippets:panic.pushdevice:list', _('Push Devices')),
            ],
            'patrol': [
                ('wagtailsnippets:panic.vehicle:list', _('Vehicles')),
                ('wagtailsnippets:panic.patrolwaypoint:list', _('Patrol Waypoints')),
                ('wagtailsnippets:panic.patrolroute:list', _('Patrol Routes')),
                ('wagtailsnippets:panic.patrolshift:list', _('Patrol Shifts')),
            ],
            'system': [
                ('wagtailsnippets:panic.escalationrule:list', _('Escalation Rules')),
                ('wagtailsnippets:panic.escalationtarget:list', _('Escalation Targets')),
            ],
        }


    @hooks.register("register_admin_urls")
    def register_panic_admin_urls():
        return [
            path(
                "panic/reports/patrol-coverage/",
                PatrolCoverageReportView.as_view(),
                name="wagtailadmin_panic_patrol_coverage_report",
            ),
        ]


    # Panic Dashboard menu item removed - now using ViewSetGroup with sub-items


    # Old individual menu items removed - now using ViewSetGroup


    @hooks.register("register_reports_menu_item")
    def register_panic_report_menu_item():
        return MenuItem(
            label=_("Patrol coverage"),
            url=reverse("wagtailadmin_panic_patrol_coverage_report"),
            icon_name="success",
            order=100,
        )


    # ========================================
    # Panic Model ViewSets (Following Community Pattern)
    # ========================================

    class IncidentViewSet(ModelViewSet):
        model = Incident
        menu_label = _("Incidents")
        icon = "warning"
        list_display = ("reference", "status", "priority", "client", "province", "source", "created_at")
        list_filter = ("status", "priority", "province", "source", "created_at")
        search_fields = ("reference", "description", "client__full_name", "address")
        ordering = ("-created_at",)
        form_fields = [
            "reference", "status", "priority", "client", "description", "source",
            "address", "province", "location", "context", "acknowledged_at", "resolved_at"
        ]
        
        panels = [
            MultiFieldPanel([
                FieldPanel("reference"),
                FieldPanel("status"),
                FieldPanel("priority"),
            ], heading=_("Incident Details")),
            MultiFieldPanel([
                FieldPanel("client"),
                FieldPanel("description"),
                FieldPanel("source"),
            ], heading=_("Source Information")),
            MultiFieldPanel([
                FieldPanel("address"),
                FieldPanel("province"),
                FieldPanel("location"),
            ], heading=_("Location")),
            MultiFieldPanel([
                FieldPanel("context"),
                FieldPanel("acknowledged_at"),
                FieldPanel("resolved_at"),
            ], heading=_("Status & Context")),
        ]


    class ClientProfileViewSet(ModelViewSet):
        model = ClientProfile
        menu_label = _("Client Profiles")
        icon = "user"
        list_display = ("full_name", "phone_number", "email", "province", "is_active", "created_at")
        list_filter = ("province", "is_active", "created_at")
        search_fields = ("full_name", "phone_number", "email", "address")
        ordering = ("-created_at",)
        form_fields = [
            "full_name", "phone_number", "email", "address", "province", 
            "location", "is_active"
        ]
        
        panels = [
            MultiFieldPanel([
                FieldPanel("full_name"),
                FieldPanel("phone_number"),
                FieldPanel("email"),
            ], heading=_("Contact Information")),
            MultiFieldPanel([
                FieldPanel("address"),
                FieldPanel("province"),
                FieldPanel("location"),
            ], heading=_("Location & Identity")),
            FieldPanel("is_active"),
        ]


    class ResponderViewSet(ModelViewSet):
        model = Responder
        menu_label = _("Responders")
        icon = "group"
        list_display = ("full_name", "phone_number", "responder_type", "province", "is_active")
        list_filter = ("responder_type", "province", "is_active")
        search_fields = ("full_name", "phone_number", "email")
        ordering = ("full_name",)
        form_fields = [
            "full_name", "phone_number", "email", "responder_type", "province", "is_active"
        ]
        
        panels = [
            MultiFieldPanel([
                FieldPanel("full_name"),
                FieldPanel("phone_number"),
                FieldPanel("email"),
            ], heading=_("Contact Information")),
            MultiFieldPanel([
                FieldPanel("responder_type"),
                FieldPanel("province"),
            ], heading=_("Role & Location")),
            FieldPanel("is_active"),
        ]


    class VehicleViewSet(ModelViewSet):
        model = Vehicle
        menu_label = _("Vehicles")
        icon = "pick"
        list_display = ("name", "is_active", "last_seen_at", "speed_kph")
        list_filter = ("is_active", "last_seen_at")
        search_fields = ("name", "token")
        ordering = ("name",)
        form_fields = ["name", "token", "is_active", "last_seen_at", "last_position", "speed_kph", "heading_deg"]
        
        panels = [
            MultiFieldPanel([
                FieldPanel("name"),
                FieldPanel("token"),
            ], heading=_("Vehicle Information")),
            MultiFieldPanel([
                FieldPanel("is_active"),
                FieldPanel("last_seen_at"),
            ], heading=_("Status")),
            MultiFieldPanel([
                FieldPanel("last_position"),
                FieldPanel("speed_kph"),
                FieldPanel("heading_deg"),
            ], heading=_("Location & Movement")),
        ]


    class PatrolWaypointViewSet(ModelViewSet):
        model = PatrolWaypoint
        menu_label = _("Patrol Waypoints")
        icon = "radio-full"
        list_display = ("name", "province", "radius_m", "is_active")
        list_filter = ("province", "is_active")
        search_fields = ("name",)
        ordering = ("name",)
        form_fields = ["name", "province", "point", "radius_m", "is_active"]
        
        panels = [
            MultiFieldPanel([
                FieldPanel("name"),
                FieldPanel("province"),
            ], heading=_("Waypoint Information")),
            MultiFieldPanel([
                FieldPanel("point"),
                FieldPanel("radius_m"),
            ], heading=_("Location Settings")),
            FieldPanel("is_active"),
        ]


    class EscalationRuleViewSet(ModelViewSet):
        model = EscalationRule
        menu_label = _("Escalation Rules")
        icon = "cogs"
        list_display = ("name", "province", "delay_seconds", "active")
        list_filter = ("province", "active")
        search_fields = ("name",)
        ordering = ("name",)
        form_fields = ["name", "province", "delay_seconds", "active"]
        
        panels = [
            MultiFieldPanel([
                FieldPanel("name"),
                FieldPanel("province"),
            ], heading=_("Rule Configuration")),
            MultiFieldPanel([
                FieldPanel("delay_seconds"),
                FieldPanel("active"),
            ], heading=_("Timing & Status")),
        ]


    class PanicGroup(ViewSetGroup):
        menu_label = _("Panic")
        menu_icon = "warning"
        menu_order = 201
        items = (
            IncidentViewSet,
            ClientProfileViewSet,
            ResponderViewSet,
            VehicleViewSet,
            PatrolWaypointViewSet,
            EscalationRuleViewSet,
        )


    @hooks.register("register_admin_viewset")
    def register_panic_group():
        return PanicGroup()
