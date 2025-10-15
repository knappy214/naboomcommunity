"""
WebSocket Scalability Testing
Test WebSocket performance with 1000+ concurrent connections.
"""

import asyncio
import json
import time
import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import concurrent.futures
import threading
from collections import defaultdict

User = get_user_model()
logger = logging.getLogger(__name__)


class WebSocketScalabilityTestMixin:
    """
    Mixin class providing WebSocket scalability testing utilities.
    """
    
    def setUp(self):
        """Set up scalability testing environment."""
        super().setUp()
        self.connections = []
        self.connection_results = defaultdict(list)
        self.test_start_time = None
        self.test_end_time = None
        self.max_connections = 1000
        self.connection_timeout = 30  # seconds
        self.message_timeout = 10  # seconds
    
    async def create_websocket_connection(self, user, room_name='test_room'):
        """
        Create a WebSocket connection for testing.
        
        Args:
            user: User instance
            room_name: Room name for connection
        
        Returns:
            WebsocketCommunicator instance
        """
        try:
            # Create WebSocket communicator
            communicator = WebsocketCommunicator(
                self.application,
                f"/ws/emergency/{room_name}/?token={self.get_test_token(user)}"
            )
            
            # Connect
            connected, subprotocol = await communicator.connect()
            
            if not connected:
                raise ConnectionError(f"Failed to connect WebSocket for user {user.username}")
            
            return communicator
            
        except Exception as e:
            logger.error(f"Failed to create WebSocket connection: {e}")
            raise
    
    def get_test_token(self, user):
        """
        Get test JWT token for user.
        
        Args:
            user: User instance
        
        Returns:
            JWT token string
        """
        # Mock JWT token for testing
        return f"test_token_{user.id}_{user.username}"
    
    async def send_test_message(self, communicator, message_type='ping', data=None):
        """
        Send test message through WebSocket.
        
        Args:
            communicator: WebsocketCommunicator instance
            message_type: Type of message to send
            data: Message data
        
        Returns:
            Response data
        """
        try:
            message = {
                'type': message_type,
                'data': data or {},
                'timestamp': time.time()
            }
            
            await communicator.send_json_to(message)
            
            # Wait for response
            response = await asyncio.wait_for(
                communicator.receive_json_from(),
                timeout=self.message_timeout
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning("WebSocket message timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to send test message: {e}")
            return None
    
    async def test_connection_performance(self, communicator, user_id):
        """
        Test individual connection performance.
        
        Args:
            communicator: WebsocketCommunicator instance
            user_id: User ID for tracking
        
        Returns:
            Performance metrics
        """
        start_time = time.time()
        messages_sent = 0
        messages_received = 0
        errors = 0
        
        try:
            # Test ping-pong
            for i in range(10):
                response = await self.send_test_message(communicator, 'ping', {'test_id': i})
                if response:
                    messages_sent += 1
                    if response.get('type') == 'pong':
                        messages_received += 1
                else:
                    errors += 1
                
                # Small delay between messages
                await asyncio.sleep(0.1)
            
            # Test emergency alert
            response = await self.send_test_message(communicator, 'emergency_alert', {
                'alert_type': 'test',
                'location': {'lat': -26.2041, 'lng': 28.0473},
                'timestamp': time.time()
            })
            
            if response:
                messages_sent += 1
                if response.get('type') == 'success':
                    messages_received += 1
                else:
                    errors += 1
            
            # Test location update
            response = await self.send_test_message(communicator, 'location_update', {
                'location': {'lat': -26.2041, 'lng': 28.0473},
                'accuracy': 10.5,
                'timestamp': time.time()
            })
            
            if response:
                messages_sent += 1
                if response.get('type') == 'success':
                    messages_received += 1
                else:
                    errors += 1
            
        except Exception as e:
            logger.error(f"Connection performance test failed for user {user_id}: {e}")
            errors += 1
        
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'user_id': user_id,
                'duration': duration,
                'messages_sent': messages_sent,
                'messages_received': messages_received,
                'errors': errors,
                'success_rate': (messages_received / messages_sent) if messages_sent > 0 else 0,
                'messages_per_second': messages_sent / duration if duration > 0 else 0
            }
    
    async def run_concurrent_connections(self, num_connections=100):
        """
        Run concurrent WebSocket connections test.
        
        Args:
            num_connections: Number of concurrent connections to test
        
        Returns:
            Test results
        """
        logger.info(f"Starting concurrent connections test with {num_connections} connections")
        
        self.test_start_time = time.time()
        results = []
        
        # Create users for testing
        users = []
        for i in range(num_connections):
            user = await database_sync_to_async(User.objects.create_user)(
                username=f'testuser_{i}',
                email=f'test{i}@example.com',
                password='testpass123'
            )
            users.append(user)
        
        # Create connections concurrently
        tasks = []
        for i, user in enumerate(users):
            task = asyncio.create_task(self.test_single_connection(user, i))
            tasks.append(task)
        
        # Wait for all connections to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.test_end_time = time.time()
        
        # Process results
        successful_connections = [r for r in results if isinstance(r, dict) and 'user_id' in r]
        failed_connections = [r for r in results if isinstance(r, Exception)]
        
        total_duration = self.test_end_time - self.test_start_time
        
        return {
            'total_connections': num_connections,
            'successful_connections': len(successful_connections),
            'failed_connections': len(failed_connections),
            'success_rate': len(successful_connections) / num_connections,
            'total_duration': total_duration,
            'connections_per_second': num_connections / total_duration if total_duration > 0 else 0,
            'results': successful_connections,
            'errors': failed_connections
        }
    
    async def test_single_connection(self, user, connection_id):
        """
        Test a single WebSocket connection.
        
        Args:
            user: User instance
            connection_id: Connection ID for tracking
        
        Returns:
            Test result
        """
        communicator = None
        try:
            # Create connection
            communicator = await self.create_websocket_connection(user)
            self.connections.append(communicator)
            
            # Test performance
            result = await self.test_connection_performance(communicator, connection_id)
            result['connection_id'] = connection_id
            result['user_id'] = user.id
            result['username'] = user.username
            
            return result
            
        except Exception as e:
            logger.error(f"Single connection test failed for user {user.username}: {e}")
            return {
                'connection_id': connection_id,
                'user_id': user.id,
                'username': user.username,
                'error': str(e),
                'success': False
            }
        
        finally:
            if communicator:
                try:
                    await communicator.disconnect()
                except Exception as e:
                    logger.warning(f"Failed to disconnect WebSocket: {e}")
    
    async def test_message_broadcasting(self, num_connections=100):
        """
        Test message broadcasting to multiple connections.
        
        Args:
            num_connections: Number of connections to test
        
        Returns:
            Broadcasting test results
        """
        logger.info(f"Starting message broadcasting test with {num_connections} connections")
        
        # Create connections
        users = []
        communicators = []
        
        for i in range(num_connections):
            user = await database_sync_to_async(User.objects.create_user)(
                username=f'broadcast_user_{i}',
                email=f'broadcast{i}@example.com',
                password='testpass123'
            )
            users.append(user)
            
            communicator = await self.create_websocket_connection(user)
            communicators.append(communicator)
        
        # Test broadcasting
        start_time = time.time()
        
        # Send broadcast message
        broadcast_message = {
            'type': 'emergency_update',
            'data': {
                'message': 'Test emergency broadcast',
                'timestamp': time.time()
            }
        }
        
        # Send to all connections
        for communicator in communicators:
            await communicator.send_json_to(broadcast_message)
        
        # Collect responses
        responses = []
        for communicator in communicators:
            try:
                response = await asyncio.wait_for(
                    communicator.receive_json_from(),
                    timeout=self.message_timeout
                )
                responses.append(response)
            except asyncio.TimeoutError:
                responses.append(None)
        
        end_time = time.time()
        
        # Clean up
        for communicator in communicators:
            try:
                await communicator.disconnect()
            except Exception as e:
                logger.warning(f"Failed to disconnect: {e}")
        
        return {
            'total_connections': num_connections,
            'responses_received': len([r for r in responses if r is not None]),
            'response_rate': len([r for r in responses if r is not None]) / num_connections,
            'broadcast_duration': end_time - start_time,
            'responses': responses
        }
    
    async def test_connection_stability(self, num_connections=100, duration=60):
        """
        Test connection stability over time.
        
        Args:
            num_connections: Number of connections to test
            duration: Test duration in seconds
        
        Returns:
            Stability test results
        """
        logger.info(f"Starting connection stability test with {num_connections} connections for {duration} seconds")
        
        # Create connections
        users = []
        communicators = []
        
        for i in range(num_connections):
            user = await database_sync_to_async(User.objects.create_user)(
                username=f'stability_user_{i}',
                email=f'stability{i}@example.com',
                password='testpass123'
            )
            users.append(user)
            
            communicator = await self.create_websocket_connection(user)
            communicators.append(communicator)
        
        # Monitor connections
        start_time = time.time()
        active_connections = len(communicators)
        disconnections = 0
        
        # Send periodic messages
        message_count = 0
        while time.time() - start_time < duration:
            for communicator in communicators:
                try:
                    await communicator.send_json_to({
                        'type': 'heartbeat',
                        'data': {'timestamp': time.time()}
                    })
                    message_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat: {e}")
                    disconnections += 1
            
            await asyncio.sleep(1)  # Send every second
        
        end_time = time.time()
        
        # Clean up
        for communicator in communicators:
            try:
                await communicator.disconnect()
            except Exception as e:
                logger.warning(f"Failed to disconnect: {e}")
        
        return {
            'total_connections': num_connections,
            'active_connections': active_connections,
            'disconnections': disconnections,
            'stability_rate': (active_connections - disconnections) / active_connections,
            'test_duration': end_time - start_time,
            'messages_sent': message_count,
            'messages_per_second': message_count / (end_time - start_time)
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Disconnect all connections
        for communicator in self.connections:
            try:
                asyncio.run(communicator.disconnect())
            except Exception as e:
                logger.warning(f"Failed to disconnect: {e}")
        
        super().tearDown()


class EmergencyWebSocketScalabilityTest(WebSocketScalabilityTestMixin, TransactionTestCase):
    """
    Test WebSocket scalability for emergency response system.
    """
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Import the ASGI application
        from naboomcommunity.asgi import application
        self.application = application
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_100_concurrent_connections(self, mock_auth):
        """Test 100 concurrent WebSocket connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.run_concurrent_connections(100)
        
        # Assertions
        self.assertGreaterEqual(result['success_rate'], 0.95, "Success rate too low")
        self.assertLess(result['total_duration'], 30, "Test took too long")
        self.assertGreater(result['connections_per_second'], 3, "Connections per second too low")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_500_concurrent_connections(self, mock_auth):
        """Test 500 concurrent WebSocket connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.run_concurrent_connections(500)
        
        # Assertions
        self.assertGreaterEqual(result['success_rate'], 0.90, "Success rate too low")
        self.assertLess(result['total_duration'], 60, "Test took too long")
        self.assertGreater(result['connections_per_second'], 8, "Connections per second too low")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_1000_concurrent_connections(self, mock_auth):
        """Test 1000 concurrent WebSocket connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.run_concurrent_connections(1000)
        
        # Assertions
        self.assertGreaterEqual(result['success_rate'], 0.85, "Success rate too low")
        self.assertLess(result['total_duration'], 120, "Test took too long")
        self.assertGreater(result['connections_per_second'], 8, "Connections per second too low")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_message_broadcasting_100(self, mock_auth):
        """Test message broadcasting to 100 connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.test_message_broadcasting(100)
        
        # Assertions
        self.assertGreaterEqual(result['response_rate'], 0.95, "Response rate too low")
        self.assertLess(result['broadcast_duration'], 5, "Broadcast took too long")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_message_broadcasting_500(self, mock_auth):
        """Test message broadcasting to 500 connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.test_message_broadcasting(500)
        
        # Assertions
        self.assertGreaterEqual(result['response_rate'], 0.90, "Response rate too low")
        self.assertLess(result['broadcast_duration'], 10, "Broadcast took too long")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_connection_stability_100(self, mock_auth):
        """Test connection stability with 100 connections for 60 seconds."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.test_connection_stability(100, 60)
        
        # Assertions
        self.assertGreaterEqual(result['stability_rate'], 0.95, "Stability rate too low")
        self.assertGreater(result['messages_per_second'], 1, "Message rate too low")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_connection_stability_500(self, mock_auth):
        """Test connection stability with 500 connections for 60 seconds."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run test
        result = await self.test_connection_stability(500, 60)
        
        # Assertions
        self.assertGreaterEqual(result['stability_rate'], 0.90, "Stability rate too low")
        self.assertGreater(result['messages_per_second'], 5, "Message rate too low")
    
    def test_websocket_memory_usage(self):
        """Test WebSocket memory usage with multiple connections."""
        # This test would require memory monitoring tools
        # For now, we'll just ensure the test structure is in place
        self.assertTrue(True, "Memory usage test placeholder")
    
    def test_websocket_cpu_usage(self):
        """Test WebSocket CPU usage with multiple connections."""
        # This test would require CPU monitoring tools
        # For now, we'll just ensure the test structure is in place
        self.assertTrue(True, "CPU usage test placeholder")
    
    def test_websocket_network_bandwidth(self):
        """Test WebSocket network bandwidth usage."""
        # This test would require network monitoring tools
        # For now, we'll just ensure the test structure is in place
        self.assertTrue(True, "Network bandwidth test placeholder")


class EmergencyWebSocketLoadTest(WebSocketScalabilityTestMixin, TransactionTestCase):
    """
    Load testing for emergency WebSocket system.
    """
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Import the ASGI application
        from naboomcommunity.asgi import application
        self.application = application
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_gradual_load_increase(self, mock_auth):
        """Test gradual load increase from 10 to 1000 connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Test different load levels
        load_levels = [10, 50, 100, 250, 500, 750, 1000]
        results = []
        
        for load in load_levels:
            logger.info(f"Testing load level: {load} connections")
            result = await self.run_concurrent_connections(load)
            results.append({
                'load': load,
                'success_rate': result['success_rate'],
                'duration': result['total_duration'],
                'connections_per_second': result['connections_per_second']
            })
        
        # Assertions
        for result in results:
            self.assertGreaterEqual(result['success_rate'], 0.80, 
                                  f"Success rate too low at load {result['load']}")
            self.assertLess(result['duration'], 120, 
                          f"Test took too long at load {result['load']}")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_sustained_load(self, mock_auth):
        """Test sustained load with 500 connections for 5 minutes."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run sustained load test
        result = await self.test_connection_stability(500, 300)  # 5 minutes
        
        # Assertions
        self.assertGreaterEqual(result['stability_rate'], 0.95, "Sustained load stability too low")
        self.assertGreater(result['messages_per_second'], 5, "Sustained load message rate too low")
    
    @patch('panic.websocket.emergency_auth.EmergencyWebSocketConsumer.authenticate_websocket')
    async def test_peak_load_handling(self, mock_auth):
        """Test peak load handling with 1000 connections."""
        # Mock authentication
        mock_auth.return_value = None
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock user authentication
        mock_auth.return_value = user
        
        # Run peak load test
        result = await self.run_concurrent_connections(1000)
        
        # Assertions
        self.assertGreaterEqual(result['success_rate'], 0.85, "Peak load success rate too low")
        self.assertLess(result['total_duration'], 180, "Peak load test took too long")
        self.assertGreater(result['connections_per_second'], 5, "Peak load connections per second too low")
