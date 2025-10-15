"""
Enhanced MQTT Service with Comprehensive Monitoring

This module extends the base MQTT service with health tracking, metrics collection,
and monitoring capabilities for operational visibility.
"""

import json
import logging
import signal
import sys
import time
from typing import Any, List, Optional
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings

from .mqtt_health import health_tracker

logger = logging.getLogger(__name__)


class MonitoredMQTTService:
    """
    Enhanced MQTT service with comprehensive monitoring and health tracking.
    
    This service extends the base MQTT functionality with:
    - Real-time health status tracking
    - Metrics collection and caching
    - Error tracking and reporting
    - Connection state monitoring
    - Performance indicators
    """
    
    def __init__(self):
        self.client = None
        self.running = True
        self.setup_signal_handlers()
        
        # Initialize health tracking
        self._initialize_health_tracking()
        
    def _initialize_health_tracking(self):
        """Initialize health tracking and metrics collection."""
        # Update connection status
        health_tracker.update_connection_status(False)
        
        # Set up default subscribed topics
        default_topics = [
            "naboom/community/+/+",  # All community topics
            "naboom/system/status",  # System status
            "naboom/notifications/+",  # Notifications
            "naboom/alerts/+",  # Emergency alerts
        ]
        health_tracker.update_subscribed_topics(default_topics)
        
        logger.info("Health tracking initialized")
    
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
            health_tracker.update_connection_status(True)
            
            # Subscribe to relevant topics
            topics = [
                "naboom/community/+/+",  # All community topics
                "naboom/system/status",  # System status
                "naboom/notifications/+",  # Notifications
                "naboom/alerts/+",  # Emergency alerts
            ]
            
            for topic in topics:
                result = client.subscribe(topic)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Successfully subscribed to topic: {topic}")
                else:
                    logger.error(f"Failed to subscribe to topic {topic}: {result}")
                    health_tracker.record_error(f"Failed to subscribe to {topic}")
            
            # Update subscribed topics in health tracker
            health_tracker.update_subscribed_topics(topics)
            
        else:
            error_msg = f"Failed to connect to MQTT broker: {reason_code}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
            health_tracker.update_connection_status(False)
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client disconnects from the broker."""
        if reason_code == 0:
            logger.info("Disconnected from MQTT broker")
        else:
            error_msg = f"Unexpected disconnection from MQTT broker: {reason_code}"
            logger.warning(error_msg)
            health_tracker.record_error(error_msg)
        
        health_tracker.update_connection_status(False)
    
    def on_message(self, client, userdata, message):
        """Callback for when a message is received."""
        try:
            # Track message processing
            health_tracker.increment_message_count()
            
            topic = message.topic
            payload = message.payload.decode('utf-8')
            
            logger.debug(f"Received message on topic '{topic}': {payload}")
            
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
            elif topic_parts[0] == 'naboom' and topic_parts[1] == 'alerts':
                self.handle_alert_message(topic_parts[2], payload)
                
        except Exception as e:
            error_msg = f"Error processing MQTT message: {e}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
    
    def handle_community_message(self, channel_id: str, action: str, payload: str):
        """Handle community-related MQTT messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.info(f"Community message - Channel: {channel_id}, Action: {action}, Data: {data}")
            
            # Handle different actions
            if action == "post":
                self.handle_new_post(channel_id, data)
            elif action == "comment":
                self.handle_new_comment(channel_id, data)
            elif action == "user_join":
                self.handle_user_join(channel_id, data)
            elif action == "user_leave":
                self.handle_user_leave(channel_id, data)
            elif action == "reaction":
                self.handle_reaction(channel_id, data)
            else:
                logger.warning(f"Unknown community action: {action}")
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in community message: {payload}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
        except Exception as e:
            error_msg = f"Error handling community message: {e}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
    
    def handle_system_message(self, action: str, payload: str):
        """Handle system-related MQTT messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.info(f"System message - Action: {action}, Data: {data}")
            
            if action == "status":
                self.handle_system_status(data)
            elif action == "health_check":
                self.handle_health_check(data)
            elif action == "metrics_request":
                self.handle_metrics_request(data)
            else:
                logger.warning(f"Unknown system action: {action}")
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in system message: {payload}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
        except Exception as e:
            error_msg = f"Error handling system message: {e}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
    
    def handle_notification_message(self, user_id: str, payload: str):
        """Handle notification-related MQTT messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.info(f"Notification message - User: {user_id}, Data: {data}")
            
            # Send real-time notification
            self.send_user_notification(user_id, data)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in notification message: {payload}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
        except Exception as e:
            error_msg = f"Error handling notification message: {e}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
    
    def handle_alert_message(self, alert_type: str, payload: str):
        """Handle emergency alert messages."""
        try:
            data = json.loads(payload) if payload else {}
            logger.warning(f"Alert message - Type: {alert_type}, Data: {data}")
            
            # Handle different alert types
            if alert_type == "emergency":
                self.handle_emergency_alert(data)
            elif alert_type == "security":
                self.handle_security_alert(data)
            elif alert_type == "system":
                self.handle_system_alert(data)
            else:
                logger.warning(f"Unknown alert type: {alert_type}")
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in alert message: {payload}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
        except Exception as e:
            error_msg = f"Error handling alert message: {e}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
    
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
        
    def handle_reaction(self, channel_id: str, data: dict):
        """Handle reaction notifications."""
        logger.info(f"Reaction in channel {channel_id}: {data}")
        # Add your reaction handling logic here
        
    def handle_system_status(self, data: dict):
        """Handle system status updates."""
        logger.info(f"System status update: {data}")
        # Add your system status logic here
        
    def handle_health_check(self, data: dict):
        """Handle health check requests."""
        logger.info(f"Health check request: {data}")
        
        # Get current health metrics
        metrics = health_tracker.get_health_metrics()
        
        # Publish health status
        health_data = {
            "status": "healthy" if metrics.connected else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": metrics.uptime,
            "messages_processed": metrics.messages_processed,
            "connected": metrics.connected,
            "services": {
                "django": "running",
                "celery": "running",
                "daphne": "running",
                "mqtt": "connected" if metrics.connected else "disconnected"
            }
        }
        self.publish_message("naboom/system/health", json.dumps(health_data))
        
    def handle_metrics_request(self, data: dict):
        """Handle metrics request."""
        logger.info(f"Metrics request: {data}")
        
        # Get current metrics
        metrics = health_tracker.get_health_metrics()
        
        # Publish metrics
        metrics_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": metrics.uptime,
            "messages_processed": metrics.messages_processed,
            "messages_per_minute": metrics.messages_per_minute,
            "connection_retries": metrics.connection_retries,
            "error_count": metrics.error_count,
            "subscribed_topics": metrics.subscribed_topics,
        }
        self.publish_message("naboom/system/metrics", json.dumps(metrics_data))
        
    def handle_emergency_alert(self, data: dict):
        """Handle emergency alerts."""
        logger.critical(f"Emergency alert: {data}")
        # Add your emergency alert logic here
        
    def handle_security_alert(self, data: dict):
        """Handle security alerts."""
        logger.warning(f"Security alert: {data}")
        # Add your security alert logic here
        
    def handle_system_alert(self, data: dict):
        """Handle system alerts."""
        logger.warning(f"System alert: {data}")
        # Add your system alert logic here
        
    def send_user_notification(self, user_id: str, data: dict):
        """Send notification to specific user."""
        logger.info(f"Sending notification to user {user_id}: {data}")
        # Add your notification logic here
        
    def publish_message(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Publish a message to MQTT broker."""
        if self.client and self.client.is_connected():
            try:
                result = self.client.publish(topic, payload, qos, retain)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"Published message to {topic}")
                    # Track successful publish
                    health_tracker.increment_message_count()
                else:
                    error_msg = f"Failed to publish message to {topic}: {result.rc}"
                    logger.error(error_msg)
                    health_tracker.record_error(error_msg)
            except Exception as e:
                error_msg = f"Exception while publishing to {topic}: {e}"
                logger.error(error_msg)
                health_tracker.record_error(error_msg)
        else:
            error_msg = "MQTT client not connected, cannot publish message"
            logger.warning(error_msg)
            health_tracker.record_error(error_msg)
    
    def connect(self):
        """Connect to MQTT broker with retry logic."""
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
            error_msg = f"Failed to connect to MQTT broker: {e}"
            logger.error(error_msg)
            health_tracker.record_error(error_msg)
            health_tracker.increment_connection_retries()
            return False
    
    def run(self):
        """Run the monitored MQTT service."""
        if not self.connect():
            logger.error("Failed to connect to MQTT broker")
            return False
            
        logger.info("Starting monitored MQTT service...")
        
        # Start the network loop
        self.client.loop_start()
        
        # Main service loop with health monitoring
        while self.running:
            try:
                # Check connection status
                if not self.client.is_connected():
                    logger.warning("MQTT connection lost, attempting to reconnect...")
                    health_tracker.update_connection_status(False)
                    health_tracker.increment_connection_retries()
                    
                    # Attempt reconnection
                    if not self.connect():
                        logger.error("Failed to reconnect to MQTT broker")
                        time.sleep(5)  # Wait before retry
                        continue
                    else:
                        self.client.loop_start()
                
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                error_msg = f"Unexpected error in MQTT service: {e}"
                logger.error(error_msg)
                health_tracker.record_error(error_msg)
                time.sleep(1)
        
        # Cleanup
        logger.info("Stopping monitored MQTT service...")
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        health_tracker.update_connection_status(False)
        logger.info("Monitored MQTT service stopped")
        return True


class Command(BaseCommand):
    """Django management command to run monitored MQTT service."""
    
    help = 'Run monitored MQTT service for Naboom Community with health tracking'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (not implemented yet)',
        )
        parser.add_argument(
            '--log-level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set logging level',
        )
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Setup logging
        log_level = getattr(logging, options['log_level'].upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info("Starting Naboom Community Monitored MQTT Service")
        
        # Create and run monitored MQTT service
        mqtt_service = MonitoredMQTTService()
        success = mqtt_service.run()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('Monitored MQTT service completed successfully')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Monitored MQTT service failed to start')
            )
            sys.exit(1)
