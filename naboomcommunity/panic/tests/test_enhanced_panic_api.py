"""
Contract Tests for Enhanced Panic Button API
Tests the API contract and behavior for the enhanced panic button functionality.
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

from ..models import EmergencyLocation, EmergencyMedical, EmergencyAuditLog
from ..api.throttling import EmergencyPanicThrottle

User = get_user_model()


class EnhancedPanicButtonAPIContractTest(APITestCase):
    """
    Contract tests for the enhanced panic button API.
    Tests the API contract, request/response format, and behavior.
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
    
    def test_panic_button_activation_contract(self):
        """
        Test the contract for panic button activation.
        Should accept location data and return emergency response.
        """
        url = reverse('panic:enhanced-panic-button')
        
        # Test data matching the expected contract
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5,
                'altitude': 1500.0,
                'heading': 45.0,
                'speed': 0.0
            },
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android',
                'app_version': '1.0.0',
                'os_version': '11.0'
            },
            'context': {
                'description': 'Emergency situation requiring immediate assistance',
                'severity': 'high',
                'timestamp': timezone.now().isoformat()
            }
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Contract assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('emergency_id', response.data)
        self.assertIn('status', response.data)
        self.assertIn('timestamp', response.data)
        self.assertIn('location_processed', response.data)
        self.assertIn('medical_data_retrieved', response.data)
        self.assertIn('notifications_sent', response.data)
        
        # Verify response structure
        expected_fields = [
            'emergency_id', 'status', 'timestamp', 'location_processed',
            'medical_data_retrieved', 'notifications_sent', 'response_time_ms'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data, f"Missing field: {field}")
    
    def test_panic_button_activation_without_location(self):
        """
        Test panic button activation without location data.
        Should still work but with limited functionality.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android'
            },
            'context': {
                'description': 'Emergency without location',
                'severity': 'high'
            }
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should still succeed but with location_processed = False
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['location_processed'])
        self.assertIn('emergency_id', response.data)
    
    def test_panic_button_activation_invalid_data(self):
        """
        Test panic button activation with invalid data.
        Should return appropriate error response.
        """
        url = reverse('panic:enhanced-panic-button')
        
        # Test with missing required fields
        invalid_data = {
            'emergency_type': 'panic'
            # Missing device_info and context
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
    
    def test_panic_button_activation_unauthorized(self):
        """
        Test panic button activation without authentication.
        Should return 401 Unauthorized.
        """
        # Create new client without authentication
        unauthenticated_client = APIClient()
        
        url = reverse('panic:enhanced-panic-button')
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency'}
        }
        
        response = unauthenticated_client.post(url, panic_data, format='json')
        
        # Should return unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_panic_button_activation_rate_limited(self):
        """
        Test panic button activation rate limiting.
        Should respect rate limits for panic button activation.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency'}
        }
        
        # Make multiple requests quickly to trigger rate limiting
        responses = []
        for i in range(10):  # Exceed rate limit
            response = self.client.post(url, panic_data, format='json')
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        self.assertGreater(len(rate_limited_responses), 0, "Rate limiting not working")
    
    def test_panic_button_activation_response_time(self):
        """
        Test that panic button activation responds within acceptable time.
        Should complete within 5 seconds as per requirements.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency'}
        }
        
        start_time = time.time()
        response = self.client.post(url, panic_data, format='json')
        end_time = time.time()
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should complete within 5 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 5.0, f"Response time {response_time:.2f}s exceeds 5 second limit")
        
        # Check if response includes response time
        if 'response_time_ms' in response.data:
            self.assertLess(response.data['response_time_ms'], 5000, "Response time in data exceeds 5 seconds")
    
    def test_panic_button_activation_medical_data_integration(self):
        """
        Test that panic button activation retrieves medical data.
        Should include medical information in response.
        """
        # Create medical data for user
        medical_data = EmergencyMedical.objects.create(
            user=self.user,
            blood_type='O+',
            consent_level='full',
            emergency_contact_name='John Doe',
            emergency_contact_phone='+27123456789'
        )
        
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency with medical data'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should succeed and include medical data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['medical_data_retrieved'])
        
        # Should include medical information in response
        if 'medical_info' in response.data:
            medical_info = response.data['medical_info']
            self.assertIn('blood_type', medical_info)
            self.assertIn('emergency_contact', medical_info)
    
    def test_panic_button_activation_location_processing(self):
        """
        Test that panic button activation processes location data correctly.
        Should validate and store location information.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5,
                'altitude': 1500.0,
                'heading': 45.0,
                'speed': 0.0
            },
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency with location'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should succeed and process location
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['location_processed'])
        
        # Should create EmergencyLocation record
        emergency_locations = EmergencyLocation.objects.filter(user=self.user)
        self.assertEqual(emergency_locations.count(), 1)
        
        location = emergency_locations.first()
        self.assertEqual(location.emergency_type, 'panic')
        self.assertIsNotNone(location.location)
        self.assertEqual(location.accuracy, 10.5)
    
    def test_panic_button_activation_notification_sending(self):
        """
        Test that panic button activation sends notifications.
        Should notify emergency contacts and services.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency with notifications'}
        }
        
        with patch('panic.tasks.emergency_tasks.send_emergency_notification.delay') as mock_notification:
            response = self.client.post(url, panic_data, format='json')
            
            # Should succeed and send notifications
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['notifications_sent'])
            
            # Should call notification task
            mock_notification.assert_called_once()
    
    def test_panic_button_activation_audit_logging(self):
        """
        Test that panic button activation creates audit logs.
        Should log the emergency activation for security and compliance.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency with audit logging'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should create audit log
        audit_logs = EmergencyAuditLog.objects.filter(
            user=self.user,
            action_type='panic_activate'
        )
        self.assertEqual(audit_logs.count(), 1)
        
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.severity, 'critical')
        self.assertIn('Panic button activated', audit_log.description)
    
    def test_panic_button_activation_different_emergency_types(self):
        """
        Test panic button activation with different emergency types.
        Should handle various emergency types correctly.
        """
        url = reverse('panic:enhanced-panic-button')
        
        emergency_types = ['panic', 'medical', 'fire', 'crime', 'accident']
        
        for emergency_type in emergency_types:
            panic_data = {
                'emergency_type': emergency_type,
                'device_info': {'device_id': f'test-device-{emergency_type}'},
                'context': {'description': f'Test {emergency_type} emergency'}
            }
            
            response = self.client.post(url, panic_data, format='json')
            
            # Should succeed for all emergency types
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['status'], 'activated')
    
    def test_panic_button_activation_invalid_emergency_type(self):
        """
        Test panic button activation with invalid emergency type.
        Should return validation error.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'invalid_type',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test invalid emergency type'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('emergency_type', response.data.get('error', {}))
    
    def test_panic_button_activation_missing_device_info(self):
        """
        Test panic button activation with missing device info.
        Should return validation error.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'context': {'description': 'Test emergency without device info'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('device_info', response.data.get('error', {}))
    
    def test_panic_button_activation_missing_context(self):
        """
        Test panic button activation with missing context.
        Should return validation error.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('context', response.data.get('error', {}))
    
    def test_panic_button_activation_invalid_location_data(self):
        """
        Test panic button activation with invalid location data.
        Should handle gracefully and still process emergency.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': 'invalid_lat',  # Invalid latitude
                'longitude': 28.0473,
                'accuracy': -10.5  # Invalid accuracy
            },
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency with invalid location'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should still succeed but with location_processed = False
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['location_processed'])
    
    def test_panic_button_activation_concurrent_requests(self):
        """
        Test panic button activation with concurrent requests.
        Should handle multiple simultaneous activations correctly.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test concurrent emergency'}
        }
        
        # Make multiple concurrent requests
        responses = []
        for i in range(5):
            response = self.client.post(url, panic_data, format='json')
            responses.append(response)
        
        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should create multiple emergency locations
        emergency_locations = EmergencyLocation.objects.filter(user=self.user)
        self.assertEqual(emergency_locations.count(), 5)
    
    def test_panic_button_activation_error_handling(self):
        """
        Test panic button activation error handling.
        Should handle internal errors gracefully.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test emergency with error handling'}
        }
        
        # Mock an internal error
        with patch('panic.models.EmergencyLocation.objects.create', side_effect=Exception('Database error')):
            response = self.client.post(url, panic_data, format='json')
            
            # Should return error response
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('Internal server error', response.data['error'])


class EnhancedPanicButtonAPIIntegrationTest(TransactionTestCase):
    """
    Integration tests for the enhanced panic button API.
    Tests the full integration with external services and systems.
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
    
    def test_panic_button_activation_full_integration(self):
        """
        Test full integration of panic button activation.
        Should integrate with all systems: location, medical, notifications, audit.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Full integration test'}
        }
        
        # Mock external services
        with patch('panic.tasks.emergency_tasks.send_emergency_notification.delay') as mock_notification, \
             patch('panic.tasks.emergency_tasks.process_location_update.delay') as mock_location, \
             patch('panic.tasks.emergency_tasks.process_medical_data.delay') as mock_medical:
            
            response = self.client.post(url, panic_data, format='json')
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Should call all integration tasks
            mock_notification.assert_called_once()
            mock_location.assert_called_once()
            mock_medical.assert_called_once()
            
            # Should create emergency location
            emergency_locations = EmergencyLocation.objects.filter(user=self.user)
            self.assertEqual(emergency_locations.count(), 1)
            
            # Should create audit log
            audit_logs = EmergencyAuditLog.objects.filter(
                user=self.user,
                action_type='panic_activate'
            )
            self.assertEqual(audit_logs.count(), 1)
    
    def test_panic_button_activation_with_medical_data(self):
        """
        Test panic button activation with medical data integration.
        Should retrieve and include medical information.
        """
        # Create medical data
        medical_data = EmergencyMedical.objects.create(
            user=self.user,
            blood_type='O+',
            consent_level='full',
            emergency_contact_name='John Doe',
            emergency_contact_phone='+27123456789'
        )
        
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test with medical data'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should succeed and include medical data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['medical_data_retrieved'])
    
    def test_panic_button_activation_without_medical_data(self):
        """
        Test panic button activation without medical data.
        Should still work but with limited medical information.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Test without medical data'}
        }
        
        response = self.client.post(url, panic_data, format='json')
        
        # Should succeed but without medical data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['medical_data_retrieved'])
    
    def test_panic_button_activation_performance(self):
        """
        Test panic button activation performance.
        Should complete within acceptable time limits.
        """
        url = reverse('panic:enhanced-panic-button')
        
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {'device_id': 'test-device-123'},
            'context': {'description': 'Performance test'}
        }
        
        start_time = time.time()
        response = self.client.post(url, panic_data, format='json')
        end_time = time.time()
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should complete within 5 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 5.0, f"Response time {response_time:.2f}s exceeds 5 second limit")
        
        # Should include response time in data
        if 'response_time_ms' in response.data:
            self.assertLess(response.data['response_time_ms'], 5000, "Response time in data exceeds 5 seconds")
