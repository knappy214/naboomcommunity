"""
Location Service for Emergency Response
Handles GPS accuracy, location validation, and geospatial operations.
"""

import logging
from typing import Dict, Optional, Tuple
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.conf import settings

logger = logging.getLogger(__name__)


class LocationService:
    """
    Service for handling location-related operations in emergency response.
    """
    
    # Minimum accuracy threshold for emergency locations (in meters)
    MIN_ACCURACY_THRESHOLD = 50.0
    
    # Maximum accuracy threshold for emergency locations (in meters)
    MAX_ACCURACY_THRESHOLD = 1000.0
    
    def __init__(self):
        """Initialize the location service."""
        self.logger = logger
    
    def validate_location(self, latitude: float, longitude: float, accuracy: float) -> Dict[str, any]:
        """
        Validate location data for emergency response.
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: GPS accuracy in meters
            
        Returns:
            Dict containing validation result and processed location data
        """
        try:
            # Validate coordinate ranges
            if not (-90 <= latitude <= 90):
                return {
                    'valid': False,
                    'error': 'Invalid latitude range',
                    'code': 'INVALID_LATITUDE'
                }
            
            if not (-180 <= longitude <= 180):
                return {
                    'valid': False,
                    'error': 'Invalid longitude range',
                    'code': 'INVALID_LONGITUDE'
                }
            
            # Validate accuracy
            if accuracy < 0:
                return {
                    'valid': False,
                    'error': 'Accuracy cannot be negative',
                    'code': 'INVALID_ACCURACY'
                }
            
            if accuracy > self.MAX_ACCURACY_THRESHOLD:
                return {
                    'valid': False,
                    'error': f'Accuracy too low (>{self.MAX_ACCURACY_THRESHOLD}m)',
                    'code': 'LOW_ACCURACY'
                }
            
            # Create Point object for geospatial operations
            point = Point(longitude, latitude, srid=4326)
            
            # Determine accuracy level
            accuracy_level = self._get_accuracy_level(accuracy)
            
            return {
                'valid': True,
                'point': point,
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': accuracy,
                'accuracy_level': accuracy_level,
                'srid': 4326
            }
            
        except Exception as e:
            self.logger.error(f"Location validation error: {str(e)}")
            return {
                'valid': False,
                'error': 'Location validation failed',
                'code': 'VALIDATION_ERROR'
            }
    
    def _get_accuracy_level(self, accuracy: float) -> str:
        """
        Determine accuracy level based on GPS accuracy.
        
        Args:
            accuracy: GPS accuracy in meters
            
        Returns:
            Accuracy level string
        """
        if accuracy <= self.MIN_ACCURACY_THRESHOLD:
            return 'high'
        elif accuracy <= self.MIN_ACCURACY_THRESHOLD * 2:
            return 'medium'
        else:
            return 'low'
    
    def calculate_distance(self, point1: Point, point2: Point) -> float:
        """
        Calculate distance between two points in meters.
        
        Args:
            point1: First point
            point2: Second point
            
        Returns:
            Distance in meters
        """
        try:
            # Ensure both points have the same SRID
            if point1.srid != point2.srid:
                point2.transform(point1.srid)
            
            distance = point1.distance(point2)
            return distance * 111000  # Convert to meters (approximate)
            
        except Exception as e:
            self.logger.error(f"Distance calculation error: {str(e)}")
            return 0.0
    
    def is_within_radius(self, center_point: Point, test_point: Point, radius_meters: float) -> bool:
        """
        Check if a point is within a specified radius of another point.
        
        Args:
            center_point: Center point
            test_point: Point to test
            radius_meters: Radius in meters
            
        Returns:
            True if point is within radius
        """
        try:
            distance = self.calculate_distance(center_point, test_point)
            return distance <= radius_meters
            
        except Exception as e:
            self.logger.error(f"Radius check error: {str(e)}")
            return False
    
    def get_emergency_zone(self, point: Point, radius_meters: float = 1000) -> Dict[str, any]:
        """
        Get emergency zone information for a location.
        
        Args:
            point: Center point
            radius_meters: Zone radius in meters
            
        Returns:
            Dict containing zone information
        """
        try:
            # TODO: Implement emergency zone lookup
            # This would typically query a database of emergency zones
            
            return {
                'zone_id': 'placeholder',
                'zone_name': 'Emergency Zone',
                'radius_meters': radius_meters,
                'center_point': point,
                'services_available': ['police', 'medical', 'fire']
            }
            
        except Exception as e:
            self.logger.error(f"Emergency zone lookup error: {str(e)}")
            return {
                'zone_id': None,
                'zone_name': 'Unknown Zone',
                'radius_meters': radius_meters,
                'center_point': point,
                'services_available': []
            }
