"""
External Services Models
Models for external emergency service integration and dispatch tracking.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class ExternalServiceProvider(models.Model):
    """
    External emergency service provider configuration.
    Stores configuration for different emergency service providers.
    """
    
    # Service types
    SERVICE_TYPES = [
        ('police', 'Police Emergency Services'),
        ('ambulance', 'Medical Emergency Services'),
        ('fire', 'Fire Emergency Services'),
        ('rescue', 'Search and Rescue Services'),
        ('disaster', 'Disaster Management Services'),
        ('security', 'Private Security Services'),
        ('community', 'Community Emergency Response')
    ]
    
    # Integration protocols
    PROTOCOLS = [
        ('rest_api', 'REST API'),
        ('soap', 'SOAP Web Service'),
        ('webhook', 'Webhook'),
        ('sms', 'SMS Gateway'),
        ('ussd', 'USSD Gateway'),
        ('radio', 'Radio Dispatch'),
        ('custom', 'Custom Protocol')
    ]
    
    # Service status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('deprecated', 'Deprecated')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Service identification
    name = models.CharField(max_length=255, help_text="Service provider name")
    service_type = models.CharField(
        max_length=50,
        choices=SERVICE_TYPES,
        help_text="Type of emergency service"
    )
    protocol = models.CharField(
        max_length=20,
        choices=PROTOCOLS,
        help_text="Integration protocol"
    )
    
    # Service configuration
    endpoint = models.URLField(
        max_length=500,
        validators=[URLValidator()],
        help_text="Service endpoint URL"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="API key or authentication token"
    )
    username = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Username for authentication"
    )
    password = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Password for authentication"
    )
    
    # Service settings
    timeout = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
        help_text="Request timeout in seconds"
    )
    retry_attempts = models.PositiveIntegerField(
        default=3,
        validators=[MaxValueValidator(10)],
        help_text="Number of retry attempts"
    )
    retry_delay = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Delay between retries in seconds"
    )
    
    # Priority mapping
    priority_mapping = models.JSONField(
        default=dict,
        help_text="Mapping of internal priorities to service priorities"
    )
    
    # Service status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Service status"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary service for this type"
    )
    
    # Health check settings
    health_check_enabled = models.BooleanField(
        default=True,
        help_text="Enable health checks"
    )
    health_check_interval = models.PositiveIntegerField(
        default=300,
        validators=[MinValueValidator(60), MaxValueValidator(3600)],
        help_text="Health check interval in seconds"
    )
    health_check_endpoint = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Health check endpoint URL"
    )
    
    # Additional configuration
    custom_headers = models.JSONField(
        default=dict,
        help_text="Custom HTTP headers"
    )
    custom_parameters = models.JSONField(
        default=dict,
        help_text="Custom parameters"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Service description"
    )
    contact_info = models.JSONField(
        default=dict,
        help_text="Contact information"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_health_check = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'external_service_providers'
        verbose_name = 'External Service Provider'
        verbose_name_plural = 'External Service Providers'
        ordering = ['service_type', 'name']
        unique_together = ['service_type', 'name']
        indexes = [
            models.Index(fields=['service_type', 'status']),
            models.Index(fields=['protocol']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['last_health_check']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.service_type})"
    
    def clean(self):
        """Validate service configuration."""
        from django.core.exceptions import ValidationError
        
        # Validate endpoint for REST API and SOAP
        if self.protocol in ['rest_api', 'soap'] and not self.endpoint:
            raise ValidationError("Endpoint is required for REST API and SOAP protocols.")
        
        # Validate API key for REST API
        if self.protocol == 'rest_api' and not self.api_key:
            raise ValidationError("API key is required for REST API protocol.")
        
        # Validate health check endpoint
        if self.health_check_enabled and not self.health_check_endpoint:
            if self.protocol == 'rest_api':
                self.health_check_endpoint = f"{self.endpoint.rstrip('/')}/health"
    
    def save(self, *args, **kwargs):
        """Save with validation."""
        self.clean()
        super().save(*args, **kwargs)


class EmergencyDispatch(models.Model):
    """
    Emergency dispatch record.
    Tracks emergency dispatches to external services.
    """
    
    # Dispatch status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('dispatched', 'Dispatched'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed')
    ]
    
    # Priority levels
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Emergency information
    emergency_id = models.UUIDField(help_text="Associated emergency ID")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emergency_dispatches'
    )
    
    # Service information
    service_provider = models.ForeignKey(
        ExternalServiceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatches'
    )
    service_type = models.CharField(
        max_length=50,
        help_text="Type of service dispatched"
    )
    service_name = models.CharField(
        max_length=255,
        help_text="Name of service provider"
    )
    
    # Dispatch details
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='high',
        help_text="Dispatch priority"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Dispatch status"
    )
    
    # External service response
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="External service dispatch ID"
    )
    external_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="External service reference number"
    )
    
    # Dispatch data
    dispatch_data = models.JSONField(
        default=dict,
        help_text="Data sent to external service"
    )
    response_data = models.JSONField(
        default=dict,
        help_text="Response from external service"
    )
    
    # Timing information
    dispatched_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When dispatch was sent"
    )
    acknowledged_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When dispatch was acknowledged"
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When dispatch was completed"
    )
    
    # Performance metrics
    response_time = models.FloatField(
        blank=True,
        null=True,
        help_text="Response time in seconds"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    
    # Error information
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if failed"
    )
    error_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Error code if failed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emergency_dispatches'
        verbose_name = 'Emergency Dispatch'
        verbose_name_plural = 'Emergency Dispatches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['emergency_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['service_type', 'status']),
            models.Index(fields=['external_id']),
            models.Index(fields=['dispatched_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Dispatch {self.id} - {self.service_name} ({self.status})"
    
    def mark_dispatched(self, external_id: str = None, response_data: dict = None):
        """Mark dispatch as dispatched."""
        self.status = 'dispatched'
        self.dispatched_at = timezone.now()
        if external_id:
            self.external_id = external_id
        if response_data:
            self.response_data = response_data
        self.save()
    
    def mark_acknowledged(self):
        """Mark dispatch as acknowledged."""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.save()
    
    def mark_completed(self):
        """Mark dispatch as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message: str = None, error_code: str = None):
        """Mark dispatch as failed."""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.save()
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.save()


class ServiceHealthCheck(models.Model):
    """
    Service health check record.
    Tracks health check results for external services.
    """
    
    # Health status
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('unhealthy', 'Unhealthy'),
        ('timeout', 'Timeout'),
        ('unreachable', 'Unreachable'),
        ('error', 'Error'),
        ('unknown', 'Unknown')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Service information
    service_provider = models.ForeignKey(
        ExternalServiceProvider,
        on_delete=models.CASCADE,
        related_name='health_checks'
    )
    
    # Health check details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Health check status"
    )
    response_time = models.FloatField(
        blank=True,
        null=True,
        help_text="Response time in seconds"
    )
    status_code = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="HTTP status code"
    )
    
    # Health check data
    check_data = models.JSONField(
        default=dict,
        help_text="Health check request data"
    )
    response_data = models.JSONField(
        default=dict,
        help_text="Health check response data"
    )
    
    # Error information
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if failed"
    )
    
    # Timestamps
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_health_checks'
        verbose_name = 'Service Health Check'
        verbose_name_plural = 'Service Health Checks'
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['service_provider', 'status']),
            models.Index(fields=['checked_at']),
            models.Index(fields=['status', 'checked_at']),
        ]
    
    def __str__(self):
        return f"Health check {self.id} - {self.service_provider.name} ({self.status})"


class ServiceConfiguration(models.Model):
    """
    Service configuration template.
    Stores configuration templates for different service types.
    """
    
    # Configuration types
    CONFIG_TYPES = [
        ('default', 'Default Configuration'),
        ('custom', 'Custom Configuration'),
        ('template', 'Configuration Template')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Configuration identification
    name = models.CharField(max_length=255, help_text="Configuration name")
    config_type = models.CharField(
        max_length=20,
        choices=CONFIG_TYPES,
        default='custom',
        help_text="Configuration type"
    )
    service_type = models.CharField(
        max_length=50,
        help_text="Service type this configuration is for"
    )
    
    # Configuration data
    configuration = models.JSONField(
        default=dict,
        help_text="Configuration data"
    )
    
    # Configuration metadata
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Configuration description"
    )
    version = models.CharField(
        max_length=20,
        default='1.0.0',
        help_text="Configuration version"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether configuration is active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_configurations'
        verbose_name = 'Service Configuration'
        verbose_name_plural = 'Service Configurations'
        ordering = ['service_type', 'name']
        unique_together = ['name', 'service_type', 'version']
        indexes = [
            models.Index(fields=['service_type', 'is_active']),
            models.Index(fields=['config_type']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.service_type}) - v{self.version}"


class DispatchTemplate(models.Model):
    """
    Dispatch template for different emergency types.
    Stores templates for formatting dispatch data.
    """
    
    # Template types
    TEMPLATE_TYPES = [
        ('emergency', 'Emergency Template'),
        ('medical', 'Medical Template'),
        ('fire', 'Fire Template'),
        ('police', 'Police Template'),
        ('custom', 'Custom Template')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template identification
    name = models.CharField(max_length=255, help_text="Template name")
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        help_text="Template type"
    )
    service_type = models.CharField(
        max_length=50,
        help_text="Service type this template is for"
    )
    
    # Template content
    template_data = models.JSONField(
        default=dict,
        help_text="Template data structure"
    )
    template_format = models.TextField(
        help_text="Template format string"
    )
    
    # Template variables
    variables = models.JSONField(
        default=list,
        help_text="Available template variables"
    )
    
    # Template settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether template is active"
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Template priority (higher = more important)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dispatch_templates'
        verbose_name = 'Dispatch Template'
        verbose_name_plural = 'Dispatch Templates'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['template_type', 'service_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_type} - {self.service_type})"
    
    def render_template(self, context: dict) -> dict:
        """
        Render template with provided context.
        
        Args:
            context: Template variables
            
        Returns:
            Rendered template data
        """
        try:
            # Simple template rendering (in production, use a proper template engine)
            rendered = self.template_data.copy()
            
            # Replace variables in template data
            def replace_variables(obj):
                if isinstance(obj, dict):
                    return {k: replace_variables(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [replace_variables(item) for item in obj]
                elif isinstance(obj, str):
                    for key, value in context.items():
                        obj = obj.replace(f"{{{{{key}}}}}", str(value))
                    return obj
                else:
                    return obj
            
            return replace_variables(rendered)
            
        except Exception as e:
            # Return original template data if rendering fails
            return self.template_data
