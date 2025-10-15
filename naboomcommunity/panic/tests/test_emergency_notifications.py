"""
Integration Tests for Emergency Notifications
Tests notification sending and delivery for emergency response.
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
from ..tasks.emergency_tasks import send_emergency_notification, send_sms_notification, send_push_notification

User = get_user_model()


class EmergencyNotificationsIntegrationTest(APITestCase):
    """
    Integration tests for emergency notification system.
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
        
        # Create emergency location
        self.emergency_location = EmergencyLocation.objects.create(
            user=self.user,
            emergency_type='panic',
            location=None,  # Will be set in tests
            accuracy=10.5,
            device_id='test-device-123',
            description='Test emergency location'
        )
    
    def test_emergency_notification_sending(self):
        """
        Test emergency notification sending.
        Should send notifications to all configured channels.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'location': {
                'latitude': -26.2041,
                'longitude': 28.0473,
                'accuracy': 10.5
            },
            'channels': ['sms', 'email', 'push'],
            'recipients': [
                {
                    'type': 'emergency_contact',
                    'name': 'John Doe',
                    'phone': '+27123456789',
                    'email': 'john@example.com'
                },
                {
                    'type': 'family_member',
                    'name': 'Jane Doe',
                    'phone': '+27123456790',
                    'email': 'jane@example.com'
                }
            ],
            'message': 'Emergency situation requiring immediate assistance',
            'priority': 'high'
        }
        
        with patch('panic.tasks.emergency_tasks.send_emergency_notification.delay') as mock_notification:
            response = self.client.post(url, notification_data, format='json')
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('notification_id', response.data)
            self.assertIn('status', response.data)
            self.assertIn('channels_sent', response.data)
            self.assertIn('recipients_notified', response.data)
            
            # Should call notification task
            mock_notification.assert_called_once()
    
    def test_emergency_notification_sms_only(self):
        """
        Test emergency notification sending via SMS only.
        Should send SMS notifications to specified recipients.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms'],
            'recipients': [
                {
                    'type': 'emergency_contact',
                    'name': 'John Doe',
                    'phone': '+27123456789'
                }
            ],
            'message': 'Emergency situation requiring immediate assistance',
            'priority': 'high'
        }
        
        with patch('panic.tasks.emergency_tasks.send_sms_notification.delay') as mock_sms:
            response = self.client.post(url, notification_data, format='json')
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['channels_sent'], ['sms'])
            
            # Should call SMS notification task
            mock_sms.assert_called_once()
    
    def test_emergency_notification_email_only(self):
        """
        Test emergency notification sending via email only.
        Should send email notifications to specified recipients.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['email'],
            'recipients': [
                {
                    'type': 'emergency_contact',
                    'name': 'John Doe',
                    'email': 'john@example.com'
                }
            ],
            'message': 'Emergency situation requiring immediate assistance',
            'priority': 'high'
        }
        
        with patch('django.core.mail.send_mail') as mock_email:
            response = self.client.post(url, notification_data, format='json')
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['channels_sent'], ['email'])
            
            # Should call email sending
            mock_email.assert_called_once()
    
    def test_emergency_notification_push_only(self):
        """
        Test emergency notification sending via push notification only.
        Should send push notifications to specified devices.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['push'],
            'recipients': [
                {
                    'type': 'device',
                    'device_token': 'test-device-token-123',
                    'platform': 'android'
                }
            ],
            'message': 'Emergency situation requiring immediate assistance',
            'priority': 'high'
        }
        
        with patch('panic.tasks.emergency_tasks.send_push_notification.delay') as mock_push:
            response = self.client.post(url, notification_data, format='json')
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['channels_sent'], ['push'])
            
            # Should call push notification task
            mock_push.assert_called_once()
    
    def test_emergency_notification_multiple_channels(self):
        """
        Test emergency notification sending via multiple channels.
        Should send notifications via all specified channels.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms', 'email', 'push'],
            'recipients': [
                {
                    'type': 'emergency_contact',
                    'name': 'John Doe',
                    'phone': '+27123456789',
                    'email': 'john@example.com',
                    'device_token': 'test-device-token-123'
                }
            ],
            'message': 'Emergency situation requiring immediate assistance',
            'priority': 'high'
        }
        
        with patch('panic.tasks.emergency_tasks.send_sms_notification.delay') as mock_sms, \
             patch('django.core.mail.send_mail') as mock_email, \
             patch('panic.tasks.emergency_tasks.send_push_notification.delay') as mock_push:
            
            response = self.client.post(url, notification_data, format='json')
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(set(response.data['channels_sent']), {'sms', 'email', 'push'})
            
            # Should call all notification tasks
            mock_sms.assert_called_once()
            mock_email.assert_called_once()
            mock_push.assert_called_once()
    
    def test_emergency_notification_invalid_data(self):
        """
        Test emergency notification sending with invalid data.
        Should return validation error.
        """
        url = reverse('panic:send-emergency-notification')
        
        # Test with missing required fields
        invalid_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic'
            # Missing channels and recipients
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('channels', response.data.get('error', {}))
    
    def test_emergency_notification_unauthorized(self):
        """
        Test emergency notification sending without authentication.
        Should return 401 Unauthorized.
        """
        # Create new client without authentication
        unauthenticated_client = APIClient()
        
        url = reverse('panic:send-emergency-notification')
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms'],
            'recipients': [{'type': 'emergency_contact', 'name': 'John Doe', 'phone': '+27123456789'}],
            'message': 'Test emergency'
        }
        
        response = unauthenticated_client.post(url, notification_data, format='json')
        
        # Should return unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_emergency_notification_rate_limiting(self):
        """
        Test emergency notification rate limiting.
        Should respect rate limits for notification sending.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms'],
            'recipients': [{'type': 'emergency_contact', 'name': 'John Doe', 'phone': '+27123456789'}],
            'message': 'Test emergency'
        }
        
        # Make multiple requests quickly to trigger rate limiting
        responses = []
        for i in range(10):  # Exceed rate limit
            response = self.client.post(url, notification_data, format='json')
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        self.assertGreater(len(rate_limited_responses), 0, "Rate limiting not working")
    
    def test_emergency_notification_performance(self):
        """
        Test emergency notification performance.
        Should complete within acceptable time limits.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms'],
            'recipients': [{'type': 'emergency_contact', 'name': 'John Doe', 'phone': '+27123456789'}],
            'message': 'Test emergency'
        }
        
        start_time = time.time()
        response = self.client.post(url, notification_data, format='json')
        end_time = time.time()
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should complete within 3 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 3.0, f"Response time {response_time:.2f}s exceeds 3 second limit")
    
    def test_emergency_notification_audit_logging(self):
        """
        Test emergency notification audit logging.
        Should log notification sending for security and compliance.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms'],
            'recipients': [{'type': 'emergency_contact', 'name': 'John Doe', 'phone': '+27123456789'}],
            'message': 'Test emergency'
        }
        
        response = self.client.post(url, notification_data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should create audit log
        audit_logs = EmergencyAuditLog.objects.filter(
            user=self.user,
            action_type='notification_send'
        )
        self.assertEqual(audit_logs.count(), 1)
        
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.severity, 'medium')
        self.assertIn('Emergency notification sent', audit_log.description)
    
    def test_emergency_notification_error_handling(self):
        """
        Test emergency notification error handling.
        Should handle errors gracefully.
        """
        url = reverse('panic:send-emergency-notification')
        
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms'],
            'recipients': [{'type': 'emergency_contact', 'name': 'John Doe', 'phone': '+27123456789'}],
            'message': 'Test emergency'
        }
        
        # Mock an internal error
        with patch('panic.tasks.emergency_tasks.send_sms_notification.delay', side_effect=Exception('SMS service error')):
            response = self.client.post(url, notification_data, format='json')
            
            # Should return error response
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('Internal server error', response.data['error'])


class EmergencyNotificationTasksTest(TransactionTestCase):
    """
    Integration tests for emergency notification tasks.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='+27123456789'
        )
        
        # Create emergency location
        self.emergency_location = EmergencyLocation.objects.create(
            user=self.user,
            emergency_type='panic',
            location=None,
            accuracy=10.5,
            device_id='test-device-123',
            description='Test emergency location'
        )
    
    def test_send_emergency_notification_task(self):
        """
        Test send_emergency_notification task.
        Should send notifications via all configured channels.
        """
        notification_data = {
            'emergency_id': str(self.emergency_location.id),
            'emergency_type': 'panic',
            'channels': ['sms', 'email', 'push'],
            'recipients': [
                {
                    'type': 'emergency_contact',
                    'name': 'John Doe',
                    'phone': '+27123456789',
                    'email': 'john@example.com',
                    'device_token': 'test-device-token-123'
                }
            ],
            'message': 'Emergency situation requiring immediate assistance',
            'priority': 'high'
        }
        
        with patch('panic.tasks.emergency_tasks.send_sms_notification.delay') as mock_sms, \
             patch('django.core.mail.send_mail') as mock_email, \
             patch('panic.tasks.emergency_tasks.send_push_notification.delay') as mock_push:
            
            result = send_emergency_notification.delay(
                self.user.id, notification_data
            )
            
            # Should succeed
            self.assertTrue(result.successful())
            
            # Should call all notification tasks
            mock_sms.assert_called_once()
            mock_email.assert_called_once()
            mock_push.assert_called_once()
    
    def test_send_sms_notification_task(self):
        """
        Test send_sms_notification task.
        Should send SMS notifications to specified phone numbers.
        """
        phone_numbers = ['+27123456789', '+27123456790']
        message = 'Emergency situation requiring immediate assistance'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'status': 'success'}
            
            result = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            
            # Should succeed
            self.assertTrue(result.successful())
            
            # Should call SMS service
            mock_post.assert_called_once()
    
    def test_send_push_notification_task(self):
        """
        Test send_push_notification task.
        Should send push notifications to specified devices.
        """
        device_tokens = ['test-device-token-123', 'test-device-token-456']
        notification = {
            'title': 'Emergency Alert',
            'body': 'Emergency situation requiring immediate assistance',
            'data': {'emergency_type': 'panic'}
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'status': 'success'}
            
            result = send_push_notification.delay(
                self.user.id, device_tokens, notification
            )
            
            # Should succeed
            self.assertTrue(result.successful())
            
            # Should call push notification service
            mock_post.assert_called_once()
    
    def test_notification_task_error_handling(self):
        """
        Test notification task error handling.
        Should handle errors gracefully.
        """
        phone_numbers = ['+27123456789']
        message = 'Test emergency'
        
        with patch('requests.post', side_effect=Exception('SMS service error')):
            result = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            
            # Should fail gracefully
            self.assertFalse(result.successful())
            self.assertIn('error', result.result)
    
    def test_notification_task_retry_mechanism(self):
        """
        Test notification task retry mechanism.
        Should retry failed notifications.
        """
        phone_numbers = ['+27123456789']
        message = 'Test emergency'
        
        with patch('requests.post') as mock_post:
            # First call fails, second call succeeds
            mock_post.side_effect = [
                Exception('SMS service error'),
                MagicMock(status_code=200, json=lambda: {'status': 'success'})
            ]
            
            result = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            
            # Should eventually succeed after retry
            self.assertTrue(result.successful())
            
            # Should have made multiple calls
            self.assertEqual(mock_post.call_count, 2)
    
    def test_notification_task_audit_logging(self):
        """
        Test notification task audit logging.
        Should log notification sending for security and compliance.
        """
        phone_numbers = ['+27123456789']
        message = 'Test emergency'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'status': 'success'}
            
            result = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            
            # Should succeed
            self.assertTrue(result.successful())
            
            # Should create audit log
            audit_logs = EmergencyAuditLog.objects.filter(
                user=self.user,
                action_type='sms_send'
            )
            self.assertEqual(audit_logs.count(), 1)
            
            audit_log = audit_logs.first()
            self.assertEqual(audit_log.severity, 'low')
            self.assertIn('SMS notification sent', audit_log.description)
    
    def test_notification_task_performance(self):
        """
        Test notification task performance.
        Should complete within acceptable time limits.
        """
        phone_numbers = ['+27123456789']
        message = 'Test emergency'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'status': 'success'}
            
            start_time = time.time()
            result = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            end_time = time.time()
            
            # Should succeed
            self.assertTrue(result.successful())
            
            # Should complete within 2 seconds
            response_time = end_time - start_time
            self.assertLess(response_time, 2.0, f"Response time {response_time:.2f}s exceeds 2 second limit")
    
    def test_notification_task_caching(self):
        """
        Test notification task caching.
        Should cache notification data for performance.
        """
        phone_numbers = ['+27123456789']
        message = 'Test emergency'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'status': 'success'}
            
            # First call
            result1 = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            self.assertTrue(result1.successful())
            
            # Second call with same data
            result2 = send_sms_notification.delay(
                self.user.id, phone_numbers, message
            )
            self.assertTrue(result2.successful())
            
            # Should have similar response times (cached)
            # This is a basic test - in practice, you'd check cache hit rates
            self.assertEqual(result1.result['sent_count'], result2.result['sent_count'])
