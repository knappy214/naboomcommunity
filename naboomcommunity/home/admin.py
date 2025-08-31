from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserGroup, UserRole, UserGroupMembership

# Unregister the default User admin
admin.site.unregister(User)

# Register custom User admin with UserProfile inline
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.register(User, UserAdmin)

# Note: UserProfile, UserGroup, UserRole, and UserGroupMembership are now managed through Wagtail admin
# via wagtail_hooks.py, so we don't need to register them here.
