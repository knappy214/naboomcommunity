"""
Emergency WebSocket Consumers
Real-time WebSocket consumers for emergency response status updates.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone as django_timezone

from ..models import EmergencyLocation, EmergencyMedical, EmergencyAuditLog
from ..services.location_service import LocationService
from ..services.medical_service import MedicalService

User = get_user_model()
logger = logging.getLogger(__name__)


class EmergencyConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for emergency response real-time updates.
    Handles emergency status updates, location tracking, and notifications.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            # Extract room name from URL
            self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'general')
            self.room_group_name = f'emergency_{self.room_name}'
            
            # Get user from scope
            self.user = self.scope.get('user')
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Accept connection
            await self.accept()
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to emergency updates',
                'room': self.room_name,
                'timestamp': django_timezone.now().isoformat()
            }))
            
            # Log connection
            await self.log_connection('connected')
            
            logger.info(f"Emergency WebSocket connected: User {self.user.id}, Room {self.room_name}")
            
        except Exception as e:
            logger.error(f"Emergency WebSocket connection failed: {str(e)}")
            await self.close(code=4000)  # Internal error
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Log disconnection
            await self.log_connection('disconnected', close_code)
            
            logger.info(f"Emergency WebSocket disconnected: User {self.user.id}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Emergency WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                # Route message based on type
                if message_type == 'ping':
                    await self.handle_ping(data)
                elif message_type == 'subscribe_emergency':
                    await self.handle_subscribe_emergency(data)
                elif message_type == 'unsubscribe_emergency':
                    await self.handle_unsubscribe_emergency(data)
                elif message_type == 'request_status':
                    await self.handle_request_status(data)
                elif message_type == 'update_location':
                    await self.handle_update_location(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
            elif bytes_data:
                await self.send_error('binary_not_supported', 'Binary data not supported')
                
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Emergency WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_ping(self, data):
        """Handle ping message."""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def handle_subscribe_emergency(self, data):
        """Handle emergency subscription."""
        emergency_id = data.get('emergency_id')
        if not emergency_id:
            await self.send_error('missing_emergency_id', 'Emergency ID is required')
            return
        
        # Add to emergency-specific group
        emergency_group = f'emergency_{emergency_id}'
        await self.channel_layer.group_add(
            emergency_group,
            self.channel_name
        )
        
        # Store subscription
        await self.store_subscription(emergency_id)
        
        await self.send(text_data=json.dumps({
            'type': 'subscribed',
            'emergency_id': emergency_id,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def handle_unsubscribe_emergency(self, data):
        """Handle emergency unsubscription."""
        emergency_id = data.get('emergency_id')
        if not emergency_id:
            await self.send_error('missing_emergency_id', 'Emergency ID is required')
            return
        
        # Remove from emergency-specific group
        emergency_group = f'emergency_{emergency_id}'
        await self.channel_layer.group_discard(
            emergency_group,
            self.channel_name
        )
        
        # Remove subscription
        await self.remove_subscription(emergency_id)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscribed',
            'emergency_id': emergency_id,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def handle_request_status(self, data):
        """Handle status request."""
        emergency_id = data.get('emergency_id')
        if not emergency_id:
            await self.send_error('missing_emergency_id', 'Emergency ID is required')
            return
        
        # Get emergency status
        status = await self.get_emergency_status(emergency_id)
        
        await self.send(text_data=json.dumps({
            'type': 'status_response',
            'emergency_id': emergency_id,
            'status': status,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def handle_update_location(self, data):
        """Handle location update request."""
        location_data = data.get('location_data', {})
        if not location_data:
            await self.send_error('missing_location_data', 'Location data is required')
            return
        
        # Process location update
        result = await self.process_location_update(location_data)
        
        await self.send(text_data=json.dumps({
            'type': 'location_updated',
            'result': result,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def emergency_status_update(self, event):
        """Handle emergency status update from group."""
        await self.send(text_data=json.dumps({
            'type': 'emergency_status_update',
            'emergency_id': event['emergency_id'],
            'status': event['status'],
            'message': event.get('message', ''),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def emergency_location_update(self, event):
        """Handle emergency location update from group."""
        await self.send(text_data=json.dumps({
            'type': 'emergency_location_update',
            'emergency_id': event['emergency_id'],
            'location': event['location'],
            'accuracy': event.get('accuracy'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def emergency_notification(self, event):
        """Handle emergency notification from group."""
        await self.send(text_data=json.dumps({
            'type': 'emergency_notification',
            'emergency_id': event['emergency_id'],
            'notification_type': event['notification_type'],
            'message': event['message'],
            'priority': event.get('priority', 'medium'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def emergency_responder_update(self, event):
        """Handle emergency responder update from group."""
        await self.send(text_data=json.dumps({
            'type': 'emergency_responder_update',
            'emergency_id': event['emergency_id'],
            'responder_id': event['responder_id'],
            'responder_name': event.get('responder_name', ''),
            'status': event['status'],
            'eta': event.get('eta'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def emergency_medical_update(self, event):
        """Handle emergency medical update from group."""
        await self.send(text_data=json.dumps({
            'type': 'emergency_medical_update',
            'emergency_id': event['emergency_id'],
            'medical_data': event['medical_data'],
            'consent_level': event.get('consent_level', 'none'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def log_connection(self, action: str, close_code: Optional[int] = None):
        """Log WebSocket connection event."""
        try:
            EmergencyAuditLog.log_action(
                action_type='websocket_connected' if action == 'connected' else 'websocket_disconnected',
                description=f'Emergency WebSocket {action}',
                user=self.user,
                severity='low',
                room_name=self.room_name,
                close_code=close_code
            )
        except Exception as e:
            logger.error(f"Failed to log WebSocket connection: {str(e)}")
    
    @database_sync_to_async
    def store_subscription(self, emergency_id: str):
        """Store emergency subscription."""
        try:
            cache_key = f"emergency_subscription:{self.user.id}:{emergency_id}"
            cache.set(cache_key, {
                'emergency_id': emergency_id,
                'user_id': self.user.id,
                'subscribed_at': django_timezone.now().isoformat()
            }, 3600)  # 1 hour
        except Exception as e:
            logger.error(f"Failed to store subscription: {str(e)}")
    
    @database_sync_to_async
    def remove_subscription(self, emergency_id: str):
        """Remove emergency subscription."""
        try:
            cache_key = f"emergency_subscription:{self.user.id}:{emergency_id}"
            cache.delete(cache_key)
        except Exception as e:
            logger.error(f"Failed to remove subscription: {str(e)}")
    
    @database_sync_to_async
    def get_emergency_status(self, emergency_id: str) -> Dict[str, Any]:
        """Get emergency status from database."""
        try:
            # This would typically query the database for emergency status
            # For now, return a basic structure
            cache_key = f"emergency_status:{emergency_id}"
            cached_status = cache.get(cache_key)
            
            if cached_status:
                return cached_status
            
            return {
                'emergency_id': emergency_id,
                'status': 'not_found',
                'message': 'Emergency not found'
            }
        except Exception as e:
            logger.error(f"Failed to get emergency status: {str(e)}")
            return {
                'emergency_id': emergency_id,
                'status': 'error',
                'message': 'Failed to retrieve status'
            }
    
    @database_sync_to_async
    def process_location_update(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process location update."""
        try:
            location_service = LocationService()
            result = location_service.process_location_update(self.user, location_data)
            return result
        except Exception as e:
            logger.error(f"Failed to process location update: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process location update',
                'details': str(e)
            }


class LocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for location tracking updates.
    Handles real-time location updates and GPS accuracy monitoring.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            # Extract user ID from URL
            self.user_id = self.scope['url_route']['kwargs'].get('user_id')
            if not self.user_id:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Get user from scope
            self.user = self.scope.get('user')
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Create user-specific group
            self.location_group_name = f'location_{self.user_id}'
            
            # Join location group
            await self.channel_layer.group_add(
                self.location_group_name,
                self.channel_name
            )
            
            # Accept connection
            await self.accept()
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'location_connected',
                'message': 'Connected to location updates',
                'user_id': self.user_id,
                'timestamp': django_timezone.now().isoformat()
            }))
            
            logger.info(f"Location WebSocket connected: User {self.user_id}")
            
        except Exception as e:
            logger.error(f"Location WebSocket connection failed: {str(e)}")
            await self.close(code=4000)  # Internal error
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Leave location group
            await self.channel_layer.group_discard(
                self.location_group_name,
                self.channel_name
            )
            
            logger.info(f"Location WebSocket disconnected: User {self.user_id}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Location WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                if message_type == 'location_update':
                    await self.handle_location_update(data)
                elif message_type == 'accuracy_request':
                    await self.handle_accuracy_request(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Location WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_location_update(self, data):
        """Handle location update."""
        location_data = data.get('location_data', {})
        if not location_data:
            await self.send_error('missing_location_data', 'Location data is required')
            return
        
        # Process location update
        result = await self.process_location_update(location_data)
        
        await self.send(text_data=json.dumps({
            'type': 'location_processed',
            'result': result,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def handle_accuracy_request(self, data):
        """Handle accuracy request."""
        location_data = data.get('location_data', {})
        if not location_data:
            await self.send_error('missing_location_data', 'Location data is required')
            return
        
        # Validate accuracy
        validation = await self.validate_location_accuracy(location_data)
        
        await self.send(text_data=json.dumps({
            'type': 'accuracy_response',
            'validation': validation,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def location_update(self, event):
        """Handle location update from group."""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'location': event['location'],
            'accuracy': event.get('accuracy'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def accuracy_alert(self, event):
        """Handle accuracy alert from group."""
        await self.send(text_data=json.dumps({
            'type': 'accuracy_alert',
            'message': event['message'],
            'accuracy': event['accuracy'],
            'threshold': event.get('threshold'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def process_location_update(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process location update."""
        try:
            location_service = LocationService()
            result = location_service.process_location_update(self.user, location_data)
            return result
        except Exception as e:
            logger.error(f"Failed to process location update: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process location update',
                'details': str(e)
            }
    
    @database_sync_to_async
    def validate_location_accuracy(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location accuracy."""
        try:
            location_service = LocationService()
            validation = location_service.validate_location_data(location_data)
            return validation
        except Exception as e:
            logger.error(f"Failed to validate location accuracy: {str(e)}")
            return {
                'is_valid': False,
                'errors': ['validation_failed'],
                'details': str(e)
            }


class MedicalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for medical data updates.
    Handles real-time medical information updates and privacy controls.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            # Extract user ID from URL
            self.user_id = self.scope['url_route']['kwargs'].get('user_id')
            if not self.user_id:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Get user from scope
            self.user = self.scope.get('user')
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Create user-specific group
            self.medical_group_name = f'medical_{self.user_id}'
            
            # Join medical group
            await self.channel_layer.group_add(
                self.medical_group_name,
                self.channel_name
            )
            
            # Accept connection
            await self.accept()
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'medical_connected',
                'message': 'Connected to medical updates',
                'user_id': self.user_id,
                'timestamp': django_timezone.now().isoformat()
            }))
            
            logger.info(f"Medical WebSocket connected: User {self.user_id}")
            
        except Exception as e:
            logger.error(f"Medical WebSocket connection failed: {str(e)}")
            await self.close(code=4000)  # Internal error
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Leave medical group
            await self.channel_layer.group_discard(
                self.medical_group_name,
                self.channel_name
            )
            
            logger.info(f"Medical WebSocket disconnected: User {self.user_id}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Medical WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                if message_type == 'medical_data_request':
                    await self.handle_medical_data_request(data)
                elif message_type == 'consent_update':
                    await self.handle_consent_update(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Medical WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_medical_data_request(self, data):
        """Handle medical data request."""
        consent_level = data.get('consent_level', 'basic')
        
        # Get medical data
        medical_data = await self.get_medical_data(consent_level)
        
        await self.send(text_data=json.dumps({
            'type': 'medical_data_response',
            'medical_data': medical_data,
            'consent_level': consent_level,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def handle_consent_update(self, data):
        """Handle consent update."""
        consent_level = data.get('consent_level')
        if not consent_level:
            await self.send_error('missing_consent_level', 'Consent level is required')
            return
        
        # Update consent
        result = await self.update_consent(consent_level)
        
        await self.send(text_data=json.dumps({
            'type': 'consent_updated',
            'result': result,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    async def medical_data_update(self, event):
        """Handle medical data update from group."""
        await self.send(text_data=json.dumps({
            'type': 'medical_data_update',
            'medical_data': event['medical_data'],
            'consent_level': event.get('consent_level', 'none'),
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def consent_update(self, event):
        """Handle consent update from group."""
        await self.send(text_data=json.dumps({
            'type': 'consent_update',
            'consent_level': event['consent_level'],
            'timestamp': event.get('timestamp', django_timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': django_timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_medical_data(self, consent_level: str) -> Dict[str, Any]:
        """Get medical data."""
        try:
            medical_service = MedicalService()
            result = medical_service.get_medical_data(self.user, consent_level)
            return result
        except Exception as e:
            logger.error(f"Failed to get medical data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve medical data',
                'details': str(e)
            }
    
    @database_sync_to_async
    def update_consent(self, consent_level: str) -> Dict[str, Any]:
        """Update consent level."""
        try:
            medical_service = MedicalService()
            result = medical_service.update_medical_data(self.user, {
                'consent_level': consent_level
            })
            return result
        except Exception as e:
            logger.error(f"Failed to update consent: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update consent',
                'details': str(e)
            }