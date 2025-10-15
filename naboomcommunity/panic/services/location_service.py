"""
Location Service for Emergency Response
Handles GPS accuracy validation, location processing, and geospatial operations.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from ..models import EmergencyLocation, EmergencyZone
from ..auth.emergency_permissions import EmergencyUserPermission
from ..rate_limiting.emergency_rate_limits import emergency_rate_limiter

User = get_user_model()
logger = logging.getLogger(__name__)


class LocationService:
    """
    Service for handling location-related operations in emergency response.
    Provides GPS accuracy validation, location processing, and geospatial queries.
    """
    
    # GPS accuracy thresholds
    ACCURACY_THRESHOLDS = {
        'very_high': 5.0,    # < 5 meters
        'high': 25.0,        # 5-25 meters
        'medium': 100.0,     # 25-100 meters
        'low': 500.0,        # 100-500 meters
        'very_low': 1000.0,  # 500-1000 meters
        'unacceptable': 1000.0  # > 1000 meters
    }
    
    # Coordinate validation ranges
    LATITUDE_RANGE = (-90.0, 90.0)
    LONGITUDE_RANGE = (-180.0, 180.0)
    
    # Cache settings
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_PREFIX = 'emergency_location'
    
    def __init__(self):
        self.rate_limiter = emergency_rate_limiter
    
    def validate_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Validate GPS coordinates for emergency response.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Validation result dictionary
        """
        errors = []
        
        # Validate latitude
        if not isinstance(latitude, (int, float)):
            errors.append('latitude_must_be_number')
        elif not (self.LATITUDE_RANGE[0] <= latitude <= self.LATITUDE_RANGE[1]):
            errors.append('latitude_out_of_range')
        
        # Validate longitude
        if not isinstance(longitude, (int, float)):
            errors.append('longitude_must_be_number')
        elif not (self.LONGITUDE_RANGE[0] <= longitude <= self.LONGITUDE_RANGE[1]):
            errors.append('longitude_out_of_range')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'latitude': latitude,
            'longitude': longitude
        }
    
    def validate_accuracy(self, accuracy: float) -> Dict[str, Any]:
        """
        Validate GPS accuracy for emergency response.
        
        Args:
            accuracy: GPS accuracy in meters
            
        Returns:
            Validation result dictionary
        """
        if not isinstance(accuracy, (int, float)):
            return {
                'is_valid': False,
                'level': 'invalid',
                'errors': ['accuracy_must_be_number']
            }
        
        if accuracy < 0:
            return {
                'is_valid': False,
                'level': 'invalid',
                'errors': ['accuracy_negative']
            }
        
        # Determine accuracy level
        if accuracy <= self.ACCURACY_THRESHOLDS['very_high']:
            level = 'very_high'
        elif accuracy <= self.ACCURACY_THRESHOLDS['high']:
            level = 'high'
        elif accuracy <= self.ACCURACY_THRESHOLDS['medium']:
            level = 'medium'
        elif accuracy <= self.ACCURACY_THRESHOLDS['low']:
            level = 'low'
        elif accuracy <= self.ACCURACY_THRESHOLDS['very_low']:
            level = 'very_low'
        else:
            level = 'unacceptable'
        
        # Determine if acceptable for emergency response
        is_valid = accuracy <= self.ACCURACY_THRESHOLDS['low']
        
        warnings = []
        if accuracy > self.ACCURACY_THRESHOLDS['medium']:
            warnings.append('low_accuracy_warning')
        if accuracy > self.ACCURACY_THRESHOLDS['high']:
            warnings.append('consider_alternative_location')
        
        return {
            'is_valid': is_valid,
            'level': level,
            'accuracy': accuracy,
            'warnings': warnings,
            'thresholds': self.ACCURACY_THRESHOLDS
        }
    
    def validate_location_data(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete location data for emergency response.
        
        Args:
            location_data: Dictionary containing location information
            
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        
        # Extract required fields
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        accuracy = location_data.get('accuracy')
        timestamp = location_data.get('timestamp')
        source = location_data.get('source', 'unknown')
        
        # Validate coordinates
        coord_validation = self.validate_coordinates(latitude, longitude)
        if not coord_validation['is_valid']:
            errors.extend(coord_validation['errors'])
        
        # Validate accuracy
        accuracy_validation = self.validate_accuracy(accuracy)
        if not accuracy_validation['is_valid']:
            errors.extend(accuracy_validation['errors'])
        else:
            warnings.extend(accuracy_validation['warnings'])
        
        # Validate timestamp
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    parsed_time = timezone.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    parsed_time = timestamp
                
                # Check if timestamp is in the future
                now = timezone.now()
                if parsed_time > now:
                    errors.append('timestamp_in_future')
                elif (now - parsed_time).total_seconds() > 3600:  # 1 hour old
                    warnings.append('timestamp_old')
                    
            except (ValueError, TypeError):
                errors.append('timestamp_invalid_format')
        
        # Validate source
        valid_sources = ['gps', 'network', 'passive', 'fused', 'unknown']
        if source not in valid_sources:
            warnings.append('unknown_source')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'coordinate_validation': coord_validation,
            'accuracy_validation': accuracy_validation,
            'location_data': location_data
        }
    
    def create_emergency_location(self, user: User, emergency_type: str, 
                                location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create emergency location record with validation.
        
        Args:
            user: User instance
            emergency_type: Type of emergency
            location_data: Location data dictionary
            
        Returns:
            Creation result dictionary
        """
        try:
            # Validate location data
            validation = self.validate_location_data(location_data)
            if not validation['is_valid']:
                return {
                    'success': False,
                    'error': 'Location validation failed',
                    'details': validation['errors']
                }
            
            # Extract validated data
            latitude = validation['coordinate_validation']['latitude']
            longitude = validation['coordinate_validation']['longitude']
            accuracy = validation['accuracy_validation']['accuracy']
            accuracy_level = validation['accuracy_validation']['level']
            
            # Create Point object
            point = Point(longitude, latitude, srid=4326)
            
            # Create emergency location
            with transaction.atomic():
                emergency_location = EmergencyLocation.objects.create(
                    user=user,
                    emergency_type=emergency_type,
                    location=point,
                    accuracy=accuracy,
                    accuracy_level=accuracy_level,
                    device_id=location_data.get('device_id', ''),
                    network_type=location_data.get('source', 'unknown'),
                    battery_level=location_data.get('battery_level'),
                    altitude=location_data.get('altitude'),
                    speed=location_data.get('speed'),
                    heading=location_data.get('heading'),
                    description=location_data.get('description', ''),
                    is_active=True
                )
            
            # Cache location for quick access
            cache_key = f"{self.CACHE_PREFIX}:{emergency_location.id}"
            cache.set(cache_key, {
                'id': str(emergency_location.id),
                'user_id': user.id,
                'emergency_type': emergency_type,
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': accuracy,
                'accuracy_level': accuracy_level,
                'created_at': emergency_location.created_at.isoformat()
            }, self.CACHE_TIMEOUT)
            
            logger.info(f"Created emergency location {emergency_location.id} for user {user.id}")
            
            return {
                'success': True,
                'location_id': str(emergency_location.id),
                'accuracy_level': accuracy_level,
                'warnings': validation['warnings'],
                'emergency_location': emergency_location
            }
            
        except Exception as e:
            logger.error(f"Failed to create emergency location: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create emergency location',
                'details': str(e)
            }
    
    def process_location_update(self, user: User, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process location update for emergency response.
        
        Args:
            user: User instance
            location_data: Location data dictionary
            
        Returns:
            Processing result dictionary
        """
        try:
            # Check rate limiting
            if not self.rate_limiter.check_location_update_rate(user):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded for location updates',
                    'retry_after': self.rate_limiter.get_retry_after('location_update')
                }
            
            # Validate location data
            validation = self.validate_location_data(location_data)
            if not validation['is_valid']:
                return {
                    'success': False,
                    'error': 'Location validation failed',
                    'details': validation['errors']
                }
            
            # Extract emergency type from location data or default
            emergency_type = location_data.get('emergency_type', 'panic')
            
            # Create emergency location
            result = self.create_emergency_location(user, emergency_type, location_data)
            
            if result['success']:
                # Update rate limiter
                self.rate_limiter.record_location_update(user)
                
                # Check for nearby emergency zones
                zones = self.find_nearby_emergency_zones(
                    validation['coordinate_validation']['latitude'],
                    validation['coordinate_validation']['longitude']
                )
                
                result['nearby_zones'] = zones
                
                logger.info(f"Processed location update for user {user.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process location update: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process location update',
                'details': str(e)
            }
    
    def find_nearby_emergency_zones(self, latitude: float, longitude: float, 
                                   radius_meters: float = 1000.0) -> List[Dict[str, Any]]:
        """
        Find emergency zones near a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius in meters
            
        Returns:
            List of nearby emergency zones
        """
        try:
            point = Point(longitude, latitude, srid=4326)
            radius = Distance(m=radius_meters)
            
            # Find zones that contain or are near the point
            zones = EmergencyZone.objects.filter(
                boundary__intersects=point.buffer(radius.sr / 111000)  # Convert to degrees
            ).filter(is_active=True).order_by('priority')
            
            nearby_zones = []
            for zone in zones:
                # Calculate distance to zone center
                zone_center = zone.get_zone_center()
                if zone_center:
                    distance = point.distance(zone_center) * 111000  # Convert to meters
                else:
                    distance = None
                
                nearby_zones.append({
                    'id': str(zone.id),
                    'name': zone.name,
                    'zone_type': zone.zone_type,
                    'priority': zone.priority,
                    'distance_meters': distance,
                    'contact_phone': zone.contact_phone,
                    'contact_email': zone.contact_email
                })
            
            return nearby_zones
            
        except Exception as e:
            logger.error(f"Failed to find nearby emergency zones: {str(e)}")
            return []
    
    def get_user_locations(self, user: User, limit: int = 10, 
                          active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get recent locations for a user.
        
        Args:
            user: User instance
            limit: Maximum number of locations to return
            active_only: Whether to return only active locations
            
        Returns:
            List of user locations
        """
        try:
            queryset = EmergencyLocation.objects.filter(user=user)
            
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            locations = queryset.order_by('-created_at')[:limit]
            
            location_list = []
            for location in locations:
                location_list.append({
                    'id': str(location.id),
                    'emergency_type': location.emergency_type,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'accuracy': location.accuracy,
                    'accuracy_level': location.accuracy_level,
                    'created_at': location.created_at.isoformat(),
                    'is_active': location.is_active,
                    'device_id': location.device_id,
                    'network_type': location.network_type
                })
            
            return location_list
            
        except Exception as e:
            logger.error(f"Failed to get user locations: {str(e)}")
            return []
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in meters.
        
        Args:
            lat1: First latitude
            lon1: First longitude
            lat2: Second latitude
            lon2: Second longitude
            
        Returns:
            Distance in meters
        """
        try:
            point1 = Point(lon1, lat1, srid=4326)
            point2 = Point(lon2, lat2, srid=4326)
            
            # Calculate distance and convert to meters
            distance = point1.distance(point2) * 111000
            return distance
            
        except Exception as e:
            logger.error(f"Failed to calculate distance: {str(e)}")
            return 0.0
    
    def is_location_within_radius(self, lat1: float, lon1: float, 
                                 lat2: float, lon2: float, 
                                 radius_meters: float) -> bool:
        """
        Check if one location is within radius of another.
        
        Args:
            lat1: First latitude
            lon1: First longitude
            lat2: Second latitude
            lon2: Second longitude
            radius_meters: Radius in meters
            
        Returns:
            True if within radius
        """
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        return distance <= radius_meters
    
    def get_location_statistics(self, user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get location statistics for a user.
        
        Args:
            user: User instance
            days: Number of days to analyze
            
        Returns:
            Location statistics dictionary
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            since = timezone.now() - timedelta(days=days)
            
            locations = EmergencyLocation.objects.filter(
                user=user,
                created_at__gte=since
            )
            
            total_locations = locations.count()
            active_locations = locations.filter(is_active=True).count()
            
            # Calculate average accuracy
            accuracy_values = locations.values_list('accuracy', flat=True)
            avg_accuracy = sum(accuracy_values) / len(accuracy_values) if accuracy_values else 0
            
            # Count by accuracy level
            accuracy_levels = {}
            for level in ['very_high', 'high', 'medium', 'low', 'very_low']:
                count = locations.filter(accuracy_level=level).count()
                accuracy_levels[level] = count
            
            # Count by emergency type
            emergency_types = {}
            for emergency_type in ['panic', 'medical', 'fire', 'crime', 'accident']:
                count = locations.filter(emergency_type=emergency_type).count()
                emergency_types[emergency_type] = count
            
            return {
                'total_locations': total_locations,
                'active_locations': active_locations,
                'average_accuracy': round(avg_accuracy, 2),
                'accuracy_levels': accuracy_levels,
                'emergency_types': emergency_types,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get location statistics: {str(e)}")
            return {
                'total_locations': 0,
                'active_locations': 0,
                'average_accuracy': 0,
                'accuracy_levels': {},
                'emergency_types': {},
                'period_days': days
            }