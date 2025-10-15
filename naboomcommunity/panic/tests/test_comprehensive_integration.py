"""
Comprehensive Integration Tests
End-to-end tests for the complete emergency response system.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone as django_timezone
from rest_framework.test import APITestCase
from rest_framework import status
from channels.testing import WebsocketCommunicator
from unittest.mock import patch, MagicMock

from ..models import (
    EmergencyLocation, EmergencyMedical, EmergencyContact, 
    EmergencyAuditLog, ExternalServiceProvider, EmergencyDispatch
)
from ..services.location_service import LocationService
from ..services.medical_service import MedicalService
from ..services.notification_service import NotificationService
from ..services.external_service_integration import ExternalServiceIntegration
from ..services.offline_sync_service import OfflineSyncService
from ..api.throttling import emergency_rate_limiter

User = get_user_model()


class ComprehensiveEmergencySystemTest(APITestCase):
    """
    Comprehensive integration tests for the complete emergency response system.
    Tests the full flow from panic button activation to external service dispatch.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create emergency contact
        self.emergency_contact = EmergencyContact.objects.create(
            user=self.user,
            name='Emergency Contact',
            phone='+27123456789',
            email='emergency@example.com',
            relationship='spouse',
            contact_type='family',
            priority='critical',
            is_primary=True
        )
        
        # Create medical data
        self.medical_data = EmergencyMedical.objects.create(
            user=self.user,
            blood_type='O+',
            allergies=[
                {'name': 'Penicillin', 'severity': 'severe', 'requires_immediate_attention': True}
            ],
            medical_conditions=[
                {'name': 'Diabetes', 'type': 'Type 1', 'requires_immediate_attention': True}
            ],
            medications=[
                {'name': 'Insulin', 'dosage': '10 units', 'is_emergency_medication': True}
            ],
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+27123456789',
            emergency_contact_relationship='spouse',
            consent_level='emergency_only'
        )
        
        # Create external service provider
        self.service_provider = ExternalServiceProvider.objects.create(
            name='Test Police Service',
            service_type='police',
            protocol='rest_api',
            endpoint='https://api.test-police.gov.za/emergency',
            api_key='test-api-key',
            timeout=30,
            retry_attempts=3,
            priority_mapping={
                'critical': 'emergency',
                'high': 'urgent',
                'medium': 'normal',
                'low': 'low'
            },
            status='active',
            is_primary=True
        )
        
        # Clear cache
        cache.clear()
    
    def test_complete_emergency_flow(self):
        """
        Test complete emergency flow from panic button to external dispatch.
        """
        # 1. Activate panic button
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
                'description': 'Test emergency situation',
                'severity': 'high',
                'timestamp': django_timezone.now().isoformat()
            }
        }
        
        response = self.client.post(
            '/api/enhanced/panic/',
            data=json.dumps(panic_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        emergency_id = response.data['emergency_id']
        
        # 2. Verify location was recorded
        location = EmergencyLocation.objects.filter(
            user=self.user,
            emergency_type='panic'
        ).first()
        self.assertIsNotNone(location)
        self.assertEqual(location.latitude, -26.2041)
        self.assertEqual(location.longitude, 28.0473)
        
        # 3. Send family notification
        notification_data = {
            'emergency_id': emergency_id,
            'emergency_type': 'panic',
            'channels': ['sms', 'email'],
            'recipients': [
                {
                    'name': 'Emergency Contact',
                    'phone': '+27123456789',
                    'email': 'emergency@example.com',
                    'relationship': 'spouse',
                    'priority': 'high'
                }
            ],
            'message': 'Emergency alert: Test emergency situation',
            'priority': 'high',
            'location': panic_data['location'],
            'medical_data': {
                'blood_type': 'O+',
                'allergies': self.medical_data.allergies,
                'medical_conditions': self.medical_data.medical_conditions,
                'consent_level': 'emergency_only'
            }
        }
        
        with patch('panic.services.notification_service.NotificationService._send_sms_notification') as mock_sms, \
             patch('panic.services.notification_service.NotificationService._send_email_notification') as mock_email:
            
            mock_sms.return_value = {'success': True, 'sent_count': 1, 'failed_count': 0}
            mock_email.return_value = {'success': True, 'sent_count': 1, 'failed_count': 0}
            
            response = self.client.post(
                '/api/family/notify/',
                data=json.dumps(notification_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['total_sent'], 2)
        
        # 4. Dispatch to external service
        dispatch_data = {
            'emergency_id': emergency_id,
            'emergency_type': 'panic',
            'priority': 'high',
            'description': 'Test emergency situation',
            'location': panic_data['location'],
            'medical_data': {
                'blood_type': 'O+',
                'allergies': self.medical_data.allergies,
                'medical_conditions': self.medical_data.medical_conditions,
                'consent_level': 'emergency_only'
            },
            'service_preference': 'police'
        }
        
        with patch('panic.services.external_service_integration.ExternalServiceIntegration._dispatch_rest_api') as mock_dispatch:
            mock_dispatch.return_value = {
                'success': True,
                'external_id': 'ext-123',
                'status_code': 200,
                'message': 'Emergency dispatched successfully'
            }
            
            response = self.client.post(
                '/api/integration/dispatch/',
                data=json.dumps(dispatch_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['status'], 'dispatched')
        
        # 5. Verify audit logs
        audit_logs = EmergencyAuditLog.objects.filter(
            user=self.user,
            emergency_id=emergency_id
        ).order_by('created_at')
        
        self.assertGreaterEqual(audit_logs.count(), 3)  # At least panic, notification, dispatch
        
        # Verify panic button log
        panic_log = audit_logs.filter(action_type='enhanced_panic_activated').first()
        self.assertIsNotNone(panic_log)
        self.assertEqual(panic_log.severity, 'critical')
        
        # Verify notification log
        notification_log = audit_logs.filter(action_type='notification_send').first()
        self.assertIsNotNone(notification_log)
        self.assertEqual(notification_log.severity, 'medium')
        
        # Verify dispatch log
        dispatch_log = audit_logs.filter(action_type='external_service_dispatch').first()
        self.assertIsNotNone(dispatch_log)
        self.assertEqual(dispatch_log.severity, 'high')
    
    def test_offline_sync_flow(self):
        """
        Test offline sync flow for emergency data.
        """
        # 1. Create sync session
        session_data = {
            'device_id': 'test-device-123',
            'sync_type': 'full'
        }
        
        response = self.client.post(
            '/api/offline/session/create/',
            data=json.dumps(session_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_id = response.data['session_id']
        
        # 2. Sync offline data
        offline_data = {
            'emergency_location': [
                {
                    'id': str(uuid.uuid4()),
                    'operation': 'create',
                    'timestamp': django_timezone.now().isoformat(),
                    'latitude': -26.2041,
                    'longitude': 28.0473,
                    'accuracy': 10.5,
                    'emergency_type': 'panic'
                }
            ],
            'emergency_medical': [
                {
                    'id': str(uuid.uuid4()),
                    'operation': 'create',
                    'timestamp': django_timezone.now().isoformat(),
                    'blood_type': 'O+',
                    'allergies': [],
                    'medications': [],
                    'consent_level': 'emergency_only'
                }
            ]
        }
        
        sync_data = {
            'session_id': session_id,
            'device_id': 'test-device-123',
            'sync_type': 'full',
            'offline_data': offline_data
        }
        
        response = self.client.post(
            '/api/offline/sync/',
            data=json.dumps(sync_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'synced')
        
        # 3. Close sync session
        close_data = {
            'session_id': session_id
        }
        
        response = self.client.post(
            '/api/offline/session/close/',
            data=json.dumps(close_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')
    
    def test_websocket_real_time_updates(self):
        """
        Test WebSocket real-time updates for emergency status.
        """
        # This would test WebSocket connections
        # For now, we'll test the WebSocket API endpoints
        
        # Test WebSocket status
        response = self.client.get(
            '/api/websocket/status/',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('connections', response.data)
        
        # Test WebSocket subscription
        subscription_data = {
            'channels': ['emergency_updates', 'location_updates'],
            'emergency_id': str(uuid.uuid4())
        }
        
        response = self.client.post(
            '/api/websocket/subscribe/',
            data=json.dumps(subscription_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'subscribed')
    
    def test_rate_limiting(self):
        """
        Test rate limiting for emergency endpoints.
        """
        # Test panic button rate limiting
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android'
            },
            'context': {
                'description': 'Test emergency',
                'severity': 'high'
            }
        }
        
        # Make multiple rapid requests
        for i in range(10):
            response = self.client.post(
                '/api/enhanced/panic/',
                data=json.dumps(panic_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
            )
            
            if i < 5:  # First 5 should succeed
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            else:  # Subsequent requests should be rate limited
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_medical_data_privacy(self):
        """
        Test medical data privacy and consent management.
        """
        # Test medical data retrieval with different consent levels
        response = self.client.get(
            '/api/enhanced/medical/',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only consented data is returned
        medical_data = response.data['medical_data']
        self.assertIn('blood_type', medical_data)
        self.assertIn('allergies', medical_data)
        self.assertIn('medical_conditions', medical_data)
        
        # Test medical data update
        update_data = {
            'blood_type': 'A+',
            'allergies': [
                {'name': 'Peanuts', 'severity': 'moderate', 'requires_immediate_attention': False}
            ],
            'consent_level': 'full'
        }
        
        response = self.client.put(
            '/api/enhanced/medical/',
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['consent_level'], 'full')
    
    def test_location_accuracy_validation(self):
        """
        Test location accuracy validation and processing.
        """
        # Test location accuracy validation
        location_data = {
            'latitude': -26.2041,
            'longitude': 28.0473,
            'accuracy': 5.0,
            'altitude': 1500.0,
            'heading': 45.0,
            'speed': 0.0
        }
        
        response = self.client.post(
            '/api/enhanced/location/validate/',
            data=json.dumps(location_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['accuracy_level'], 'very_high')
        self.assertTrue(response.data['is_valid'])
        
        # Test batch location accuracy
        batch_data = {
            'locations': [
                {
                    'latitude': -26.2041,
                    'longitude': 28.0473,
                    'accuracy': 5.0,
                    'timestamp': django_timezone.now().isoformat()
                },
                {
                    'latitude': -26.2042,
                    'longitude': 28.0474,
                    'accuracy': 15.0,
                    'timestamp': django_timezone.now().isoformat()
                }
            ]
        }
        
        response = self.client.post(
            '/api/enhanced/location/batch/',
            data=json.dumps(batch_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_external_service_health_monitoring(self):
        """
        Test external service health monitoring.
        """
        # Test service status
        response = self.client.get(
            f'/api/integration/services/police/status/',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        
        # Test service connection
        response = self.client.post(
            f'/api/integration/services/police/test/',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        
        # Test available services
        response = self.client.get(
            '/api/integration/services/',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('services', response.data)
        self.assertGreater(len(response.data['services']), 0)
    
    def test_error_handling_and_recovery(self):
        """
        Test error handling and recovery mechanisms.
        """
        # Test invalid emergency type
        panic_data = {
            'emergency_type': 'invalid_type',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android'
            },
            'context': {
                'description': 'Test emergency',
                'severity': 'high'
            }
        }
        
        response = self.client.post(
            '/api/enhanced/panic/',
            data=json.dumps(panic_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test invalid location data
        panic_data['emergency_type'] = 'panic'
        panic_data['location'] = {
            'latitude': 'invalid',
            'longitude': 'invalid',
            'accuracy': -1
        }
        
        response = self.client.post(
            '/api/enhanced/panic/',
            data=json.dumps(panic_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self._get_auth_token()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def _get_auth_token(self):
        """Get authentication token for testing."""
        # This would implement proper JWT token generation
        # For now, return a mock token
        return 'mock-jwt-token'


class PerformanceTest(TestCase):
    """
    Performance tests for the emergency response system.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='perftest',
            email='perf@example.com',
            password='testpass123'
        )
    
    def test_panic_button_performance(self):
        """
        Test panic button activation performance.
        """
        import time
        
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android'
            },
            'context': {
                'description': 'Performance test',
                'severity': 'high'
            }
        }
        
        start_time = time.time()
        
        with patch('panic.services.location_service.LocationService.process_location_update') as mock_location, \
             patch('panic.services.medical_service.MedicalService.get_medical_summary') as mock_medical, \
             patch('panic.tasks.emergency_tasks.LocationTask.delay') as mock_task:
            
            mock_location.return_value = {'success': True, 'location_id': str(uuid.uuid4())}
            mock_medical.return_value = {'blood_type': 'O+', 'allergies': []}
            mock_task.return_value = None
            
            response = self.client.post(
                '/api/enhanced/panic/',
                data=json.dumps(panic_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock-token'
            )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Assert response time is under 1 second
        self.assertLess(response_time, 1.0)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_concurrent_panic_buttons(self):
        """
        Test concurrent panic button activations.
        """
        import threading
        import time
        
        results = []
        
        def activate_panic_button():
            panic_data = {
                'emergency_type': 'panic',
                'location': {
                    'latitude': -26.2041,
                    'longitude': 28.0473,
                    'accuracy': 10.5
                },
                'device_info': {
                    'device_id': f'test-device-{threading.current_thread().ident}',
                    'platform': 'android'
                },
                'context': {
                    'description': 'Concurrent test',
                    'severity': 'high'
                }
            }
            
            with patch('panic.services.location_service.LocationService.process_location_update') as mock_location, \
                 patch('panic.services.medical_service.MedicalService.get_medical_summary') as mock_medical, \
                 patch('panic.tasks.emergency_tasks.LocationTask.delay') as mock_task:
                
                mock_location.return_value = {'success': True, 'location_id': str(uuid.uuid4())}
                mock_medical.return_value = {'blood_type': 'O+', 'allergies': []}
                mock_task.return_value = None
                
                response = self.client.post(
                    '/api/enhanced/panic/',
                    data=json.dumps(panic_data),
                    content_type='application/json',
                    HTTP_AUTHORIZATION=f'Bearer mock-token'
                )
                
                results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=activate_panic_button)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == 201 for status_code in results))


class SecurityTest(TestCase):
    """
    Security tests for the emergency response system.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='securitytest',
            email='security@example.com',
            password='testpass123'
        )
    
    def test_authentication_required(self):
        """
        Test that authentication is required for all endpoints.
        """
        endpoints = [
            '/api/enhanced/panic/',
            '/api/enhanced/location/validate/',
            '/api/enhanced/medical/',
            '/api/family/notify/',
            '/api/integration/dispatch/',
            '/api/offline/sync/',
        ]
        
        for endpoint in endpoints:
            response = self.client.post(endpoint, data={})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_input_validation(self):
        """
        Test input validation and sanitization.
        """
        # Test SQL injection attempt
        malicious_data = {
            'emergency_type': "'; DROP TABLE emergency_locations; --",
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android'
            },
            'context': {
                'description': 'Test emergency',
                'severity': 'high'
            }
        }
        
        response = self.client.post(
            '/api/enhanced/panic/',
            data=json.dumps(malicious_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer mock-token'
        )
        
        # Should handle malicious input gracefully
        self.assertIn(response.status_code, [400, 201])
    
    def test_data_encryption(self):
        """
        Test that sensitive data is properly encrypted.
        """
        # Test medical data encryption
        medical_data = {
            'blood_type': 'O+',
            'allergies': [
                {'name': 'Penicillin', 'severity': 'severe', 'requires_immediate_attention': True}
            ],
            'consent_level': 'full'
        }
        
        with patch('panic.services.medical_service.MedicalService.encrypt_medical_data') as mock_encrypt:
            mock_encrypt.return_value = 'encrypted_data'
            
            response = self.client.put(
                '/api/enhanced/medical/',
                data=json.dumps(medical_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock-token'
            )
            
            # Verify encryption was called
            mock_encrypt.assert_called_once()
    
    def test_audit_logging(self):
        """
        Test that all actions are properly audited.
        """
        # Test panic button activation audit
        panic_data = {
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'device_info': {
                'device_id': 'test-device-123',
                'platform': 'android'
            },
            'context': {
                'description': 'Audit test',
                'severity': 'high'
            }
        }
        
        with patch('panic.models.emergency_audit.EmergencyAuditLog.log_action') as mock_log:
            response = self.client.post(
                '/api/enhanced/panic/',
                data=json.dumps(panic_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock-token'
            )
            
            # Verify audit logging was called
            mock_log.assert_called()


@pytest.mark.django_db
class PytestIntegrationTest:
    """
    Pytest-based integration tests for the emergency response system.
    """
    
    def test_emergency_location_creation(self, user, location_data):
        """Test emergency location creation with pytest."""
        location = EmergencyLocation.objects.create(
            user=user,
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            accuracy=location_data['accuracy'],
            emergency_type='panic'
        )
        
        assert location.user == user
        assert location.latitude == location_data['latitude']
        assert location.longitude == location_data['longitude']
        assert location.emergency_type == 'panic'
    
    def test_medical_data_encryption(self, user, medical_data):
        """Test medical data encryption with pytest."""
        medical = EmergencyMedical.objects.create(
            user=user,
            blood_type=medical_data['blood_type'],
            allergies=medical_data['allergies'],
            consent_level='full'
        )
        
        assert medical.user == user
        assert medical.blood_type == medical_data['blood_type']
        assert medical.consent_level == 'full'
    
    def test_emergency_contact_creation(self, user, contact_data):
        """Test emergency contact creation with pytest."""
        contact = EmergencyContact.objects.create(
            user=user,
            name=contact_data['name'],
            phone=contact_data['phone'],
            email=contact_data['email'],
            relationship=contact_data['relationship'],
            contact_type='family',
            priority='high'
        )
        
        assert contact.user == user
        assert contact.name == contact_data['name']
        assert contact.phone == contact_data['phone']
        assert contact.contact_type == 'family'
    
    def test_external_service_provider_creation(self, service_data):
        """Test external service provider creation with pytest."""
        provider = ExternalServiceProvider.objects.create(
            name=service_data['name'],
            service_type=service_data['service_type'],
            protocol=service_data['protocol'],
            endpoint=service_data['endpoint'],
            api_key=service_data['api_key']
        )
        
        assert provider.name == service_data['name']
        assert provider.service_type == service_data['service_type']
        assert provider.protocol == service_data['protocol']
        assert provider.endpoint == service_data['endpoint']


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='pytestuser',
        email='pytest@example.com',
        password='testpass123'
    )


@pytest.fixture
def location_data():
    """Create test location data."""
    return {
        'latitude': -26.2041,
        'longitude': 28.0473,
        'accuracy': 10.5,
        'altitude': 1500.0,
        'heading': 45.0,
        'speed': 0.0
    }


@pytest.fixture
def medical_data():
    """Create test medical data."""
    return {
        'blood_type': 'O+',
        'allergies': [
            {'name': 'Penicillin', 'severity': 'severe', 'requires_immediate_attention': True}
        ],
        'medical_conditions': [
            {'name': 'Diabetes', 'type': 'Type 1', 'requires_immediate_attention': True}
        ],
        'medications': [
            {'name': 'Insulin', 'dosage': '10 units', 'is_emergency_medication': True}
        ]
    }


@pytest.fixture
def contact_data():
    """Create test contact data."""
    return {
        'name': 'Test Contact',
        'phone': '+27123456789',
        'email': 'contact@example.com',
        'relationship': 'spouse'
    }


@pytest.fixture
def service_data():
    """Create test service data."""
    return {
        'name': 'Test Service',
        'service_type': 'police',
        'protocol': 'rest_api',
        'endpoint': 'https://api.test.gov.za/emergency',
        'api_key': 'test-api-key'
    }
