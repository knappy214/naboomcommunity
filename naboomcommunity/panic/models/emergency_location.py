"""
Emergency Location Models
Handles GPS accuracy, location tracking, and geospatial emergency data.
"""

from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class EmergencyLocation(models.Model):
    """
    Emergency location data with GPS accuracy and geospatial indexing.
    Optimized for emergency response with PostGIS integration.
    """
    
    EMERGENCY_TYPES = [
        ('medical', 'Medical Emergency'),
        ('security', 'Security Emergency'),
        ('fire', 'Fire Emergency'),
        ('other', 'Other Emergency'),
    ]
    
    ACCURACY_LEVELS = [
        ('high', 'High Accuracy (< 50m)'),
        ('medium', 'Medium Accuracy (50-100m)'),
        ('low', 'Low Accuracy (> 100m)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_locations')
    
    # Location data with PostGIS Point field
    location = models.PointField(srid=4326, help_text="GPS coordinates as PostGIS Point")
    accuracy = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        help_text="GPS accuracy in meters"
    )
    accuracy_level = models.CharField(max_length=10, choices=ACCURACY_LEVELS, default='medium')
    
    # Emergency context
    emergency_type = models.CharField(max_length=20, choices=EMERGENCY_TYPES)
    description = models.TextField(blank=True, help_text="Emergency description")
    is_active = models.BooleanField(default=True, help_text="Whether this emergency is still active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional location metadata
    altitude = models.FloatField(null=True, blank=True, help_text="Altitude in meters")
    speed = models.FloatField(null=True, blank=True, help_text="Speed in m/s")
    heading = models.FloatField(null=True, blank=True, help_text="Heading in degrees")
    
    # Network and device info
    device_id = models.CharField(max_length=255, blank=True)
    network_type = models.CharField(max_length=50, blank=True)  # wifi, cellular, gps
    battery_level = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    class Meta:
        db_table = 'panic_emergency_location'
        verbose_name = 'Emergency Location'
        verbose_name_plural = 'Emergency Locations'
        
        # Optimized indexes for emergency queries
        indexes = [
            # Geospatial index for location queries
            models.Index(fields=['location'], name='emergency_loc_spatial_idx'),
            # User and active status for user-specific queries
            models.Index(fields=['user', 'is_active'], name='emergency_loc_user_active_idx'),
            # Emergency type and active status for filtering
            models.Index(fields=['emergency_type', 'is_active'], name='emergency_loc_type_active_idx'),
            # Timestamp for time-based queries
            models.Index(fields=['created_at'], name='emergency_loc_created_idx'),
            # Composite index for common queries
            models.Index(fields=['user', 'emergency_type', 'is_active'], name='emergency_loc_user_type_idx'),
        ]
        
        # Constraints
        constraints = [
            # Ensure accuracy is within valid range
            models.CheckConstraint(
                check=models.Q(accuracy__gte=0) & models.Q(accuracy__lte=10000),
                name='emergency_location_accuracy_range'
            ),
            # Ensure battery level is within valid range
            models.CheckConstraint(
                check=models.Q(battery_level__isnull=True) | (models.Q(battery_level__gte=0) & models.Q(battery_level__lte=100)),
                name='emergency_location_battery_range'
            ),
        ]
        
        # Ordering for efficient queries
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Emergency {self.emergency_type} at {self.location} ({self.accuracy}m accuracy)"
    
    @property
    def latitude(self):
        """Get latitude from Point field."""
        return self.location.y if self.location else None
    
    @property
    def longitude(self):
        """Get longitude from Point field."""
        return self.location.x if self.location else None
    
    def get_distance_to(self, other_location):
        """
        Calculate distance to another EmergencyLocation.
        
        Args:
            other_location: EmergencyLocation instance
            
        Returns:
            Distance in meters
        """
        if not self.location or not other_location.location:
            return None
        
        # Use PostGIS distance function
        return self.location.distance(other_location.location) * 111000  # Convert to meters
    
    def is_within_radius(self, center_point, radius_meters):
        """
        Check if this location is within a specified radius.
        
        Args:
            center_point: PostGIS Point
            radius_meters: Radius in meters
            
        Returns:
            Boolean
        """
        if not self.location or not center_point:
            return False
        
        distance = self.location.distance(center_point) * 111000
        return distance <= radius_meters
    
    def save(self, *args, **kwargs):
        """Override save to set accuracy level based on accuracy value."""
        if self.accuracy <= 50:
            self.accuracy_level = 'high'
        elif self.accuracy <= 100:
            self.accuracy_level = 'medium'
        else:
            self.accuracy_level = 'low'
        
        super().save(*args, **kwargs)


class EmergencyZone(models.Model):
    """
    Emergency zones for location-based emergency services.
    Uses PostGIS polygons for zone definitions.
    """
    
    ZONE_TYPES = [
        ('medical', 'Medical Zone'),
        ('police', 'Police Zone'),
        ('fire', 'Fire Zone'),
        ('general', 'General Emergency Zone'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    
    # PostGIS polygon for zone boundary
    boundary = models.PolygonField(srid=4326, help_text="Zone boundary as PostGIS Polygon")
    
    # Zone metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="Zone priority (1=highest)")
    
    # Contact information
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_emergency_zone'
        verbose_name = 'Emergency Zone'
        verbose_name_plural = 'Emergency Zones'
        
        indexes = [
            # Geospatial index for zone queries
            models.Index(fields=['boundary'], name='emergency_zone_spatial_idx'),
            # Zone type and active status
            models.Index(fields=['zone_type', 'is_active'], name='emergency_zone_type_active_idx'),
            # Priority for ordering
            models.Index(fields=['priority'], name='emergency_zone_priority_idx'),
        ]
        
        constraints = [
            # Ensure priority is positive
            models.CheckConstraint(
                check=models.Q(priority__gt=0),
                name='emergency_zone_priority_positive'
            ),
        ]
        
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.zone_type})"
    
    def contains_location(self, location_point):
        """
        Check if a location point is within this zone.
        
        Args:
            location_point: PostGIS Point
            
        Returns:
            Boolean
        """
        if not self.boundary or not location_point:
            return False
        
        return self.boundary.contains(location_point)
    
    def get_zone_center(self):
        """
        Get the center point of the zone.
        
        Returns:
            PostGIS Point
        """
        if not self.boundary:
            return None
        
        return self.boundary.centroid
