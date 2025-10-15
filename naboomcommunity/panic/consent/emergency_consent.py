"""
Emergency Consent Management System
Handles medical data consent and privacy controls for emergency response.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class EmergencyConsent(models.Model):
    """
    Emergency consent management for medical data access.
    """
    
    CONSENT_TYPES = [
        ('medical_basic', 'Basic Medical Information'),
        ('medical_full', 'Full Medical Information'),
        ('location_tracking', 'Location Tracking'),
        ('emergency_contact', 'Emergency Contact Access'),
        ('family_notification', 'Family Notification'),
        ('external_services', 'External Emergency Services'),
        ('data_sharing', 'Data Sharing with Responders'),
    ]
    
    CONSENT_STATUS = [
        ('pending', 'Pending'),
        ('granted', 'Granted'),
        ('denied', 'Denied'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_consents')
    
    # Consent details
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    status = models.CharField(max_length=20, choices=CONSENT_STATUS, default='pending')
    
    # Consent data
    granted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    # Consent metadata
    consent_text = models.TextField(help_text="Text of the consent agreement")
    version = models.CharField(max_length=20, default='1.0')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional context
    context_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_consent'
        verbose_name = 'Emergency Consent'
        verbose_name_plural = 'Emergency Consents'
        
        indexes = [
            models.Index(fields=['user', 'consent_type'], name='emergency_consent_user_type_idx'),
            models.Index(fields=['status', 'expires_at'], name='emergency_consent_status_expiry_idx'),
            models.Index(fields=['consent_type', 'status'], name='emergency_consent_type_status_idx'),
        ]
        
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'consent_type'],
                name='emergency_consent_user_type_unique'
            ),
        ]
        
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.consent_type} ({self.status})"
    
    def clean(self):
        """Validate consent data."""
        super().clean()
        
        if self.status == 'granted' and not self.granted_at:
            raise ValidationError("Granted consent must have a granted_at timestamp")
        
        if self.status == 'revoked' and not self.revoked_at:
            raise ValidationError("Revoked consent must have a revoked_at timestamp")
        
        if self.expires_at and self.granted_at and self.expires_at <= self.granted_at:
            raise ValidationError("Expiration date must be after grant date")
    
    def is_valid(self):
        """Check if consent is currently valid."""
        if self.status != 'granted':
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        return True
    
    def grant(self, ip_address=None, user_agent=None, context_data=None):
        """Grant consent."""
        self.status = 'granted'
        self.granted_at = timezone.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        if context_data:
            self.context_data.update(context_data)
        self.save()
        
        logger.info(f"Emergency consent granted: {self.user.username} - {self.consent_type}")
    
    def revoke(self, notes=None):
        """Revoke consent."""
        self.status = 'revoked'
        self.revoked_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
        
        logger.info(f"Emergency consent revoked: {self.user.username} - {self.consent_type}")
    
    def expire(self):
        """Mark consent as expired."""
        self.status = 'expired'
        self.save()
        
        logger.info(f"Emergency consent expired: {self.user.username} - {self.consent_type}")


class EmergencyConsentTemplate(models.Model):
    """
    Template for emergency consent agreements.
    """
    
    CONSENT_CATEGORIES = [
        ('medical', 'Medical Information'),
        ('location', 'Location Data'),
        ('emergency', 'Emergency Response'),
        ('privacy', 'Privacy & Data Protection'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    consent_type = models.CharField(max_length=50, choices=EmergencyConsent.CONSENT_TYPES)
    category = models.CharField(max_length=20, choices=CONSENT_CATEGORIES)
    
    # Template content
    title = models.CharField(max_length=255)
    description = models.TextField()
    consent_text = models.TextField()
    legal_text = models.TextField(blank=True)
    
    # Template metadata
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    is_required = models.BooleanField(default=True)
    expires_days = models.IntegerField(null=True, blank=True, help_text="Consent expiration in days")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_consent_template'
        verbose_name = 'Emergency Consent Template'
        verbose_name_plural = 'Emergency Consent Templates'
        
        indexes = [
            models.Index(fields=['consent_type', 'is_active'], name='emergency_consent_template_type_active_idx'),
            models.Index(fields=['category', 'is_active'], name='emergency_consent_template_category_active_idx'),
        ]
        
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.consent_type})"
    
    def get_consent_text(self, user=None, context=None):
        """
        Get personalized consent text.
        
        Args:
            user: User requesting consent
            context: Additional context data
            
        Returns:
            Personalized consent text
        """
        text = self.consent_text
        
        if user:
            text = text.replace('{username}', user.username)
            text = text.replace('{user_id}', str(user.id))
        
        if context:
            for key, value in context.items():
                text = text.replace(f'{{{key}}}', str(value))
        
        return text


class EmergencyConsentManager:
    """
    Manager for emergency consent operations.
    """
    
    @staticmethod
    def get_user_consent(user, consent_type):
        """
        Get user's consent for a specific type.
        
        Args:
            user: User to check
            consent_type: Type of consent
            
        Returns:
            EmergencyConsent instance or None
        """
        try:
            return EmergencyConsent.objects.get(
                user=user,
                consent_type=consent_type,
                status='granted'
            )
        except EmergencyConsent.DoesNotExist:
            return None
    
    @staticmethod
    def has_valid_consent(user, consent_type):
        """
        Check if user has valid consent for a specific type.
        
        Args:
            user: User to check
            consent_type: Type of consent
            
        Returns:
            Boolean
        """
        consent = EmergencyConsentManager.get_user_consent(user, consent_type)
        return consent and consent.is_valid()
    
    @staticmethod
    def get_required_consents(user):
        """
        Get all required consents for a user.
        
        Args:
            user: User to check
            
        Returns:
            List of required consent types
        """
        required_templates = EmergencyConsentTemplate.objects.filter(
            is_active=True,
            is_required=True
        )
        
        required_consents = []
        for template in required_templates:
            if not EmergencyConsentManager.has_valid_consent(user, template.consent_type):
                required_consents.append(template)
        
        return required_consents
    
    @staticmethod
    def create_consent(user, consent_type, consent_text, version='1.0', 
                      expires_days=None, ip_address=None, user_agent=None, 
                      context_data=None):
        """
        Create a new consent record.
        
        Args:
            user: User granting consent
            consent_type: Type of consent
            consent_text: Consent agreement text
            version: Consent version
            expires_days: Expiration in days
            ip_address: IP address
            user_agent: User agent
            context_data: Additional context
            
        Returns:
            EmergencyConsent instance
        """
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timezone.timedelta(days=expires_days)
        
        consent = EmergencyConsent.objects.create(
            user=user,
            consent_type=consent_type,
            consent_text=consent_text,
            version=version,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            context_data=context_data or {}
        )
        
        return consent
    
    @staticmethod
    def grant_consent(user, consent_type, ip_address=None, user_agent=None, 
                     context_data=None):
        """
        Grant consent for a user.
        
        Args:
            user: User granting consent
            consent_type: Type of consent
            ip_address: IP address
            user_agent: User agent
            context_data: Additional context
            
        Returns:
            EmergencyConsent instance
        """
        try:
            consent = EmergencyConsent.objects.get(
                user=user,
                consent_type=consent_type
            )
        except EmergencyConsent.DoesNotExist:
            # Create new consent
            template = EmergencyConsentTemplate.objects.get(
                consent_type=consent_type,
                is_active=True
            )
            consent = EmergencyConsentManager.create_consent(
                user=user,
                consent_type=consent_type,
                consent_text=template.get_consent_text(user, context_data),
                version=template.version,
                expires_days=template.expires_days,
                ip_address=ip_address,
                user_agent=user_agent,
                context_data=context_data
            )
        
        consent.grant(ip_address, user_agent, context_data)
        return consent
    
    @staticmethod
    def revoke_consent(user, consent_type, notes=None):
        """
        Revoke consent for a user.
        
        Args:
            user: User revoking consent
            consent_type: Type of consent
            notes: Revocation notes
            
        Returns:
            EmergencyConsent instance or None
        """
        try:
            consent = EmergencyConsent.objects.get(
                user=user,
                consent_type=consent_type,
                status='granted'
            )
            consent.revoke(notes)
            return consent
        except EmergencyConsent.DoesNotExist:
            return None
    
    @staticmethod
    def cleanup_expired_consents():
        """
        Clean up expired consents.
        
        Returns:
            Number of consents cleaned up
        """
        expired_consents = EmergencyConsent.objects.filter(
            status='granted',
            expires_at__lt=timezone.now()
        )
        
        count = expired_consents.count()
        for consent in expired_consents:
            consent.expire()
        
        logger.info(f"Cleaned up {count} expired consents")
        return count
