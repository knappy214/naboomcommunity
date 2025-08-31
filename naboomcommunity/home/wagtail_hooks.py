from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets import ViewSetGroup

from .models import UserProfile, UserGroup, UserRole, UserGroupMembership


class UserProfileViewSet(ModelViewSet):
    model = UserProfile
    menu_label = "User Profiles"
    icon = "user"
    list_display = ("user", "phone", "city", "province", "preferred_language", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone", "city")
    ordering = ("-created_at",)


class UserGroupViewSet(ModelViewSet):
    model = UserGroup
    menu_label = "User Groups"
    icon = "group"
    list_display = ("name", "description", "is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)


class UserRoleViewSet(ModelViewSet):
    model = UserRole
    menu_label = "User Roles"
    icon = "group"
    list_display = ("name", "description", "is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)


class UserGroupMembershipViewSet(ModelViewSet):
    model = UserGroupMembership
    menu_label = "Group Memberships"
    icon = "user"
    list_display = ("user", "group", "role", "joined_at", "is_active")
    search_fields = ("user__username", "group__name", "role__name")
    list_filter = ("is_active", "group", "role")
    ordering = ("-joined_at",)


class CommunityGroup(ViewSetGroup):
    menu_label = "Community"
    menu_icon = "group"
    menu_order = 200
    items = (
        UserProfileViewSet,
        UserGroupViewSet,
        UserRoleViewSet,
        UserGroupMembershipViewSet,
    )


@hooks.register("register_admin_viewset")
def register_community_group():
    return CommunityGroup()
