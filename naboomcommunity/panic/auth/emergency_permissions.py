"""
Emergency Response Authentication and Permissions
Advanced permission system for emergency response operations.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class EmergencyPermission(models.Model):
    """
    Custom emergency response permissions with context and conditions.
    """
    
    PERMISSION_TYPES = [
        ('panic_activate', 'Activate Panic Button'),
        ('location_access', 'Access Location Data'),
        ('medical_access', 'Access Medical Data'),
        ('notification_send', 'Send Notifications'),
        ('responder_assign', 'Assign Responders'),
        ('audit_view', 'View Audit Logs'),
        ('admin_override', 'Admin Override'),
        ('offline_sync', 'Offline Data Sync'),
        ('websocket_connect', 'WebSocket Connection'),
        ('external_api', 'External API Access'),
    ]
    
    SCOPE_LEVELS = [
        ('own', 'Own Data Only'),
        ('family', 'Family Members'),
        ('neighborhood', 'Neighborhood'),
        ('zone', 'Emergency Zone'),
        ('global', 'Global Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    permission_type = models.CharField(max_length=50, choices=PERMISSION_TYPES)
    scope_level = models.CharField(max_length=20, choices=SCOPE_LEVELS, default='own')
    
    # Permission conditions
    requires_consent = models.BooleanField(default=True)
    requires_verification = models.BooleanField(default=False)
    emergency_only = models.BooleanField(default=False)
    
    # Time-based restrictions
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_permission'
        verbose_name = 'Emergency Permission'
        verbose_name_plural = 'Emergency Permissions'
        
        indexes = [
            models.Index(fields=['permission_type', 'is_active'], name='emergency_permission_type_active_idx'),
            models.Index(fields=['scope_level'], name='emergency_permission_scope_idx'),
            models.Index(fields=['valid_until'], name='emergency_permission_validity_idx'),
        ]
        
        ordering = ['permission_type', 'scope_level']
    
    def __str__(self):
        return f"{self.name} ({self.permission_type})"
    
    def is_valid(self):
        """Check if permission is currently valid."""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True


class EmergencyUserPermission(models.Model):
    """
    User-specific emergency permissions with conditions and overrides.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_permissions')
    permission = models.ForeignKey(EmergencyPermission, on_delete=models.CASCADE)
    
    # Permission conditions
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Override conditions
    override_consent = models.BooleanField(default=False)
    override_verification = models.BooleanField(default=False)
    emergency_override = models.BooleanField(default=False)
    
    # Additional context
    context_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_user_permission'
        verbose_name = 'Emergency User Permission'
        verbose_name_plural = 'Emergency User Permissions'
        
        indexes = [
            models.Index(fields=['user', 'permission'], name='emergency_user_permission_user_perm_idx'),
            models.Index(fields=['user', 'is_active'], name='emergency_user_permission_user_active_idx'),
            models.Index(fields=['expires_at'], name='emergency_user_permission_expiry_idx'),
            models.Index(fields=['permission', 'is_active'], name='emergency_user_permission_perm_active_idx'),
        ]
        
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'permission'],
                name='emergency_user_permission_unique'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.permission.name}"
    
    def is_valid(self):
        """Check if user permission is currently valid."""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if not self.permission.is_valid():
            return False
        
        if self.expires_at and now > self.expires_at:
            return False
        
        return True


class EmergencyRole(models.Model):
    """
    Emergency response roles with predefined permission sets.
    """
    
    ROLE_TYPES = [
        ('citizen', 'Citizen'),
        ('responder', 'Emergency Responder'),
        ('coordinator', 'Emergency Coordinator'),
        ('admin', 'Emergency Administrator'),
        ('medical', 'Medical Professional'),
        ('security', 'Security Personnel'),
        ('family', 'Family Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES)
    description = models.TextField(blank=True)
    
    # Role permissions
    permissions = models.ManyToManyField(EmergencyPermission, blank=True, related_name='roles')
    
    # Role properties
    is_default = models.BooleanField(default=False)
    requires_verification = models.BooleanField(default=False)
    emergency_priority = models.IntegerField(default=1, help_text="Priority level (1=highest)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_role'
        verbose_name = 'Emergency Role'
        verbose_name_plural = 'Emergency Roles'
        
        indexes = [
            models.Index(fields=['role_type'], name='emergency_role_type_idx'),
            models.Index(fields=['is_default'], name='emergency_role_default_idx'),
            models.Index(fields=['emergency_priority'], name='emergency_role_priority_idx'),
        ]
        
        ordering = ['emergency_priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.role_type})"


class EmergencyUserRole(models.Model):
    """
    User roles in emergency response system.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_roles')
    role = models.ForeignKey(EmergencyRole, on_delete=models.CASCADE)
    
    # Role assignment
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Role context
    context_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_user_role'
        verbose_name = 'Emergency User Role'
        verbose_name_plural = 'Emergency User Roles'
        
        indexes = [
            models.Index(fields=['user', 'role'], name='emergency_user_role_user_role_idx'),
            models.Index(fields=['user', 'is_active'], name='emergency_user_role_user_active_idx'),
            models.Index(fields=['expires_at'], name='emergency_user_role_expiry_idx'),
        ]
        
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role'],
                name='emergency_user_role_unique'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    def is_valid(self):
        """Check if user role is currently valid."""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.expires_at and now > self.expires_at:
            return False
        
        return True


class EmergencyAccessLog(models.Model):
    """
    Log of emergency system access attempts and permissions used.
    """
    
    ACCESS_TYPES = [
        ('granted', 'Access Granted'),
        ('denied', 'Access Denied'),
        ('expired', 'Permission Expired'),
        ('insufficient', 'Insufficient Permissions'),
        ('consent_required', 'Consent Required'),
        ('verification_required', 'Verification Required'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_access_logs')
    permission = models.ForeignKey(EmergencyPermission, on_delete=models.CASCADE, null=True, blank=True)
    
    # Access details
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    resource_type = models.CharField(max_length=100)
    resource_id = models.UUIDField(null=True, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    
    # Additional data
    context_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'panic_emergency_access_log'
        verbose_name = 'Emergency Access Log'
        verbose_name_plural = 'Emergency Access Logs'
        
        indexes = [
            models.Index(fields=['user', 'timestamp'], name='emergency_access_log_user_timestamp_idx'),
            models.Index(fields=['access_type', 'timestamp'], name='emergency_access_log_type_timestamp_idx'),
            models.Index(fields=['resource_type', 'resource_id'], name='emergency_access_log_resource_idx'),
            models.Index(fields=['ip_address', 'timestamp'], name='emergency_access_log_ip_timestamp_idx'),
        ]
        
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.access_type} - {self.resource_type}"
