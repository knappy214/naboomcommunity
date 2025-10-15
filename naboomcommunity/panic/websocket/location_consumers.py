"""
Additional WebSocket Consumers
Family, integration, offline, and status WebSocket consumers.
"""

import json
import logging
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class FamilyConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for family notifications.
    Handles real-time family notification updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.user_id = self.scope['url_route']['kwargs'].get('user_id')
            if not self.user_id:
                await self.close(code=4001)  # Unauthorized
                return
            
            self.user = self.scope.get('user')
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            self.family_group_name = f'family_{self.user_id}'
            
            await self.channel_layer.group_add(
                self.family_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'family_connected',
                'message': 'Connected to family notifications',
                'user_id': self.user_id,
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"Family WebSocket connected: User {self.user_id}")
            
        except Exception as e:
            logger.error(f"Family WebSocket connection failed: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            await self.channel_layer.group_discard(
                self.family_group_name,
                self.channel_name
            )
            
            logger.info(f"Family WebSocket disconnected: User {self.user_id}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Family WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                if message_type == 'family_notification_request':
                    await self.handle_family_notification_request(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Family WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_family_notification_request(self, data):
        """Handle family notification request."""
        notification_data = data.get('notification_data', {})
        
        # Process family notification
        result = await self.process_family_notification(notification_data)
        
        await self.send(text_data=json.dumps({
            'type': 'family_notification_response',
            'result': result,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def family_notification(self, event):
        """Handle family notification from group."""
        await self.send(text_data=json.dumps({
            'type': 'family_notification',
            'notification': event['notification'],
            'priority': event.get('priority', 'medium'),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def process_family_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process family notification."""
        try:
            # This would integrate with the family notification service
            return {
                'success': True,
                'message': 'Family notification processed',
                'notification_id': 'mock_id'
            }
        except Exception as e:
            logger.error(f"Failed to process family notification: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process family notification',
                'details': str(e)
            }


class IntegrationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for external service integration.
    Handles real-time integration updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.service_type = self.scope['url_route']['kwargs'].get('service_type', 'general')
            self.user = self.scope.get('user')
            
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            self.integration_group_name = f'integration_{self.service_type}'
            
            await self.channel_layer.group_add(
                self.integration_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'integration_connected',
                'message': f'Connected to {self.service_type} integration',
                'service_type': self.service_type,
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"Integration WebSocket connected: Service {self.service_type}")
            
        except Exception as e:
            logger.error(f"Integration WebSocket connection failed: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            await self.channel_layer.group_discard(
                self.integration_group_name,
                self.channel_name
            )
            
            logger.info(f"Integration WebSocket disconnected: Service {self.service_type}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Integration WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                if message_type == 'integration_request':
                    await self.handle_integration_request(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Integration WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_integration_request(self, data):
        """Handle integration request."""
        request_data = data.get('request_data', {})
        
        # Process integration request
        result = await self.process_integration_request(request_data)
        
        await self.send(text_data=json.dumps({
            'type': 'integration_response',
            'result': result,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def integration_update(self, event):
        """Handle integration update from group."""
        await self.send(text_data=json.dumps({
            'type': 'integration_update',
            'service_type': event['service_type'],
            'status': event['status'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def process_integration_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process integration request."""
        try:
            # This would integrate with external services
            return {
                'success': True,
                'message': 'Integration request processed',
                'service_type': self.service_type
            }
        except Exception as e:
            logger.error(f"Failed to process integration request: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process integration request',
                'details': str(e)
            }


class OfflineConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for offline sync status.
    Handles real-time offline sync updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.user_id = self.scope['url_route']['kwargs'].get('user_id')
            if not self.user_id:
                await self.close(code=4001)  # Unauthorized
                return
            
            self.user = self.scope.get('user')
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            self.offline_group_name = f'offline_{self.user_id}'
            
            await self.channel_layer.group_add(
                self.offline_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'offline_connected',
                'message': 'Connected to offline sync',
                'user_id': self.user_id,
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"Offline WebSocket connected: User {self.user_id}")
            
        except Exception as e:
            logger.error(f"Offline WebSocket connection failed: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            await self.channel_layer.group_discard(
                self.offline_group_name,
                self.channel_name
            )
            
            logger.info(f"Offline WebSocket disconnected: User {self.user_id}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Offline WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                if message_type == 'offline_sync_request':
                    await self.handle_offline_sync_request(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Offline WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_offline_sync_request(self, data):
        """Handle offline sync request."""
        sync_data = data.get('sync_data', {})
        
        # Process offline sync
        result = await self.process_offline_sync(sync_data)
        
        await self.send(text_data=json.dumps({
            'type': 'offline_sync_response',
            'result': result,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def offline_sync_update(self, event):
        """Handle offline sync update from group."""
        await self.send(text_data=json.dumps({
            'type': 'offline_sync_update',
            'sync_status': event['sync_status'],
            'progress': event.get('progress', 0),
            'message': event.get('message', ''),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def process_offline_sync(self, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process offline sync."""
        try:
            # This would integrate with the offline sync service
            return {
                'success': True,
                'message': 'Offline sync processed',
                'synced_items': len(sync_data.get('items', []))
            }
        except Exception as e:
            logger.error(f"Failed to process offline sync: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process offline sync',
                'details': str(e)
            }


class StatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for emergency status updates.
    Handles real-time emergency status monitoring.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.incident_id = self.scope['url_route']['kwargs'].get('incident_id')
            self.user = self.scope.get('user')
            
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)  # Unauthorized
                return
            
            if self.incident_id:
                self.status_group_name = f'status_{self.incident_id}'
            else:
                self.status_group_name = 'status_general'
            
            await self.channel_layer.group_add(
                self.status_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'status_connected',
                'message': 'Connected to status updates',
                'incident_id': self.incident_id,
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"Status WebSocket connected: Incident {self.incident_id}")
            
        except Exception as e:
            logger.error(f"Status WebSocket connection failed: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            await self.channel_layer.group_discard(
                self.status_group_name,
                self.channel_name
            )
            
            logger.info(f"Status WebSocket disconnected: Incident {self.incident_id}, Code {close_code}")
            
        except Exception as e:
            logger.error(f"Status WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                message_type = data.get('type', 'unknown')
                
                if message_type == 'status_request':
                    await self.handle_status_request(data)
                else:
                    await self.send_error('unknown_message_type', f'Unknown message type: {message_type}')
            
        except json.JSONDecodeError:
            await self.send_error('invalid_json', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Status WebSocket receive error: {str(e)}")
            await self.send_error('internal_error', 'Internal server error')
    
    async def handle_status_request(self, data):
        """Handle status request."""
        incident_id = data.get('incident_id', self.incident_id)
        
        # Get status
        status = await self.get_emergency_status(incident_id)
        
        await self.send(text_data=json.dumps({
            'type': 'status_response',
            'incident_id': incident_id,
            'status': status,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def status_update(self, event):
        """Handle status update from group."""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'incident_id': event['incident_id'],
            'status': event['status'],
            'message': event.get('message', ''),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def send_error(self, error_code: str, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_code': error_code,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_emergency_status(self, incident_id: str) -> Dict[str, Any]:
        """Get emergency status."""
        try:
            # This would query the database for emergency status
            return {
                'incident_id': incident_id,
                'status': 'active',
                'message': 'Emergency in progress',
                'last_updated': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get emergency status: {str(e)}")
            return {
                'incident_id': incident_id,
                'status': 'error',
                'message': 'Failed to retrieve status',
                'error': str(e)
            }