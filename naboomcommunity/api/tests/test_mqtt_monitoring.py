"""
Tests for MQTT Monitoring and Health Check System

This module contains comprehensive tests for the MQTT health monitoring,
metrics collection, and admin integration functionality.
"""

import json
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User

from .mqtt_health import MQTTHealthView, MQTTMetricsView, health_tracker, MQTTHealthMetrics
from .mqtt_admin import MQTTServiceAdmin


class MQTTHealthTrackerTestCase(TestCase):
    """Test cases for MQTT health tracker functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Clear cache before each test
        cache.clear()
        
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
    
    def test_health_tracker_singleton(self):
        """Test that health tracker is a singleton."""
        from .mqtt_health import MQTTHealthTracker
        
        tracker1 = MQTTHealthTracker()
        tracker2 = MQTTHealthTracker()
        
        self.assertIs(tracker1, tracker2)
    
    def test_connection_status_update(self):
        """Test connection status updates."""
        health_tracker.update_connection_status(True)
        metrics = health_tracker.get_health_metrics()
        self.assertTrue(metrics.connected)
        
        health_tracker.update_connection_status(False)
        metrics = health_tracker.get_health_metrics()
        self.assertFalse(metrics.connected)
    
    def test_message_count_increment(self):
        """Test message count incrementing."""
        initial_count = health_tracker.message_count
        
        health_tracker.increment_message_count()
        health_tracker.increment_message_count()
        
        metrics = health_tracker.get_health_metrics()
        self.assertEqual(metrics.messages_processed, initial_count + 2)
    
    def test_error_recording(self):
        """Test error recording functionality."""
        error_message = "Test error message"
        
        health_tracker.record_error(error_message)
        metrics = health_tracker.get_health_metrics()
        
        self.assertEqual(metrics.error_count, 1)
        self.assertEqual(metrics.last_error, error_message)
    
    def test_subscribed_topics_update(self):
        """Test subscribed topics update."""
        topics = ["topic1", "topic2", "topic3"]
        
        health_tracker.update_subscribed_topics(topics)
        metrics = health_tracker.get_health_metrics()
        
        self.assertEqual(metrics.subscribed_topics, topics)
    
    def test_uptime_calculation(self):
        """Test uptime calculation."""
        # Wait a small amount to ensure uptime > 0
        time.sleep(0.1)
        
        uptime = health_tracker.get_uptime()
        self.assertGreater(uptime, 0)
    
    def test_messages_per_minute_calculation(self):
        """Test messages per minute calculation."""
        # Reset message count
        health_tracker.message_count = 0
        health_tracker.start_time = time.time() - 60  # 1 minute ago
        
        # Add some messages
        for _ in range(10):
            health_tracker.increment_message_count()
        
        messages_per_minute = health_tracker.get_messages_per_minute()
        self.assertAlmostEqual(messages_per_minute, 10.0, delta=1.0)
    
    def test_metrics_caching(self):
        """Test metrics caching functionality."""
        # Update some metrics
        health_tracker.update_connection_status(True)
        health_tracker.increment_message_count()
        
        # Get cached metrics
        cached_metrics = health_tracker.get_cached_metrics()
        self.assertIsNotNone(cached_metrics)
        self.assertTrue(cached_metrics['connected'])
        self.assertEqual(cached_metrics['messages_processed'], 1)


class MQTTHealthViewTestCase(TestCase):
    """Test cases for MQTT health check API view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
    
    def test_health_endpoint_accessible(self):
        """Test that health endpoint is accessible."""
        response = self.client.get('/api/mqtt/health/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_response_structure(self):
        """Test health response structure."""
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        # Check required fields
        required_fields = [
            'status', 'timestamp', 'service', 'version', 'connected',
            'uptime_seconds', 'uptime_human', 'metrics', 'connection',
            'subscriptions', 'activity'
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
    
    def test_health_status_healthy(self):
        """Test health status when service is healthy."""
        # Set up healthy state
        health_tracker.update_connection_status(True)
        health_tracker.increment_message_count()
        
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['connected'])
        self.assertEqual(response.status_code, 200)
    
    def test_health_status_unhealthy(self):
        """Test health status when service is unhealthy."""
        # Set up unhealthy state
        health_tracker.update_connection_status(False)
        
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        self.assertEqual(data['status'], 'unhealthy')
        self.assertFalse(data['connected'])
        self.assertEqual(response.status_code, 503)
    
    def test_health_status_degraded(self):
        """Test health status when service is degraded."""
        # Set up degraded state (high error count)
        health_tracker.update_connection_status(True)
        for _ in range(15):  # More than 10 errors
            health_tracker.record_error("Test error")
        
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(response.status_code, 200)
    
    def test_health_metrics_included(self):
        """Test that health metrics are included in response."""
        health_tracker.update_connection_status(True)
        health_tracker.increment_message_count()
        health_tracker.record_error("Test error")
        
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        metrics = data['metrics']
        self.assertIn('messages_processed', metrics)
        self.assertIn('messages_per_minute', metrics)
        self.assertIn('connection_retries', metrics)
        self.assertIn('error_count', metrics)
        self.assertIn('last_error', metrics)
    
    def test_health_connection_details(self):
        """Test that connection details are included."""
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        connection = data['connection']
        self.assertIn('broker_host', connection)
        self.assertIn('broker_port', connection)
        self.assertIn('client_id', connection)
        self.assertIn('keepalive', connection)
    
    def test_health_subscriptions_info(self):
        """Test that subscription information is included."""
        topics = ["topic1", "topic2"]
        health_tracker.update_subscribed_topics(topics)
        
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        
        subscriptions = data['subscriptions']
        self.assertEqual(subscriptions['topics'], topics)
        self.assertEqual(subscriptions['count'], len(topics))


class MQTTMetricsViewTestCase(TestCase):
    """Test cases for MQTT metrics API view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
    
    def test_metrics_endpoint_accessible(self):
        """Test that metrics endpoint is accessible."""
        response = self.client.get('/api/mqtt/metrics/')
        self.assertEqual(response.status_code, 200)
    
    def test_metrics_response_structure(self):
        """Test metrics response structure."""
        response = self.client.get('/api/mqtt/metrics/')
        data = response.json()
        
        # Check required fields
        required_fields = [
            'timestamp', 'service', 'uptime', 'performance',
            'reliability', 'connection', 'subscriptions', 'activity'
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
    
    def test_metrics_performance_data(self):
        """Test performance metrics data."""
        # Set up some metrics
        health_tracker.update_connection_status(True)
        for _ in range(5):
            health_tracker.increment_message_count()
        
        response = self.client.get('/api/mqtt/metrics/')
        data = response.json()
        
        performance = data['performance']
        self.assertIn('messages_processed', performance)
        self.assertIn('messages_per_minute', performance)
        self.assertIn('messages_per_hour', performance)
        self.assertEqual(performance['messages_processed'], 5)
    
    def test_metrics_reliability_data(self):
        """Test reliability metrics data."""
        # Set up some errors
        health_tracker.record_error("Test error 1")
        health_tracker.record_error("Test error 2")
        health_tracker.increment_connection_retries()
        
        response = self.client.get('/api/mqtt/metrics/')
        data = response.json()
        
        reliability = data['reliability']
        self.assertIn('connection_retries', reliability)
        self.assertIn('error_count', reliability)
        self.assertIn('error_rate_percent', reliability)
        self.assertIn('last_error', reliability)
        self.assertEqual(reliability['error_count'], 2)
        self.assertEqual(reliability['connection_retries'], 1)
    
    def test_metrics_uptime_formatting(self):
        """Test uptime formatting in metrics."""
        response = self.client.get('/api/mqtt/metrics/')
        data = response.json()
        
        uptime = data['uptime']
        self.assertIn('seconds', uptime)
        self.assertIn('hours', uptime)
        self.assertIn('human', uptime)
        self.assertGreater(uptime['seconds'], 0)


class MQTTAdminTestCase(TestCase):
    """Test cases for MQTT admin integration."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = MQTTServiceAdmin(None, self.site)
        
        # Create a superuser for admin tests
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
    
    def test_admin_list_display(self):
        """Test admin list display methods."""
        # Test status badge
        status_badge = self.admin.get_status_badge(None)
        self.assertIn('span', status_badge)
        
        # Test connection status
        connection_status = self.admin.get_connection_status(None)
        self.assertIn('span', connection_status)
        
        # Test uptime
        uptime = self.admin.get_uptime(None)
        self.assertIsInstance(uptime, str)
        
        # Test messages processed
        messages = self.admin.get_messages_processed(None)
        self.assertIsInstance(messages, str)
    
    def test_admin_health_status_determination(self):
        """Test health status determination in admin."""
        # Test healthy status
        metrics = MQTTHealthMetrics(
            connected=True,
            uptime=3600,
            messages_processed=100,
            messages_per_minute=1.0,
            subscribed_topics=["topic1"],
            last_activity=datetime.now(timezone.utc),
            connection_retries=0,
            error_count=0,
            last_error=None,
            broker_host="localhost",
            broker_port=1883,
            client_id="test",
            keepalive=60
        )
        
        status = self.admin._determine_health_status(metrics)
        self.assertEqual(status, 'healthy')
        
        # Test unhealthy status
        metrics.connected = False
        status = self.admin._determine_health_status(metrics)
        self.assertEqual(status, 'unhealthy')
        
        # Test degraded status
        metrics.connected = True
        metrics.error_count = 15
        status = self.admin._determine_health_status(metrics)
        self.assertEqual(status, 'degraded')
    
    def test_admin_uptime_formatting(self):
        """Test uptime formatting in admin."""
        # Test seconds
        uptime = self.admin._format_uptime(30)
        self.assertIn('30s', uptime)
        
        # Test minutes
        uptime = self.admin._format_uptime(90)
        self.assertIn('1m', uptime)
        
        # Test hours
        uptime = self.admin._format_uptime(3660)
        self.assertIn('1h', uptime)
    
    def test_admin_time_since_activity(self):
        """Test time since activity formatting."""
        # Test recent activity
        recent_time = datetime.now(timezone.utc)
        time_since = self.admin._get_time_since_activity(recent_time)
        self.assertIn('s ago', time_since)
        
        # Test no activity
        time_since = self.admin._get_time_since_activity(None)
        self.assertEqual(time_since, 'Never')


class MQTTIntegrationTestCase(TestCase):
    """Integration tests for MQTT monitoring system."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
    
    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        # 1. Check initial health (should be unhealthy - not connected)
        response = self.client.get('/api/mqtt/health/')
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data['status'], 'unhealthy')
        
        # 2. Simulate service startup
        health_tracker.update_connection_status(True)
        health_tracker.update_subscribed_topics(["test/topic"])
        
        # 3. Check health after startup
        response = self.client.get('/api/mqtt/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['connected'])
        
        # 4. Simulate message processing
        for _ in range(10):
            health_tracker.increment_message_count()
        
        # 5. Check metrics
        response = self.client.get('/api/mqtt/metrics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['performance']['messages_processed'], 10)
        
        # 6. Simulate errors
        health_tracker.record_error("Test error")
        
        # 7. Check health with errors
        response = self.client.get('/api/mqtt/health/')
        data = response.json()
        self.assertEqual(data['metrics']['error_count'], 1)
        self.assertEqual(data['metrics']['last_error'], "Test error")
        
        # 8. Simulate disconnection
        health_tracker.update_connection_status(False)
        
        # 9. Check health after disconnection
        response = self.client.get('/api/mqtt/health/')
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data['status'], 'unhealthy')
        self.assertFalse(data['connected'])
    
    def test_error_handling(self):
        """Test error handling in health endpoints."""
        # Test with corrupted cache
        cache.set('mqtt_health_metrics', 'invalid_json', timeout=300)
        
        response = self.client.get('/api/mqtt/health/')
        self.assertEqual(response.status_code, 200)  # Should still work
        
        # Test with None cache
        cache.delete('mqtt_health_metrics')
        
        response = self.client.get('/api/mqtt/health/')
        self.assertEqual(response.status_code, 200)  # Should still work
    
    def test_concurrent_access(self):
        """Test concurrent access to health tracker."""
        import threading
        import time
        
        results = []
        
        def update_metrics():
            for _ in range(10):
                health_tracker.increment_message_count()
                time.sleep(0.01)
            results.append(health_tracker.get_health_metrics().messages_processed)
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=update_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all threads got consistent results
        self.assertEqual(len(set(results)), 1)  # All should be the same
        self.assertEqual(results[0], 30)  # 3 threads * 10 messages each
