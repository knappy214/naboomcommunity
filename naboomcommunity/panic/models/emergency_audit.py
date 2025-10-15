"""
Emergency Audit Logging Framework
Comprehensive audit trail for all emergency response operations.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid
import json

User = get_user_model()


class EmergencyAuditLog(models.Model):
    """
    Comprehensive audit logging for emergency response operations.
    Tracks all actions, changes, and access to emergency data.
    """
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('panic_activated', 'Panic Button Activated'),
        ('location_updated', 'Location Updated'),
        ('medical_accessed', 'Medical Data Accessed'),
        ('notification_sent', 'Notification Sent'),
        ('responder_assigned', 'Responder Assigned'),
        ('status_changed', 'Status Changed'),
        ('data_encrypted', 'Data Encrypted'),
        ('data_decrypted', 'Data Decrypted'),
        ('sync_started', 'Sync Started'),
        ('sync_completed', 'Sync Completed'),
        ('external_api_called', 'External API Called'),
        ('websocket_connected', 'WebSocket Connected'),
        ('websocket_disconnected', 'WebSocket Disconnected'),
        ('authentication_failed', 'Authentication Failed'),
        ('permission_denied', 'Permission Denied'),
        ('error_occurred', 'Error Occurred'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action details
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    description = models.TextField()
    
    # User and session information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='emergency_audit_logs')
    session_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Object being acted upon (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Request/Response information
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    
    # Data changes
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Additional context
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    stack_trace = models.TextField(blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'panic_emergency_audit_log'
        verbose_name = 'Emergency Audit Log'
        verbose_name_plural = 'Emergency Audit Logs'
        
        indexes = [
            # Action type and timestamp for filtering
            models.Index(fields=['action_type', 'timestamp'], name='emergency_audit_action_idx'),
            # User and timestamp for user-specific queries
            models.Index(fields=['user', 'timestamp'], name='emergency_audit_user_idx'),
            # Severity for filtering critical events
            models.Index(fields=['severity', 'timestamp'], name='emergency_audit_severity_idx'),
            # Content type and object for object-specific queries
            models.Index(fields=['content_type', 'object_id'], name='emergency_audit_content_idx'),
            # IP address for security analysis
            models.Index(fields=['ip_address', 'timestamp'], name='emergency_audit_ip_idx'),
            # Session tracking
            models.Index(fields=['session_id', 'timestamp'], name='emergency_audit_session_idx'),
        ]
        
        # Partitioning by timestamp for performance (PostgreSQL specific)
        # This would be implemented in a custom migration
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action_type} by {self.user or 'System'} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, action_type, description, user=None, content_object=None, 
                   old_values=None, new_values=None, severity='medium', **kwargs):
        """
        Convenience method to log an action.
        
        Args:
            action_type: Type of action performed
            description: Human-readable description
            user: User who performed the action
            content_object: Object being acted upon
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            severity: Severity level
            **kwargs: Additional metadata
        """
        return cls.objects.create(
            action_type=action_type,
            description=description,
            user=user,
            content_object=content_object,
            old_values=old_values or {},
            new_values=new_values or {},
            severity=severity,
            metadata=kwargs
        )
    
    @classmethod
    def log_panic_activation(cls, user, location_data, emergency_type, **kwargs):
        """
        Log panic button activation.
        
        Args:
            user: User who activated panic button
            location_data: Location information
            emergency_type: Type of emergency
            **kwargs: Additional metadata
        """
        return cls.log_action(
            action_type='panic_activated',
            description=f'Panic button activated for {emergency_type} emergency',
            user=user,
            severity='critical',
            emergency_type=emergency_type,
            location_data=location_data,
            **kwargs
        )
    
    @classmethod
    def log_medical_access(cls, user, medical_data, access_type='read', **kwargs):
        """
        Log medical data access.
        
        Args:
            user: User accessing medical data
            medical_data: Medical information accessed
            access_type: Type of access (read, update, etc.)
            **kwargs: Additional metadata
        """
        return cls.log_action(
            action_type='medical_accessed',
            description=f'Medical data {access_type} access',
            user=user,
            severity='high',
            access_type=access_type,
            medical_data=medical_data,
            **kwargs
        )
    
    @classmethod
    def log_security_event(cls, event_type, description, user=None, ip_address=None, **kwargs):
        """
        Log security-related events.
        
        Args:
            event_type: Type of security event
            description: Event description
            user: User involved (if any)
            ip_address: IP address of the request
            **kwargs: Additional metadata
        """
        return cls.log_action(
            action_type=event_type,
            description=description,
            user=user,
            severity='high',
            ip_address=ip_address,
            **kwargs
        )


class EmergencyAuditConfig(models.Model):
    """
    Configuration for emergency audit logging.
    Controls what events to log and retention policies.
    """
    
    AUDIT_LEVELS = [
        ('minimal', 'Minimal - Critical events only'),
        ('standard', 'Standard - Important events'),
        ('detailed', 'Detailed - All events'),
        ('comprehensive', 'Comprehensive - Everything including reads'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Audit configuration
    audit_level = models.CharField(max_length=20, choices=AUDIT_LEVELS, default='standard')
    log_reads = models.BooleanField(default=False)
    log_medical_access = models.BooleanField(default=True)
    log_location_updates = models.BooleanField(default=True)
    log_notifications = models.BooleanField(default=True)
    log_websocket_events = models.BooleanField(default=False)
    
    # Retention policies
    retention_days = models.IntegerField(default=365)
    archive_after_days = models.IntegerField(default=90)
    
    # Security settings
    log_failed_attempts = models.BooleanField(default=True)
    log_suspicious_activity = models.BooleanField(default=True)
    alert_on_critical_events = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_audit_config'
        verbose_name = 'Emergency Audit Configuration'
        verbose_name_plural = 'Emergency Audit Configurations'
    
    def __str__(self):
        return f"Audit Config: {self.audit_level} (Retention: {self.retention_days} days)"
    
    @classmethod
    def get_active_config(cls):
        """
        Get the active audit configuration.
        Creates a default config if none exists.
        """
        config, created = cls.objects.get_or_create(
            defaults={
                'audit_level': 'standard',
                'retention_days': 365,
                'archive_after_days': 90,
            }
        )
        return config
