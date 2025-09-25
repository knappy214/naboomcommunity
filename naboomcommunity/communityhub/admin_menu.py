"""Custom admin menu configuration for Community Hub."""
from django.utils.translation import gettext_lazy as _
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail import hooks


@hooks.register("construct_main_menu")
def community_hub_menu(request, items):
    """Create a grouped Community Hub menu item."""
    
    # Create submenu items for Community Hub
    community_hub_submenu = Menu(
        items=[
            MenuItem(
                _("Channels"),
                "/admin/snippets/communityhub/channel/",
                icon_name="site",
                order=1,
            ),
            MenuItem(
                _("Moderation policies"),
                "/admin/snippets/communityhub/channelmoderationpolicy/",
                icon_name="warning",
                order=2,
            ),
            MenuItem(
                _("Alert policies"),
                "/admin/snippets/communityhub/channelalertpolicy/",
                icon_name="warning-inverse",
                order=3,
            ),
            MenuItem(
                _("Invites"),
                "/admin/snippets/communityhub/channelinvite/",
                icon_name="mail",
                order=4,
            ),
            MenuItem(
                _("Join requests"),
                "/admin/snippets/communityhub/channeljoinrequest/",
                icon_name="user",
                order=5,
            ),
            MenuItem(
                _("Canned reasons"),
                "/admin/snippets/communityhub/cannedreportreason/",
                icon_name="help",
                order=6,
            ),
            MenuItem(
                _("Channel configs"),
                "/admin/snippets/communityhub/channelconfiguration/",
                icon_name="cog",
                order=7,
            ),
        ]
    )
    
    # Add the main Community Hub menu item with submenu to the items list
    items.append(
        SubmenuMenuItem(
            _("Community Hub"),
            community_hub_submenu,
            icon_name="group",
            order=200,
        )
    )
