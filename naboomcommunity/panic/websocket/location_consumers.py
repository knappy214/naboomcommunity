"""
Location WebSocket Consumers
Real-time location tracking and updates for emergency response.
"""

from .emergency_auth import EmergencyWebSocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class LocationConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for location tracking and updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract user ID from URL
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.location_group_name = f'location_updates_{self.user_id}' if self.user_id else 'location_updates'
        
        # Join location group
        await self.channel_layer.group_add(
            self.location_group_name,
            self.channel_name
        )
        
        # Add to general location updates group
        await self.channel_layer.group_add('location_updates', self.channel_name)
        
        logger.info(f"Location WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Remove from groups
            if hasattr(self, 'location_group_name'):
                await self.channel_layer.group_discard(
                    self.location_group_name,
                    self.channel_name
                )
            await self.channel_layer.group_discard('location_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from location groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Location WebSocket disconnected: {close_code}")
    
    async def handle_location_update(self, data):
        """Handle location update messages."""
        try:
            # Check permission for location updates
            if not await self.check_emergency_permission('location_access'):
                await self.send_error_message('permission_denied', 'Permission denied for location updates', 4003)
                return
            
            # Process location update
            location_data = data.get('location_data', {})
            await self.process_location_update(location_data)
            
        except Exception as e:
            logger.error(f"Location update error: {str(e)}")
            await self.send_error_message('location_error', 'Location update failed', 4500)
    
    async def handle_gps_request(self, data):
        """Handle GPS accuracy request."""
        try:
            # Check permission for location access
            if not await self.check_emergency_permission('location_access'):
                await self.send_error_message('permission_denied', 'Permission denied for GPS requests', 4003)
                return
            
            # Process GPS request
            gps_data = data.get('gps_data', {})
            await self.process_gps_request(gps_data)
            
        except Exception as e:
            logger.error(f"GPS request error: {str(e)}")
            await self.send_error_message('gps_error', 'GPS request failed', 4500)
    
    async def process_location_update(self, location_data):
        """Process location update data."""
        try:
            # Log location update
            await self.log_websocket_connection(
                self.user, 'location_update', True, 
                f"Location update processed: {location_data.get('accuracy', 'unknown')}m accuracy"
            )
            
            # Send confirmation
            await self.send_success_message('location_updated', {
                'location_id': location_data.get('id'),
                'accuracy': location_data.get('accuracy'),
                'timestamp': location_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Location update processing error: {str(e)}")
            raise
    
    async def process_gps_request(self, gps_data):
        """Process GPS accuracy request."""
        try:
            # Log GPS request
            await self.log_websocket_connection(
                self.user, 'gps_request', True, 
                f"GPS request processed: {gps_data.get('requested_accuracy', 'unknown')}m"
            )
            
            # Send GPS response
            await self.send_success_message('gps_response', {
                'request_id': gps_data.get('request_id'),
                'accuracy': gps_data.get('current_accuracy'),
                'status': gps_data.get('status', 'active')
            })
            
        except Exception as e:
            logger.error(f"GPS request processing error: {str(e)}")
            raise
    
    async def location_update(self, event):
        """Handle location update messages from channel layer."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'location_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Location update event error: {str(e)}")
    
    async def gps_accuracy_update(self, event):
        """Handle GPS accuracy update messages."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'gps_accuracy_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"GPS accuracy update error: {str(e)}")
    
    async def location_alert(self, event):
        """Handle location alert messages."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'location_alert',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Location alert error: {str(e)}")
    
    async def should_receive_update(self, data):
        """Check if user should receive this location update."""
        try:
            # Check if update is for this user
            user_id = data.get('user_id')
            if user_id and str(user_id) != str(self.user.id):
                # Check if user has permission to see other users' location data
                return await self.check_emergency_permission('location_access')
            
            return True
            
        except Exception as e:
            logger.error(f"Location update permission check error: {str(e)}")
            return False


class MedicalConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for medical information updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract user ID from URL
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.medical_group_name = f'medical_updates_{self.user_id}' if self.user_id else 'medical_updates'
        
        # Join medical group
        await self.channel_layer.group_add(
            self.medical_group_name,
            self.channel_name
        )
        
        # Add to general medical updates group
        await self.channel_layer.group_add('medical_updates', self.channel_name)
        
        logger.info(f"Medical WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Remove from groups
            if hasattr(self, 'medical_group_name'):
                await self.channel_layer.group_discard(
                    self.medical_group_name,
                    self.channel_name
                )
            await self.channel_layer.group_discard('medical_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from medical groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Medical WebSocket disconnected: {close_code}")
    
    async def handle_medical_update(self, data):
        """Handle medical information update messages."""
        try:
            # Check permission for medical data access
            if not await self.check_emergency_permission('medical_access'):
                await self.send_error_message('permission_denied', 'Permission denied for medical updates', 4003)
                return
            
            # Process medical update
            medical_data = data.get('medical_data', {})
            await self.process_medical_update(medical_data)
            
        except Exception as e:
            logger.error(f"Medical update error: {str(e)}")
            await self.send_error_message('medical_error', 'Medical update failed', 4500)
    
    async def process_medical_update(self, medical_data):
        """Process medical information update."""
        try:
            # Log medical update
            await self.log_websocket_connection(
                self.user, 'medical_update', True, 
                f"Medical update processed: {medical_data.get('type', 'unknown')}"
            )
            
            # Send confirmation
            await self.send_success_message('medical_updated', {
                'medical_id': medical_data.get('id'),
                'type': medical_data.get('type'),
                'timestamp': medical_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Medical update processing error: {str(e)}")
            raise
    
    async def medical_update(self, event):
        """Handle medical update messages from channel layer."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'medical_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Medical update event error: {str(e)}")
    
    async def medical_alert(self, event):
        """Handle medical alert messages."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'medical_alert',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Medical alert error: {str(e)}")
    
    async def should_receive_update(self, data):
        """Check if user should receive this medical update."""
        try:
            # Check if update is for this user
            user_id = data.get('user_id')
            if user_id and str(user_id) != str(self.user.id):
                # Check if user has permission to see other users' medical data
                return await self.check_emergency_permission('medical_access')
            
            return True
            
        except Exception as e:
            logger.error(f"Medical update permission check error: {str(e)}")
            return False


class FamilyConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for family notification updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract user ID from URL
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.family_group_name = f'family_updates_{self.user_id}' if self.user_id else 'family_updates'
        
        # Join family group
        await self.channel_layer.group_add(
            self.family_group_name,
            self.channel_name
        )
        
        # Add to general family updates group
        await self.channel_layer.group_add('family_updates', self.channel_name)
        
        logger.info(f"Family WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Remove from groups
            if hasattr(self, 'family_group_name'):
                await self.channel_layer.group_discard(
                    self.family_group_name,
                    self.channel_name
                )
            await self.channel_layer.group_discard('family_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from family groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Family WebSocket disconnected: {close_code}")
    
    async def handle_family_notification(self, data):
        """Handle family notification messages."""
        try:
            # Check permission for family notifications
            if not await self.check_emergency_permission('notification_send'):
                await self.send_error_message('permission_denied', 'Permission denied for family notifications', 4003)
                return
            
            # Process family notification
            notification_data = data.get('notification_data', {})
            await self.process_family_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Family notification error: {str(e)}")
            await self.send_error_message('family_error', 'Family notification failed', 4500)
    
    async def process_family_notification(self, notification_data):
        """Process family notification."""
        try:
            # Log family notification
            await self.log_websocket_connection(
                self.user, 'family_notification', True, 
                f"Family notification processed: {notification_data.get('type', 'unknown')}"
            )
            
            # Send confirmation
            await self.send_success_message('family_notified', {
                'notification_id': notification_data.get('id'),
                'type': notification_data.get('type'),
                'recipients': notification_data.get('recipients', []),
                'timestamp': notification_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Family notification processing error: {str(e)}")
            raise
    
    async def family_notification(self, event):
        """Handle family notification messages from channel layer."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'family_notification',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Family notification event error: {str(e)}")
    
    async def should_receive_update(self, data):
        """Check if user should receive this family update."""
        try:
            # Check if update is for this user
            user_id = data.get('user_id')
            if user_id and str(user_id) != str(self.user.id):
                # Check if user has permission to see other users' family data
                return await self.check_emergency_permission('notification_send')
            
            return True
            
        except Exception as e:
            logger.error(f"Family update permission check error: {str(e)}")
            return False


class IntegrationConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for external service integration updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract service type from URL
        self.service_type = self.scope['url_route']['kwargs'].get('service_type')
        self.integration_group_name = f'integration_updates_{self.service_type}' if self.service_type else 'integration_updates'
        
        # Join integration group
        await self.channel_layer.group_add(
            self.integration_group_name,
            self.channel_name
        )
        
        # Add to general integration updates group
        await self.channel_layer.group_add('integration_updates', self.channel_name)
        
        logger.info(f"Integration WebSocket connected for user {self.user.username}, service: {self.service_type}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Remove from groups
            if hasattr(self, 'integration_group_name'):
                await self.channel_layer.group_discard(
                    self.integration_group_name,
                    self.channel_name
                )
            await self.channel_layer.group_discard('integration_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from integration groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Integration WebSocket disconnected: {close_code}")
    
    async def handle_integration_update(self, data):
        """Handle integration update messages."""
        try:
            # Check permission for external API access
            if not await self.check_emergency_permission('external_api'):
                await self.send_error_message('permission_denied', 'Permission denied for integration updates', 4003)
                return
            
            # Process integration update
            integration_data = data.get('integration_data', {})
            await self.process_integration_update(integration_data)
            
        except Exception as e:
            logger.error(f"Integration update error: {str(e)}")
            await self.send_error_message('integration_error', 'Integration update failed', 4500)
    
    async def process_integration_update(self, integration_data):
        """Process integration update."""
        try:
            # Log integration update
            await self.log_websocket_connection(
                self.user, 'integration_update', True, 
                f"Integration update processed: {integration_data.get('service', 'unknown')}"
            )
            
            # Send confirmation
            await self.send_success_message('integration_updated', {
                'integration_id': integration_data.get('id'),
                'service': integration_data.get('service'),
                'status': integration_data.get('status'),
                'timestamp': integration_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Integration update processing error: {str(e)}")
            raise
    
    async def integration_update(self, event):
        """Handle integration update messages from channel layer."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'integration_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Integration update event error: {str(e)}")
    
    async def should_receive_update(self, data):
        """Check if user should receive this integration update."""
        try:
            # Check if update is for this service type
            service_type = data.get('service_type')
            if service_type and self.service_type and service_type != self.service_type:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Integration update permission check error: {str(e)}")
            return False


class OfflineConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for offline sync status updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract user ID from URL
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.offline_group_name = f'offline_updates_{self.user_id}' if self.user_id else 'offline_updates'
        
        # Join offline group
        await self.channel_layer.group_add(
            self.offline_group_name,
            self.channel_name
        )
        
        # Add to general offline updates group
        await self.channel_layer.group_add('offline_updates', self.channel_name)
        
        logger.info(f"Offline WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Remove from groups
            if hasattr(self, 'offline_group_name'):
                await self.channel_layer.group_discard(
                    self.offline_group_name,
                    self.channel_name
                )
            await self.channel_layer.group_discard('offline_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from offline groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Offline WebSocket disconnected: {close_code}")
    
    async def handle_offline_sync(self, data):
        """Handle offline sync messages."""
        try:
            # Check permission for offline sync
            if not await self.check_emergency_permission('offline_sync'):
                await self.send_error_message('permission_denied', 'Permission denied for offline sync', 4003)
                return
            
            # Process offline sync
            sync_data = data.get('sync_data', {})
            await self.process_offline_sync(sync_data)
            
        except Exception as e:
            logger.error(f"Offline sync error: {str(e)}")
            await self.send_error_message('offline_error', 'Offline sync failed', 4500)
    
    async def process_offline_sync(self, sync_data):
        """Process offline sync."""
        try:
            # Log offline sync
            await self.log_websocket_connection(
                self.user, 'offline_sync', True, 
                f"Offline sync processed: {sync_data.get('status', 'unknown')}"
            )
            
            # Send confirmation
            await self.send_success_message('offline_synced', {
                'sync_id': sync_data.get('id'),
                'status': sync_data.get('status'),
                'items_synced': sync_data.get('items_synced', 0),
                'timestamp': sync_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Offline sync processing error: {str(e)}")
            raise
    
    async def offline_sync_update(self, event):
        """Handle offline sync update messages from channel layer."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'offline_sync_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Offline sync update event error: {str(e)}")
    
    async def should_receive_update(self, data):
        """Check if user should receive this offline update."""
        try:
            # Check if update is for this user
            user_id = data.get('user_id')
            if user_id and str(user_id) != str(self.user.id):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Offline update permission check error: {str(e)}")
            return False


class StatusConsumer(EmergencyWebSocketConsumer):
    """
    WebSocket consumer for general emergency status updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        await super().connect()
        
        # Extract incident ID from URL
        self.incident_id = self.scope['url_route']['kwargs'].get('incident_id')
        self.status_group_name = f'status_updates_{self.incident_id}' if self.incident_id else 'status_updates'
        
        # Join status group
        await self.channel_layer.group_add(
            self.status_group_name,
            self.channel_name
        )
        
        # Add to general status updates group
        await self.channel_layer.group_add('status_updates', self.channel_name)
        
        logger.info(f"Status WebSocket connected for user {self.user.username}, incident: {self.incident_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Remove from groups
            if hasattr(self, 'status_group_name'):
                await self.channel_layer.group_discard(
                    self.status_group_name,
                    self.channel_name
                )
            await self.channel_layer.group_discard('status_updates', self.channel_name)
        except Exception as e:
            logger.error(f"Error removing from status groups: {str(e)}")
        
        await super().disconnect(close_code)
        logger.info(f"Status WebSocket disconnected: {close_code}")
    
    async def handle_status_update(self, data):
        """Handle status update messages."""
        try:
            # Process status update
            status_data = data.get('status_data', {})
            await self.process_status_update(status_data)
            
        except Exception as e:
            logger.error(f"Status update error: {str(e)}")
            await self.send_error_message('status_error', 'Status update failed', 4500)
    
    async def process_status_update(self, status_data):
        """Process status update."""
        try:
            # Log status update
            await self.log_websocket_connection(
                self.user, 'status_update', True, 
                f"Status update processed: {status_data.get('status', 'unknown')}"
            )
            
            # Send confirmation
            await self.send_success_message('status_updated', {
                'status_id': status_data.get('id'),
                'status': status_data.get('status'),
                'incident_id': status_data.get('incident_id'),
                'timestamp': status_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Status update processing error: {str(e)}")
            raise
    
    async def status_update(self, event):
        """Handle status update messages from channel layer."""
        try:
            if await self.should_receive_update(event.get('data', {})):
                await self.send(text_data=json.dumps({
                    'type': 'status_update',
                    'data': event['data']
                }))
        except Exception as e:
            logger.error(f"Status update event error: {str(e)}")
    
    async def should_receive_update(self, data):
        """Check if user should receive this status update."""
        try:
            # Check if update is for this incident
            incident_id = data.get('incident_id')
            if incident_id and self.incident_id and str(incident_id) != str(self.incident_id):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Status update permission check error: {str(e)}")
            return False