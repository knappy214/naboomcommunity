"""Custom admin menu configuration for Panic Response module.

This mirrors the Community Hub grouped menu pattern to expose key
Panic models within the Wagtail admin main menu as a single submenu.
"""
from django.utils.translation import gettext_lazy as _
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail import hooks


@hooks.register("construct_main_menu")
def panic_response_menu(request, items):
    """Create a grouped Panic Response menu item with shortcuts to snippets.

    The links target Wagtail's snippet admin URLs for the panic app's models.
    """

    submenu_items = [
            # Incidents & alerts
            MenuItem(_("Incidents"), "/admin/snippets/panic/incident/", icon_name="warning", order=1),
            MenuItem(_("Patrol Alerts"), "/admin/snippets/panic/patrolalert/", icon_name="warning", order=2),

            # Clients & contacts
            MenuItem(_("Client Profiles"), "/admin/snippets/panic/clientprofile/", icon_name="user", order=10),
            MenuItem(_("Emergency Contacts"), "/admin/snippets/panic/emergencycontact/", icon_name="phone", order=11),
            MenuItem(_("Responders"), "/admin/snippets/panic/responder/", icon_name="group", order=12),

            # Vehicles & patrol
            MenuItem(_("Vehicles"), "/admin/snippets/panic/vehicle/", icon_name="pick", order=20),
            MenuItem(_("Patrol Waypoints"), "/admin/snippets/panic/patrolwaypoint/", icon_name="radio-full", order=21),
            MenuItem(_("Patrol Routes"), "/admin/snippets/panic/patrolroute/", icon_name="site", order=22),
            MenuItem(_("Patrol Shifts"), "/admin/snippets/panic/patrolshift/", icon_name="time", order=23),

            # Escalation rules / targets
            MenuItem(_("Escalation Rules"), "/admin/snippets/panic/escalationrule/", icon_name="cogs", order=30),
            MenuItem(_("Escalation Targets"), "/admin/snippets/panic/escalationtarget/", icon_name="crosshairs", order=31),

            # Messaging / devices
            MenuItem(_("Inbound Messages"), "/admin/snippets/panic/inboundmessage/", icon_name="mail", order=40),
            MenuItem(_("Outbound Messages"), "/admin/snippets/panic/outboundmessage/", icon_name="mail", order=41),
            MenuItem(_("Push Devices"), "/admin/snippets/panic/pushdevice/", icon_name="mobile-alt", order=42),

    ]

    # Optional Reports shortcut (visible only if user has permission)
    try:
        if request.user.has_perm("panic.view_patrolalert"):
            submenu_items.append(
                MenuItem(
                    _("Patrol Coverage Report"),
                    "/admin/panic/reports/patrol-coverage/",
                    icon_name="success",
                    order=90,
                )
            )
    except Exception:
        # If permission check fails for any reason, skip adding the report link
        pass

    submenu = Menu(items=submenu_items)

    items.append(
        SubmenuMenuItem(
            _("Panic Response"),
            submenu,
            icon_name="warning",
            order=201,
        )
    )
