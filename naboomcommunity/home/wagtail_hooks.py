from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets import ViewSetGroup
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language, activate
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import translation
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, UserGroup, UserRole, UserGroupMembership
from .forms import UserProfileAdminForm





# Language switcher hook
@hooks.register('construct_admin_menu')
def add_language_switcher(request, menu_items):
    """Add language switcher to the admin menu."""
    current_language = get_language()
    
    # Create language switcher menu item
    from wagtail.admin.menu import MenuItem
    
    language_menu = MenuItem(
        label=f"🌍 {'Afrikaans' if current_language == 'en' else 'English'}",
        url=reverse('set_language'),
        icon_name='globe',
        order=1000,
        attrs={'target': '_blank'}
    )
    
    menu_items.append(language_menu)

# Language switching view
@hooks.register('register_admin_urls')
def register_language_switcher():
    """Register language switching URL."""
    from django.urls import path
    from django.views.generic import View
    
    class LanguageSwitchView(View):
        def get(self, request):
            current_language = get_language()
            new_language = 'af' if current_language == 'en' else 'en'
            
            # Activate the new language
            activate(new_language)
            translation.activate(new_language)
            
            # Set language in session
            request.session[translation.LANGUAGE_SESSION_KEY] = new_language
            
            # Redirect back to admin
            return HttpResponseRedirect(reverse('wagtailadmin_home'))
    
    return [
        path('language-switch/', LanguageSwitchView.as_view(), name='set_language'),
    ]

class UserProfileViewSet(ModelViewSet):
    model = UserProfile
    menu_label = _("User Profiles")
    icon = "user"
    list_display = ("user", "phone", "city", "province", "preferred_language", "created_at")
    list_filter = ("preferred_language", "city", "province", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email", "phone", "city")
    ordering = ("-created_at",)
    
    # Specify form fields to avoid ImproperlyConfigured error
    form_fields = [
        "avatar", "phone", "date_of_birth", "gender", "address", "city", 
        "province", "postal_code", "allergies", "medical_conditions", "current_medications",
        "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship",
        "preferred_language", "timezone", "email_notifications", "sms_notifications", "mfa_enabled"
    ]


class UserGroupViewSet(ModelViewSet):
    model = UserGroup
    menu_label = _("User Groups")
    icon = "group"
    list_display = ("name", "description", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description")
    ordering = ("name",)
    form_fields = ["name", "description"]
    
    # Define panels for the latest Wagtail structure
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("description"),
        ], heading=_("Group Information")),
    ]


class UserRoleViewSet(ModelViewSet):
    model = UserRole
    menu_label = _("User Roles")
    icon = "tag"
    list_display = ("name", "description", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description")
    ordering = ("name",)
    form_fields = ["name", "description", "permissions"]
    
    # Define panels for the latest Wagtail structure
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("description"),
        ], heading=_("Role Information")),
        
        MultiFieldPanel([
            FieldPanel("permissions"),
        ], heading=_("Permissions"), classname="collapsible"),
    ]


class UserGroupMembershipViewSet(ModelViewSet):
    model = UserGroupMembership
    menu_label = _("Group Memberships")
    icon = "user"
    list_display = ("user", "group", "role", "joined_at", "is_active")
    list_filter = ("is_active", "group", "role", "joined_at")
    search_fields = ("user__username", "group__name", "role__name")
    ordering = ("-joined_at",)
    form_fields = ["user", "group", "role", "is_active"]
    
    # Define panels for the latest Wagtail structure
    panels = [
        MultiFieldPanel([
            FieldPanel("user"),
            FieldPanel("group"),
            FieldPanel("role"),
            FieldPanel("is_active"),
        ], heading=_("Membership Details")),
    ]


class UserViewSet(ModelViewSet):
    model = User
    menu_label = _("Users")
    icon = "user"
    list_display = ("username", "email", "first_name", "last_name", "is_active", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    
    # Define panels for the latest Wagtail structure
    panels = [
        MultiFieldPanel([
            FieldPanel("username"),
            FieldPanel("email"),
            FieldPanel("first_name"),
            FieldPanel("last_name"),
        ], heading=_("Personal Information")),
        
        MultiFieldPanel([
            FieldPanel("is_active"),
            FieldPanel("is_staff"),
            FieldPanel("is_superuser"),
        ], heading=_("Permissions")),
        
        MultiFieldPanel([
            FieldPanel("groups"),
            FieldPanel("user_permissions"),
        ], heading=_("Groups & Permissions"), classname="collapsible"),
    ]


class CommunityGroup(ViewSetGroup):
    menu_label = _("Community")
    menu_icon = "group"
    menu_order = 200
    items = (
        UserViewSet,
        UserProfileViewSet,
        UserGroupViewSet,
        UserRoleViewSet,
        UserGroupMembershipViewSet,
    )


@hooks.register("register_admin_viewset")
def register_community_group():
    return CommunityGroup()


# Customize Wagtail admin site header
@hooks.register('construct_main_menu')
def hide_snippets_menu(request, menu_items):
    """Hide the default Snippets menu since we have our own Community section."""
    menu_items[:] = [item for item in menu_items if item.name != 'snippets']


# Add custom admin branding
@hooks.register('insert_global_admin_css')
def global_admin_css():
    """Add custom CSS for the admin interface."""
    return """
    <style>
        .wagtail-branding__icon {
            background-color: #2A4D69 !important;
        }
        .wagtail-branding__icon svg {
            fill: white !important;
        }
        .c-sidebar__branding {
            background-color: #2A4D69 !important;
        }
    </style>
    """


# Customize the admin site title
@hooks.register('construct_wagtail_userbar')
def add_custom_userbar_items(request, items):
    """Add custom items to the userbar."""
    return items
