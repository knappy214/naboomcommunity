"""
Integration Tests for Location Accuracy
Tests GPS accuracy validation and location processing for emergency response.
"""

import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from django.core.cache import cache
from django.contrib.gis.geos import Point

from ..models import EmergencyLocation
from ..services.location_service import LocationService

User = get_user_model()


class LocationAccuracyIntegrationTest(APITestCase):
    """
    Integration tests for location accuracy validation and processing.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='+27123456789'
        )
        
        # Create JWT token for authentication
        self.token = AccessToken.for_user(self.user)
        
        # Set up API client with authentication
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Clear cache before each test
        cache.clear()
    
    def test_location_accuracy_validation_high_accuracy(self):
        """
        Test location accuracy validation with high accuracy GPS data.
        Should accept and process high accuracy locations.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 5.0,  # High accuracy
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['accuracy_level'], 'high')
        self.assertLess(response.data['accuracy'], 10.0)
    
    def test_location_accuracy_validation_medium_accuracy(self):
        """
        Test location accuracy validation with medium accuracy GPS data.
        Should accept and process medium accuracy locations.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 25.0,  # Medium accuracy
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['accuracy_level'], 'medium')
        self.assertLess(response.data['accuracy'], 50.0)
    
    def test_location_accuracy_validation_low_accuracy(self):
        """
        Test location accuracy validation with low accuracy GPS data.
        Should accept but flag low accuracy locations.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 100.0,  # Low accuracy
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should succeed but with warnings
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['accuracy_level'], 'low')
        self.assertGreater(response.data['accuracy'], 50.0)
        self.assertIn('warnings', response.data)
    
    def test_location_accuracy_validation_very_low_accuracy(self):
        """
        Test location accuracy validation with very low accuracy GPS data.
        Should reject very low accuracy locations.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 500.0,  # Very low accuracy
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should reject
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('error', response.data)
        self.assertIn('accuracy', response.data['error'])
    
    def test_location_accuracy_validation_network_location(self):
        """
        Test location accuracy validation with network-based location.
        Should accept network locations with appropriate accuracy level.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 200.0,  # Network accuracy
            'altitude': None,
            'heading': None,
            'speed': None,
            'timestamp': timezone.now().isoformat(),
            'source': 'network'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should succeed with network accuracy
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['accuracy_level'], 'network')
        self.assertEqual(response.data['source'], 'network')
    
    def test_location_accuracy_validation_invalid_coordinates(self):
        """
        Test location accuracy validation with invalid coordinates.
        Should reject invalid coordinate data.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': 200.0,  # Invalid latitude
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should reject
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('error', response.data)
        self.assertIn('latitude', response.data['error'])
    
    def test_location_accuracy_validation_missing_required_fields(self):
        """
        Test location accuracy validation with missing required fields.
        Should return validation error.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            # Missing longitude
            'accuracy': 10.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('longitude', response.data.get('error', {}))
    
    def test_location_accuracy_validation_negative_accuracy(self):
        """
        Test location accuracy validation with negative accuracy.
        Should reject negative accuracy values.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': -10.0,  # Negative accuracy
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should reject
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('error', response.data)
        self.assertIn('accuracy', response.data['error'])
    
    def test_location_accuracy_validation_very_high_accuracy(self):
        """
        Test location accuracy validation with very high accuracy GPS data.
        Should accept and process very high accuracy locations.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 1.0,  # Very high accuracy
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['accuracy_level'], 'very_high')
        self.assertLess(response.data['accuracy'], 5.0)
    
    def test_location_accuracy_validation_multiple_sources(self):
        """
        Test location accuracy validation with multiple location sources.
        Should handle different sources appropriately.
        """
        url = reverse('panic:location-accuracy')
        
        sources = ['gps', 'network', 'passive', 'fused']
        
        for source in sources:
            location_data = {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.0,
                'timestamp': timezone.now().isoformat(),
                'source': source
            }
            
            response = self.client.post(url, location_data, format='json')
            
            # Should succeed for all sources
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['is_valid'])
            self.assertEqual(response.data['source'], source)
    
    def test_location_accuracy_validation_historical_data(self):
        """
        Test location accuracy validation with historical location data.
        Should handle timestamps from the past.
        """
        url = reverse('panic:location-accuracy')
        
        # Location data from 1 hour ago
        past_time = timezone.now() - timezone.timedelta(hours=1)
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': past_time.isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should succeed but with warning about age
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertIn('warnings', response.data)
        self.assertIn('age', response.data['warnings'])
    
    def test_location_accuracy_validation_future_timestamp(self):
        """
        Test location accuracy validation with future timestamp.
        Should reject future timestamps.
        """
        url = reverse('panic:location-accuracy')
        
        # Location data from 1 hour in the future
        future_time = timezone.now() + timezone.timedelta(hours=1)
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': future_time.isoformat(),
            'source': 'gps'
        }
        
        response = self.client.post(url, location_data, format='json')
        
        # Should reject
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('error', response.data)
        self.assertIn('timestamp', response.data['error'])
    
    def test_location_accuracy_validation_unauthorized(self):
        """
        Test location accuracy validation without authentication.
        Should return 401 Unauthorized.
        """
        # Create new client without authentication
        unauthenticated_client = APIClient()
        
        url = reverse('panic:location-accuracy')
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        response = unauthenticated_client.post(url, location_data, format='json')
        
        # Should return unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_location_accuracy_validation_rate_limiting(self):
        """
        Test location accuracy validation rate limiting.
        Should respect rate limits for location updates.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        # Make multiple requests quickly to trigger rate limiting
        responses = []
        for i in range(20):  # Exceed rate limit
            response = self.client.post(url, location_data, format='json')
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        self.assertGreater(len(rate_limited_responses), 0, "Rate limiting not working")
    
    def test_location_accuracy_validation_performance(self):
        """
        Test location accuracy validation performance.
        Should complete within acceptable time limits.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        start_time = time.time()
        response = self.client.post(url, location_data, format='json')
        end_time = time.time()
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should complete within 1 second
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0, f"Response time {response_time:.2f}s exceeds 1 second limit")
    
    def test_location_accuracy_validation_caching(self):
        """
        Test location accuracy validation caching.
        Should cache validation results for similar locations.
        """
        url = reverse('panic:location-accuracy')
        
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'timestamp': timezone.now().isoformat(),
            'source': 'gps'
        }
        
        # First request
        response1 = self.client.post(url, location_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request with same location
        response2 = self.client.post(url, location_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Should have similar response times (cached)
        # This is a basic test - in practice, you'd check cache hit rates
        self.assertTrue(response1.data['is_valid'])
        self.assertTrue(response2.data['is_valid'])
    
    def test_location_accuracy_validation_batch_processing(self):
        """
        Test location accuracy validation with batch processing.
        Should handle multiple locations efficiently.
        """
        url = reverse('panic:location-batch-accuracy')
        
        locations = [
            {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.0,
                'timestamp': timezone.now().isoformat(),
                'source': 'gps'
            },
            {
                'latitude': -26.2042,
                'longitude': 28.0474,
                'accuracy': 15.0,
                'timestamp': timezone.now().isoformat(),
                'source': 'gps'
            },
            {
                'latitude': -26.2043,
                'longitude': 28.0475,
                'accuracy': 20.0,
                'timestamp': timezone.now().isoformat(),
                'source': 'gps'
            }
        ]
        
        batch_data = {
            'locations': locations,
            'user_id': self.user.id
        }
        
        response = self.client.post(url, batch_data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        
        # All locations should be valid
        for result in response.data['results']:
            self.assertTrue(result['is_valid'])


class LocationServiceIntegrationTest(TransactionTestCase):
    """
    Integration tests for the LocationService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='+27123456789'
        )
        
        self.location_service = LocationService()
    
    def test_location_service_accuracy_validation(self):
        """
        Test LocationService accuracy validation.
        Should validate GPS accuracy correctly.
        """
        # Test high accuracy
        result = self.location_service.validate_accuracy(5.0)
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['level'], 'high')
        
        # Test medium accuracy
        result = self.location_service.validate_accuracy(25.0)
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['level'], 'medium')
        
        # Test low accuracy
        result = self.location_service.validate_accuracy(100.0)
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['level'], 'low')
        
        # Test very low accuracy
        result = self.location_service.validate_accuracy(500.0)
        self.assertFalse(result['is_valid'])
        self.assertEqual(result['level'], 'very_low')
    
    def test_location_service_coordinate_validation(self):
        """
        Test LocationService coordinate validation.
        Should validate latitude and longitude correctly.
        """
        # Test valid coordinates
        result = self.location_service.validate_coordinates(-26.2041, 28.0473)
        self.assertTrue(result['is_valid'])
        
        # Test invalid latitude
        result = self.location_service.validate_coordinates(200.0, 28.0473)
        self.assertFalse(result['is_valid'])
        self.assertIn('latitude', result['errors'])
        
        # Test invalid longitude
        result = self.location_service.validate_coordinates(-26.2041, 200.0)
        self.assertFalse(result['is_valid'])
        self.assertIn('longitude', result['errors'])
    
    def test_location_service_emergency_location_creation(self):
        """
        Test LocationService emergency location creation.
        Should create EmergencyLocation records correctly.
        """
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'source': 'gps'
        }
        
        result = self.location_service.create_emergency_location(
            self.user, 'panic', location_data
        )
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('location_id', result)
        
        # Should create EmergencyLocation record
        emergency_location = EmergencyLocation.objects.get(id=result['location_id'])
        self.assertEqual(emergency_location.user, self.user)
        self.assertEqual(emergency_location.emergency_type, 'panic')
        self.assertEqual(emergency_location.accuracy, 10.0)
        self.assertIsNotNone(emergency_location.location)
    
    def test_location_service_location_processing(self):
        """
        Test LocationService location processing.
        Should process location data correctly.
        """
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0,
            'source': 'gps'
        }
        
        result = self.location_service.process_location_update(
            self.user, location_data
        )
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('location_id', result)
        self.assertIn('accuracy_level', result)
        self.assertEqual(result['accuracy_level'], 'high')
    
    def test_location_service_error_handling(self):
        """
        Test LocationService error handling.
        Should handle errors gracefully.
        """
        # Test with invalid data
        invalid_data = {
            'latitude': 'invalid',
            'longitude': 28.0473,
            'accuracy': 10.0
        }
        
        result = self.location_service.process_location_update(
            self.user, invalid_data
        )
        
        # Should fail gracefully
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_location_service_caching(self):
        """
        Test LocationService caching.
        Should cache location validation results.
        """
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 10.0,
            'source': 'gps'
        }
        
        # First call
        result1 = self.location_service.process_location_update(
            self.user, location_data
        )
        
        # Second call with same data
        result2 = self.location_service.process_location_update(
            self.user, location_data
        )
        
        # Both should succeed
        self.assertTrue(result1['success'])
        self.assertTrue(result2['success'])
        
        # Should have similar processing times (cached)
        # This is a basic test - in practice, you'd check cache hit rates
        self.assertEqual(result1['accuracy_level'], result2['accuracy_level'])
