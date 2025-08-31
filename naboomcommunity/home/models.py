from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.models import Page
import uuid


class UserProfile(models.Model):
    """
    Extended user profile model that extends Django's built-in User model.
    This approach avoids circular dependencies and is more compatible with existing setups.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional profile fields
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    date_of_birth = models.DateField(null=True, blank=True, help_text="User's date of birth")
    gender = models.CharField(max_length=20, blank=True, help_text="User's gender identity")
    address = models.TextField(blank=True, help_text="Full residential address")
    city = models.CharField(max_length=100, blank=True, help_text="City of residence")
    province = models.CharField(max_length=100, blank=True, help_text="Province/State of residence")
    postal_code = models.CharField(max_length=20, blank=True, help_text="Postal/ZIP code")
    
    # Medical information
    allergies = models.TextField(blank=True, help_text="Known allergies and sensitivities")
    medical_conditions = models.TextField(blank=True, help_text="Current medical conditions")
    current_medications = models.TextField(blank=True, help_text="Currently prescribed medications")
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, help_text="Emergency contact person's name")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, help_text="Emergency contact phone number")
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, help_text="Relationship to emergency contact")
    
    # Preferences
    preferred_language = models.CharField(
        max_length=10, 
        default='en',
        choices=[
            ('en', 'English'),
            ('af', 'Afrikaans'),
        ],
        help_text="Preferred language for communications"
    )
    timezone = models.CharField(max_length=50, default='UTC', help_text="User's timezone")
    email_notifications = models.BooleanField(default=True, help_text="Receive email notifications")
    sms_notifications = models.BooleanField(default=False, help_text="Receive SMS notifications")
    mfa_enabled = models.BooleanField(default=False, help_text="Multi-factor authentication enabled")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_full_address(self):
        """Return the complete formatted address."""
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.city:
            address_parts.append(self.city)
        if self.province:
            address_parts.append(self.province)
        if self.postal_code:
            address_parts.append(self.postal_code)
        return ", ".join(address_parts) if address_parts else "No address provided"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)
        # Automatically assign user to Member group with Member role
        from .utils import assign_user_to_default_group
        assign_user_to_default_group(instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when a User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class UserGroup(models.Model):
    """
    User groups for organizing community members into categories.
    Examples: Elders, Youth, Choir, Tech Support, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Name of the user group")
    description = models.TextField(blank=True, help_text="Description of the group's purpose")
    is_active = models.BooleanField(default=True, help_text="Whether the group is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_group"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    User roles defining permissions within groups.
    Examples: Leader, Member, Moderator, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Name of the role")
    description = models.TextField(blank=True, help_text="Description of the role's responsibilities")
    permissions = models.JSONField(default=dict, help_text="JSON object defining role permissions")
    is_active = models.BooleanField(default=True, help_text="Whether the role is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_role"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserGroupMembership(models.Model):
    """
    Many-to-many relationship between users, groups, and roles.
    Tracks user membership in groups with specific roles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='group_memberships',
        help_text="User who is a member of the group"
    )
    group = models.ForeignKey(
        UserGroup, 
        on_delete=models.CASCADE, 
        related_name='members',
        help_text="Group the user belongs to"
    )
    role = models.ForeignKey(
        UserRole, 
        on_delete=models.CASCADE, 
        related_name='memberships',
        help_text="Role the user has in the group"
    )
    joined_at = models.DateTimeField(auto_now_add=True, help_text="When the user joined the group")
    is_active = models.BooleanField(default=True, help_text="Whether the membership is currently active")
    notes = models.TextField(blank=True, help_text="Additional notes about the membership")
    
    class Meta:
        db_table = "user_group_membership"
        unique_together = ('user', 'group')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role.name})"


class HomePage(Page):
    """Home page model for the community website."""
    pass
