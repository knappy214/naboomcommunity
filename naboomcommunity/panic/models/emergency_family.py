"""
Emergency Family Models
Models for family and emergency contact management.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid

User = get_user_model()


class EmergencyContact(models.Model):
    """
    Emergency contact information for users.
    Stores family, medical, and friend contacts for emergency notifications.
    """
    
    # Contact types
    CONTACT_TYPES = [
        ('family', 'Family Member'),
        ('medical', 'Medical Contact'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague'),
        ('neighbor', 'Neighbor'),
        ('other', 'Other')
    ]
    
    # Priority levels
    PRIORITIES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    # Relationships
    RELATIONSHIPS = [
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('child', 'Child'),
        ('grandparent', 'Grandparent'),
        ('grandchild', 'Grandchild'),
        ('aunt', 'Aunt'),
        ('uncle', 'Uncle'),
        ('cousin', 'Cousin'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague'),
        ('neighbor', 'Neighbor'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('caregiver', 'Caregiver'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    
    # Contact information
    name = models.CharField(max_length=255, help_text="Full name of the contact")
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        help_text="Phone number with country code"
    )
    email = models.EmailField(blank=True, null=True, help_text="Email address (optional)")
    
    # Contact details
    relationship = models.CharField(
        max_length=50,
        choices=RELATIONSHIPS,
        default='friend',
        help_text="Relationship to the user"
    )
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPES,
        default='friend',
        help_text="Type of contact"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITIES,
        default='medium',
        help_text="Priority level for notifications"
    )
    
    # Notification settings
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary contact for emergency notifications"
    )
    notifications_enabled = models.BooleanField(
        default=True,
        help_text="Enable notifications to this contact"
    )
    preferred_channels = models.JSONField(
        default=list,
        help_text="Preferred notification channels (sms, email, push, etc.)"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this contact"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Physical address (optional)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emergency_contacts'
        verbose_name = 'Emergency Contact'
        verbose_name_plural = 'Emergency Contacts'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['user', 'contact_type']),
            models.Index(fields=['user', 'priority']),
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.user.username}"
    
    def clean(self):
        """Validate contact data."""
        from django.core.exceptions import ValidationError
        
        # Ensure at least one contact method
        if not self.phone and not self.email:
            raise ValidationError("At least one contact method (phone or email) is required.")
        
        # Ensure only one primary contact per user
        if self.is_primary:
            existing_primary = EmergencyContact.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(id=self.id)
            if existing_primary.exists():
                raise ValidationError("Only one primary contact is allowed per user.")
    
    def save(self, *args, **kwargs):
        """Save with validation."""
        self.clean()
        super().save(*args, **kwargs)


class NotificationTemplate(models.Model):
    """
    Notification templates for different emergency types and channels.
    """
    
    # Template types
    TEMPLATE_TYPES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('ussd', 'USSD')
    ]
    
    # Emergency types
    EMERGENCY_TYPES = [
        ('panic', 'Panic Button'),
        ('medical', 'Medical Emergency'),
        ('fire', 'Fire Emergency'),
        ('crime', 'Crime Emergency'),
        ('accident', 'Accident'),
        ('general', 'General Emergency')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template identification
    name = models.CharField(max_length=255, help_text="Template name")
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        help_text="Type of notification template"
    )
    emergency_type = models.CharField(
        max_length=20,
        choices=EMERGENCY_TYPES,
        help_text="Emergency type this template is for"
    )
    
    # Template content
    subject = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Email subject or notification title"
    )
    message = models.TextField(help_text="Template message content")
    
    # Template variables
    variables = models.JSONField(
        default=list,
        help_text="Available template variables (e.g., user_name, location, timestamp)"
    )
    
    # Template settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is active"
    )
    priority = models.CharField(
        max_length=20,
        choices=EmergencyContact.PRIORITIES,
        default='medium',
        help_text="Default priority for this template"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        ordering = ['emergency_type', 'template_type', 'name']
        unique_together = ['template_type', 'emergency_type', 'name']
        indexes = [
            models.Index(fields=['template_type', 'emergency_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_type} - {self.emergency_type})"
    
    def render_template(self, context: dict) -> str:
        """
        Render template with provided context.
        
        Args:
            context: Template variables
            
        Returns:
            Rendered template string
        """
        try:
            # Simple template rendering (in production, use a proper template engine)
            rendered = self.message
            
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            return rendered
        except Exception as e:
            # Return original message if rendering fails
            return self.message


class NotificationLog(models.Model):
    """
    Log of sent notifications for audit and tracking purposes.
    """
    
    # Notification status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]
    
    # Notification channels
    CHANNEL_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('ussd', 'USSD')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Notification details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_logs')
    emergency_id = models.UUIDField(help_text="Associated emergency ID")
    contact = models.ForeignKey(
        EmergencyContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs'
    )
    
    # Notification content
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        help_text="Notification channel"
    )
    recipient = models.CharField(max_length=255, help_text="Recipient identifier (phone, email, etc.)")
    subject = models.CharField(max_length=255, blank=True, null=True, help_text="Message subject")
    message = models.TextField(help_text="Message content")
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Notification status"
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="External service message ID"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if failed"
    )
    
    # Delivery tracking
    sent_at = models.DateTimeField(blank=True, null=True, help_text="When notification was sent")
    delivered_at = models.DateTimeField(blank=True, null=True, help_text="When notification was delivered")
    read_at = models.DateTimeField(blank=True, null=True, help_text="When notification was read")
    
    # Metadata
    priority = models.CharField(
        max_length=20,
        choices=EmergencyContact.PRIORITIES,
        default='medium',
        help_text="Notification priority"
    )
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retry attempts")
    max_retries = models.PositiveIntegerField(default=3, help_text="Maximum retry attempts")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_logs'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'emergency_id']),
            models.Index(fields=['contact']),
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_id']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['delivered_at']),
        ]
    
    def __str__(self):
        return f"{self.channel} to {self.recipient} - {self.status}"
    
    def mark_sent(self, external_id: str = None):
        """Mark notification as sent."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save()
    
    def mark_delivered(self):
        """Mark notification as delivered."""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message: str = None):
        """Mark notification as failed."""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.save()
    
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return self.retry_count < self.max_retries and self.status in ['pending', 'failed']


class NotificationPreference(models.Model):
    """
    User notification preferences for emergency notifications.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Channel preferences
    enabled_channels = models.JSONField(
        default=list,
        help_text="Enabled notification channels"
    )
    default_priority = models.CharField(
        max_length=20,
        choices=EmergencyContact.PRIORITIES,
        default='high',
        help_text="Default notification priority"
    )
    
    # Emergency type preferences
    enabled_emergency_types = models.JSONField(
        default=list,
        help_text="Enabled emergency types for notifications"
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(
        default=False,
        help_text="Enable quiet hours"
    )
    quiet_hours_start = models.TimeField(
        blank=True,
        null=True,
        help_text="Quiet hours start time"
    )
    quiet_hours_end = models.TimeField(
        blank=True,
        null=True,
        help_text="Quiet hours end time"
    )
    
    # Privacy settings
    location_sharing_enabled = models.BooleanField(
        default=True,
        help_text="Share location in notifications"
    )
    medical_sharing_enabled = models.BooleanField(
        default=True,
        help_text="Share medical information in notifications"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['quiet_hours_enabled']),
        ]
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:
            # Quiet hours span midnight
            return now >= start or now <= end
    
    def get_effective_channels(self) -> list:
        """Get effective notification channels considering quiet hours."""
        if self.is_quiet_hours():
            # During quiet hours, only send critical notifications
            return ['sms']  # SMS for critical notifications
        else:
            return self.enabled_channels or ['sms', 'email']
