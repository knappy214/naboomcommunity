"""
WebSocket Consumers for Emergency Response
Implements real-time emergency updates and notifications with authentication.
"""

import json
import logging
from .emergency_auth import EmergencyWebSocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class EmergencyConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for emergency updates and real-time notifications with authentication.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract room name from URL
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'default')
        self.room_group_name = f'emergency_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Add to emergency updates group
        await self.channel_layer.group_add('emergency_updates', self.channel_name)
        
        # Send welcome message
        await self.send_success_message('connection_established', {
            'message': 'Connected to emergency updates',
            'room': self.room_name,
            'user_id': str(self.user.id),
            'username': self.user.username
        })
        
        logger.info(f"Emergency WebSocket connected: {self.room_name} for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Leave room groups
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.channel_layer.group_discard('emergency_updates', self.channel_name)
            await self.channel_layer.group_discard('location_updates', self.channel_name)
            await self.channel_layer.group_discard('medical_updates', self.channel_name)
            await self.channel_layer.group_discard('notification_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Emergency WebSocket disconnected: {self.room_name}")
    
    async def handle_subscribe(self, data):
        """Handle subscription to emergency updates."""
        try:
            subscription_type = data.get('subscription_type', 'all')
            channels = data.get('channels', [])
            
            # Check permission for subscription type
            if not await self.check_subscription_permission(subscription_type):
                await self.send_error_message('permission_denied', f'Permission denied for {subscription_type} subscription', 4003)
                return
            
            # Add to appropriate groups
            if subscription_type == 'all':
                await self.channel_layer.group_add('emergency_updates', self.channel_name)
            elif subscription_type == 'location':
                await self.channel_layer.group_add('location_updates', self.channel_name)
            elif subscription_type == 'medical':
                await self.channel_layer.group_add('medical_updates', self.channel_name)
            elif subscription_type == 'notification':
                await self.channel_layer.group_add('notification_updates', self.channel_name)
            
            # Add to specific channels if provided
            for channel in channels:
                channel_group = f'emergency_channel_{channel}'
                await self.channel_layer.group_add(channel_group, self.channel_name)
            
            await self.send_success_message('subscribed', {
                'subscription_type': subscription_type,
                'channels': channels
            })
            
        except Exception as e:
            logger.error(f"Subscription error: {str(e)}")
            await self.send_error_message('subscription_error', 'Subscription failed', 4500)
    
    async def handle_unsubscribe(self, data):
        """Handle unsubscription from emergency updates."""
        try:
            subscription_type = data.get('subscription_type', 'all')
            channels = data.get('channels', [])
            
            # Remove from appropriate groups
            if subscription_type == 'all':
                await self.channel_layer.group_discard('emergency_updates', self.channel_name)
            elif subscription_type == 'location':
                await self.channel_layer.group_discard('location_updates', self.channel_name)
            elif subscription_type == 'medical':
                await self.channel_layer.group_discard('medical_updates', self.channel_name)
            elif subscription_type == 'notification':
                await self.channel_layer.group_discard('notification_updates', self.channel_name)
            
            # Remove from specific channels
            for channel in channels:
                channel_group = f'emergency_channel_{channel}'
                await self.channel_layer.group_discard(channel_group, self.channel_name)
            
            await self.send_success_message('unsubscribed', {
                'subscription_type': subscription_type,
                'channels': channels
            })
            
        except Exception as e:
            logger.error(f"Unsubscription error: {str(e)}")
            await self.send_error_message('unsubscription_error', 'Unsubscription failed', 4500)
    
    async def handle_emergency_alert(self, data):
        """Handle emergency alert messages."""
        try:
            # Check permission for emergency alerts
            if not await self.check_emergency_permission('panic_activate'):
                await self.send_error_message('permission_denied', 'Permission denied for emergency alerts', 4003)
                return
            
            # Process emergency alert
            alert_data = data.get('alert_data', {})
            await self.process_emergency_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Emergency alert error: {str(e)}")
            await self.send_error_message('alert_error', 'Emergency alert failed', 4500)
    
    async def check_subscription_permission(self, subscription_type: str) -> bool:
        """Check if user has permission for subscription type."""
        try:
            if subscription_type == 'medical':
                return await self.check_emergency_permission('medical_access')
            elif subscription_type == 'location':
                return await self.check_emergency_permission('location_access')
            elif subscription_type == 'notification':
                return await self.check_emergency_permission('notification_send')
            else:
                return True  # 'all' subscription is allowed for authenticated users
        except Exception as e:
            logger.error(f"Subscription permission check error: {str(e)}")
            return False
    
    async def check_emergency_permission(self, permission_type: str) -> bool:
        """Check if user has emergency permission."""
        return await self.check_websocket_permission(self.user, permission_type)
    
    async def process_emergency_alert(self, alert_data: dict):
        """Process emergency alert data."""
        try:
            # Log emergency alert
            await self.log_websocket_connection(
                self.user, 'emergency_alert', True, 
                f"Emergency alert processed: {alert_data.get('type', 'unknown')}"
            )
            
            # Send confirmation
            await self.send_success_message('alert_processed', {
                'alert_id': alert_data.get('id'),
                'timestamp': alert_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Emergency alert processing error: {str(e)}")
            raise
    
    async def emergency_update(self, event):
        """Send emergency update to WebSocket."""
        try:
            # Check if user should receive this update
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'emergency_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Emergency update error: {str(e)}")
    
    async def status_change(self, event):
        """Send status change notification to WebSocket."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'status_change',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Status change error: {str(e)}")
    
    async def responder_assignment(self, event):
        """Send responder assignment notification to WebSocket."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'responder_assignment',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Responder assignment error: {str(e)}")
    
    async def location_update(self, event):
        """Handle location update messages."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'location_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Location update error: {str(e)}")
    
    async def medical_update(self, event):
        """Handle medical update messages."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'medical_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Medical update error: {str(e)}")
    
    async def notification_update(self, event):
        """Handle notification update messages."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'notification_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Notification update error: {str(e)}")
    
    async def should_receive_update(self, data: dict) -> bool:
        """Check if user should receive this update."""
        try:
            # Check if update is for this user
            user_id = data.get('user_id')
            if user_id and str(user_id) != str(self.user.id):
                # Check if user has permission to see other users' data
                return await self.check_emergency_permission('location_access')
            
            return True
            
        except Exception as e:
            logger.error(f"Update permission check error: {str(e)}")
            return False
