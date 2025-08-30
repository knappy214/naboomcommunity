from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, UserGroup, UserRole, UserGroupMembership


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile model."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'phone', 'date_of_birth', 'gender', 'address', 'city', 'province', 'postal_code'
            )
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions', 'current_medications'),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': (
                'preferred_language', 'timezone', 'email_notifications', 
                'sms_notifications', 'mfa_enabled'
            )
        }),
    )


class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the User model with inline UserProfile.
    Organizes fields into logical sections for better usability.
    """
    inlines = (UserProfileInline,)
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_phone', 'get_city', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'profile__preferred_language', 'profile__city', 'profile__province', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone', 'profile__city')
    ordering = ('-date_joined',)
    
    def get_phone(self, obj):
        """Get phone number from profile."""
        return getattr(obj.profile, 'phone', '') if hasattr(obj, 'profile') else ''
    get_phone.short_description = 'Phone'
    
    def get_city(self, obj):
        """Get city from profile."""
        return getattr(obj.profile, 'city', '') if hasattr(obj, 'profile') else ''
    get_city.short_description = 'City'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('profile')


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'phone', 'city', 'province', 'preferred_language', 'created_at')
    list_filter = ('preferred_language', 'city', 'province', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone', 'city')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': (
                'phone', 'date_of_birth', 'gender', 'address', 'city', 'province', 'postal_code'
            )
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions', 'current_medications'),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': (
                'preferred_language', 'timezone', 'email_notifications', 
                'sms_notifications', 'mfa_enabled'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('user')


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    """Admin interface for user groups."""
    list_display = ('name', 'description', 'is_active', 'created_at', 'member_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def member_count(self, obj):
        """Display the number of active members in the group."""
        count = obj.members.filter(is_active=True).count()
        return format_html('<span style="color: {};">{}</span>', 
                         'green' if count > 0 else 'red', count)
    member_count.short_description = 'Active Members'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for user roles."""
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to show permissions as a more user-friendly interface."""
        form = super().get_form(request, obj, **kwargs)
        if 'permissions' in form.base_fields:
            form.base_fields['permissions'].help_text = (
                'Enter permissions as JSON. Example: {"can_edit": true, "can_delete": false}'
            )
        return form


@admin.register(UserGroupMembership)
class UserGroupMembershipAdmin(admin.ModelAdmin):
    """Admin interface for user group memberships."""
    list_display = ('user', 'group', 'role', 'joined_at', 'is_active')
    list_filter = ('is_active', 'group', 'role', 'joined_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'group__name', 'role__name')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at',)
    
    autocomplete_fields = ('user', 'group', 'role')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('user', 'group', 'role')
