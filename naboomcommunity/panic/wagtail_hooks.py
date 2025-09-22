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

from .models import Incident, PatrolAlert, PatrolRoute, PatrolShift, PatrolWaypoint, Vehicle


class PanicDashboardView(TemplateView):
    template_name = "panic/admin/dashboard.html"

    @method_decorator(permission_required("panic.view_incident"))
    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = [
            {
                "label": _("Incidents"),
                "count": Incident.objects.count(),
                "url": reverse("admin:panic_incident_changelist"),
            },
            {
                "label": _("Vehicles"),
                "count": Vehicle.objects.count(),
                "url": reverse("admin:panic_vehicle_changelist"),
            },
            {
                "label": _("Waypoints"),
                "count": PatrolWaypoint.objects.count(),
                "url": reverse("admin:panic_patrolwaypoint_changelist"),
            },
            {
                "label": _("Routes"),
                "count": PatrolRoute.objects.count(),
                "url": reverse("admin:panic_patrolroute_changelist"),
            },
            {
                "label": _("Shifts"),
                "count": PatrolShift.objects.count(),
                "url": reverse("admin:panic_patrolshift_changelist"),
            },
            {
                "label": _("Alerts"),
                "count": PatrolAlert.objects.count(),
                "url": reverse("admin:panic_patrolalert_changelist"),
            },
        ]
        return context


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


@hooks.register("register_admin_urls")
def register_panic_admin_urls():
    return [
        path("panic/", PanicDashboardView.as_view(), name="wagtailadmin_panic_dashboard"),
        path(
            "panic/reports/patrol-coverage/",
            PatrolCoverageReportView.as_view(),
            name="wagtailadmin_panic_patrol_coverage_report",
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_panic_menu_item():
    return MenuItem(
        label=_("Panic"),
        url=reverse("wagtailadmin_panic_dashboard"),
        icon_name="warning",
        order=201,
    )


@hooks.register("register_reports_menu_item")
def register_panic_report_menu_item():
    return MenuItem(
        label=_("Patrol coverage"),
        url=reverse("wagtailadmin_panic_patrol_coverage_report"),
        icon_name="success",
        order=100,
    )
