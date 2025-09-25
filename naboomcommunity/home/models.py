"""
Custom models for the home app.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from wagtail.images.models import Image, AbstractImage, AbstractRendition


class CustomImage(AbstractImage):
    """
    Custom image model that ensures proper S3 URL generation.
    """
    # Add any extra fields to image here if needed
    
    admin_form_fields = Image.admin_form_fields + (
        # Add any custom fields here to make them appear in the admin form
    )

    @property
    def default_alt_text(self):
        """
        Force editors to add specific alt text if description is empty.
        Do not use image title which is typically derived from file name.
        """
        return getattr(self, "description", None)


class CustomRendition(AbstractRendition):
    """
    Custom rendition model for the custom image model.
    """
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("image", "filter_spec", "focal_point_key"),
                name="unique_rendition",
            )
        ]
class UserProfile(models.Model):
    """
    Extended user profile with additional fields.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        blank=True
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('af', 'Afrikaans'),
        ],
        default='en'
    )
    timezone = models.CharField(max_length=50, default='Africa/Johannesburg')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} Profile"
    
    @property
    def avatar_url(self):
        """Get the URL of the user's avatar (medium size for better performance)."""
        if self.avatar:
            # Use medium size (150x150) as default for better performance
            return self.get_avatar_medium()
        return None
    
    def get_avatar_small(self):
        """Get a small version of the avatar (50x50px)."""
        if self.avatar:
            try:
                from django.urls import reverse
                from wagtail.images.utils import generate_signature
                signature = generate_signature(self.avatar.id, 'fill-50x50')
                return reverse('wagtailimages_serve', args=[signature, self.avatar.id, 'fill-50x50'])
            except Exception:
                # Fallback to original if rendition fails
                return self.avatar_url()
        return None
    
    def get_avatar_medium(self):
        """Get a medium version of the avatar (150x150px)."""
        if self.avatar:
            try:
                from django.urls import reverse
                from wagtail.images.utils import generate_signature
                signature = generate_signature(self.avatar.id, 'fill-150x150')
                return reverse('wagtailimages_serve', args=[signature, self.avatar.id, 'fill-150x150'])
            except Exception:
                # Fallback to original if rendition fails
                return self.avatar_url()
        return None
    
    def get_avatar_large(self):
        """Get a large version of the avatar (300x300px)."""
        if self.avatar:
            try:
                from django.urls import reverse
                from wagtail.images.utils import generate_signature
                signature = generate_signature(self.avatar.id, 'fill-300x300')
                return reverse('wagtailimages_serve', args=[signature, self.avatar.id, 'fill-300x300'])
            except Exception:
                # Fallback to original if rendition fails
                return self.get_avatar_original()
        return None
    
    def get_avatar_original(self):
        """Get the original full-size avatar image."""
        if self.avatar:
            try:
                from django.urls import reverse
                from wagtail.images.utils import generate_signature
                signature = generate_signature(self.avatar.id, 'original')
                return reverse('wagtailimages_serve', args=[signature, self.avatar.id, 'original'])
            except Exception:
                return None
        return None


class UserGroup(models.Model):
    """
    User groups for organizing members.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    User roles within groups.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserGroupMembership(models.Model):
    """
    Many-to-many relationship between users and groups with roles.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'group']

    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role.name})"