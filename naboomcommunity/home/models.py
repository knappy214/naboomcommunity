from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page
import uuid


class UserProfile(models.Model):
    """Extended user profile with additional community information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'), help_text=_('Contact phone number'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_('Date of birth'), help_text=_('User\'s date of birth'))
    gender = models.CharField(max_length=20, blank=True, verbose_name=_('Gender'), help_text=_('User\'s gender identity'))
    address = models.TextField(blank=True, verbose_name=_('Address'), help_text=_('User\'s physical address'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('City'), help_text=_('User\'s city of residence'))
    province = models.CharField(max_length=100, blank=True, verbose_name=_('Province'), help_text=_('User\'s province/state'))
    postal_code = models.CharField(max_length=20, blank=True, verbose_name=_('Postal code'), help_text=_('User\'s postal/zip code'))
    
    # Medical Information
    allergies = models.TextField(blank=True, verbose_name=_('Allergies'), help_text=_('User\'s known allergies'))
    medical_conditions = models.TextField(blank=True, verbose_name=_('Medical conditions'), help_text=_('User\'s medical conditions'))
    current_medications = models.TextField(blank=True, verbose_name=_('Current medications'), help_text=_('User\'s current medications'))
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, verbose_name=_('Emergency contact name'), help_text=_('Emergency contact person\'s name'))
    emergency_contact_phone = models.CharField(max_length=20, blank=True, verbose_name=_('Emergency contact phone'), help_text=_('Emergency contact person\'s phone number'))
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, verbose_name=_('Emergency contact relationship'), help_text=_('Relationship to emergency contact person'))
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en', verbose_name=_('Preferred language'), help_text=_('User\'s preferred language'))
    timezone = models.CharField(max_length=50, default='UTC', verbose_name=_('Timezone'), help_text=_('User\'s timezone'))
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email notifications'), help_text=_('Enable email notifications'))
    sms_notifications = models.BooleanField(default=False, verbose_name=_('SMS notifications'), help_text=_('Enable SMS notifications'))
    mfa_enabled = models.BooleanField(default=False, verbose_name=_('MFA enabled'), help_text=_('Enable multi-factor authentication'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'), help_text=_('Date and time when profile was created'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'), help_text=_('Date and time when profile was last updated'))
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserGroup(models.Model):
    """Community user groups for organizing members."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'), help_text=_('Name of the user group'))
    description = models.TextField(blank=True, verbose_name=_('Description'), help_text=_('Description of the user group'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'), help_text=_('Whether the group is currently active'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'), help_text=_('Date and time when group was created'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'), help_text=_('Date and time when group was last updated'))
    
    class Meta:
        verbose_name = _('User Group')
        verbose_name_plural = _('User Groups')
    
    def __str__(self):
        return self.name


class UserRole(models.Model):
    """User roles within groups with specific permissions."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'), help_text=_('Name of the user role'))
    description = models.TextField(blank=True, verbose_name=_('Description'), help_text=_('Description of the user role'))
    permissions = models.JSONField(default=dict, verbose_name=_('Permissions'), help_text=_('JSON field containing role permissions'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'), help_text=_('Whether the role is currently active'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'), help_text=_('Date and time when role was created'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'), help_text=_('Date and time when role was last updated'))
    
    class Meta:
        verbose_name = _('User Role')
        verbose_name_plural = _('User Roles')
    
    def __str__(self):
        return self.name


class UserGroupMembership(models.Model):
    """User membership in groups with assigned roles."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'), help_text=_('User who is a member of the group'))
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, verbose_name=_('Group'), help_text=_('Group that the user belongs to'))
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, verbose_name=_('Role'), help_text=_('Role assigned to the user in this group'))
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Joined at'), help_text=_('Date and time when user joined the group'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'), help_text=_('Whether the membership is currently active'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'), help_text=_('Additional notes about the membership'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'), help_text=_('Date and time when membership was created'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'), help_text=_('Date and time when membership was last updated'))
    
    class Meta:
        verbose_name = _('User Group Membership')
        verbose_name_plural = _('User Group Memberships')
        unique_together = ('user', 'group')
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role.name})"


class HomePage(Page):
    """Home page model for the community website."""
    pass


# Signal to automatically create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)
        # Automatically assign user to Member group with Member role
        from .utils import assign_user_to_default_group
        assign_user_to_default_group(instance)
