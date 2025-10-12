"""Django management command to run MQTT service."""
import json
import logging
import signal
import sys
import time
from typing import Any

import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT service for Naboom Community."""
    
    def __init__(self):
        self.client = None
        self.running = True
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.client:
            self.client.disconnect()
        sys.exit(0)
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client connects to the broker."""
        if reason_code == 0:
            logger.info("Connected to MQTT broker successfully")
            # Subscribe to relevant topics
            client.subscribe("naboom/community/+/+")  # All community topics
            client.subscribe("naboom/system/status")  # System status
            client.subscribe("naboom/notifications/+")  # Notifications
        else:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client disconnects from the broker."""
        if reason_code == 0:
            logger.info("Disconnected from MQTT broker")
        else:
            logger.warning(f"Unexpected disconnection from MQTT broker: {reason_code}")
    
    def on_message(self, client, userdata, message):
        """Callback for when a message is received."""
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')
            
            logger.info(f"Received message on topic '{topic}': {payload}")
            
            # Parse topic structure: naboom/community/{channel_id}/{action}
            topic_parts = topic.split('/')
            if len(topic_parts) >= 4 and topic_parts[0] == 'naboom' and topic_parts[1] == 'community':
                channel_id = topic_parts[2]
                action = topic_parts[3]
                self.handle_community_message(channel_id, action, payload)
            elif topic_parts[0] == 'naboom' and topic_parts[1] == 'system':
                self.handle_system_message(topic_parts[2], payload)
            elif topic_parts[0] == 'naboom' and topic_parts[1] == 'notifications':
                self.handle_notification_message(topic_parts[2], payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_community_message(self, channel_id: str, action: str, payload: str):
        """Handle community-related MQTT messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.info(f"Community message - Channel: {channel_id}, Action: {action}, Data: {data}")
            
            # Here you can add specific logic for different actions
            if action == "post":
                self.handle_new_post(channel_id, data)
            elif action == "comment":
                self.handle_new_comment(channel_id, data)
            elif action == "user_join":
                self.handle_user_join(channel_id, data)
            elif action == "user_leave":
                self.handle_user_leave(channel_id, data)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in community message: {payload}")
        except Exception as e:
            logger.error(f"Error handling community message: {e}")
    
    def handle_system_message(self, action: str, payload: str):
        """Handle system-related MQTT messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.info(f"System message - Action: {action}, Data: {data}")
            
            if action == "status":
                self.handle_system_status(data)
            elif action == "health_check":
                self.handle_health_check(data)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in system message: {payload}")
        except Exception as e:
            logger.error(f"Error handling system message: {e}")
    
    def handle_notification_message(self, user_id: str, payload: str):
        """Handle notification-related MQTT messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.info(f"Notification message - User: {user_id}, Data: {data}")
            
            # Here you can add logic to send real-time notifications
            self.send_user_notification(user_id, data)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in notification message: {payload}")
        except Exception as e:
            logger.error(f"Error handling notification message: {e}")
    
    def handle_new_post(self, channel_id: str, data: dict):
        """Handle new post notifications."""
        logger.info(f"New post in channel {channel_id}: {data}")
        # Add your post handling logic here
        
    def handle_new_comment(self, channel_id: str, data: dict):
        """Handle new comment notifications."""
        logger.info(f"New comment in channel {channel_id}: {data}")
        # Add your comment handling logic here
        
    def handle_user_join(self, channel_id: str, data: dict):
        """Handle user join notifications."""
        logger.info(f"User joined channel {channel_id}: {data}")
        # Add your user join logic here
        
    def handle_user_leave(self, channel_id: str, data: dict):
        """Handle user leave notifications."""
        logger.info(f"User left channel {channel_id}: {data}")
        # Add your user leave logic here
        
    def handle_system_status(self, data: dict):
        """Handle system status updates."""
        logger.info(f"System status update: {data}")
        # Add your system status logic here
        
    def handle_health_check(self, data: dict):
        """Handle health check requests."""
        logger.info(f"Health check request: {data}")
        # Publish health status
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "django": "running",
                "celery": "running",
                "daphne": "running"
            }
        }
        self.publish_message("naboom/system/health", json.dumps(health_data))
        
    def send_user_notification(self, user_id: str, data: dict):
        """Send notification to specific user."""
        logger.info(f"Sending notification to user {user_id}: {data}")
        # Add your notification logic here
        
    def publish_message(self, topic: str, payload: str, qos: int = 0):
        """Publish a message to MQTT broker."""
        if self.client and self.client.is_connected():
            result = self.client.publish(topic, payload, qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to {topic}")
            else:
                logger.error(f"Failed to publish message to {topic}: {result.rc}")
        else:
            logger.warning("MQTT client not connected, cannot publish message")
    
    def connect(self):
        """Connect to MQTT broker."""
        # Get MQTT settings from Django settings
        mqtt_host = getattr(settings, 'MQTT_HOST', 'localhost')
        mqtt_port = getattr(settings, 'MQTT_PORT', 1883)
        mqtt_username = getattr(settings, 'MQTT_USERNAME', None)
        mqtt_password = getattr(settings, 'MQTT_PASSWORD', None)
        mqtt_client_id = getattr(settings, 'MQTT_CLIENT_ID', 'naboom-community')
        mqtt_keepalive = getattr(settings, 'MQTT_KEEPALIVE', 60)
        
        # Create MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, mqtt_client_id)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Set credentials if provided
        if mqtt_username and mqtt_password:
            self.client.username_pw_set(mqtt_username, mqtt_password)
        
        # Enable logging
        self.client.enable_logger(logger)
        
        try:
            logger.info(f"Connecting to MQTT broker at {mqtt_host}:{mqtt_port}")
            self.client.connect(mqtt_host, mqtt_port, mqtt_keepalive)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def run(self):
        """Run the MQTT service."""
        if not self.connect():
            return False
            
        logger.info("Starting MQTT service...")
        
        # Start the network loop
        self.client.loop_start()
        
        # Main service loop
        while self.running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
        
        # Cleanup
        logger.info("Stopping MQTT service...")
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT service stopped")
        return True


class Command(BaseCommand):
    """Django management command to run MQTT service."""
    
    help = 'Run MQTT service for Naboom Community'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (not implemented yet)',
        )
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info("Starting Naboom Community MQTT Service")
        
        # Create and run MQTT service
        mqtt_service = MQTTService()
        success = mqtt_service.run()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('MQTT service completed successfully')
            )
        else:
            self.stdout.write(
                self.style.ERROR('MQTT service failed to start')
            )
            sys.exit(1)
