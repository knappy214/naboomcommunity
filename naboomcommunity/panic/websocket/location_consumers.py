"""
WebSocket Consumers for Location Updates
Implements real-time location tracking and updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class LocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for location updates and tracking.
    """
    
    async def connect(self):
        """Handle WebSocket connection for location updates."""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.location_group_name = f'location_{self.user_id}'
        
        # Join location group
        await self.channel_layer.group_add(
            self.location_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'location_connected',
            'message': 'Connected to location updates',
            'user_id': self.user_id
        }))
        
        logger.info(f"Location WebSocket connected: {self.user_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave location group
        await self.channel_layer.group_discard(
            self.location_group_name,
            self.channel_name
        )
        
        logger.info(f"Location WebSocket disconnected: {self.user_id}")
    
    async def receive(self, text_data):
        """Handle received location data."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'location_update':
                # TODO: Implement location update processing
                await self.send(text_data=json.dumps({
                    'type': 'location_received',
                    'timestamp': text_data_json.get('timestamp'),
                    'status': 'success'
                }))
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Location WebSocket receive error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def location_broadcast(self, event):
        """Broadcast location update to connected clients."""
        await self.send(text_data=json.dumps({
            'type': 'location_broadcast',
            'data': event['data']
        }))
    
    async def emergency_location(self, event):
        """Send emergency location update."""
        await self.send(text_data=json.dumps({
            'type': 'emergency_location',
            'data': event['data']
        }))
