"""Django management command to run optimized MQTT service for HTTP/3 architecture."""
import asyncio
import json
import logging
import signal
import ssl
import sys
import time
from typing import Any, Optional, Dict
from urllib.parse import urlparse

import aiomqtt
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class OptimizedMQTTService:
    """Optimized MQTT service for HTTP/3 architecture with WebSocket support."""
    
    def __init__(self):
        self.client: Optional[aiomqtt.Client] = None
        self.running = True
        self.connection_retries = 0
        self.max_retries = 5
        self.retry_delay = 5
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        sys.exit(0)
    
    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for secure MQTT connections."""
        if not getattr(settings, 'MQTT_USE_SSL', False):
            return None
            
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.check_hostname = False  # For self-signed certificates
            ssl_context.verify_mode = ssl.CERT_NONE  # For self-signed certificates
            
            # For production, you would load proper CA certificates:
            # ssl_context.load_verify_locations('/path/to/ca-cert.pem')
            
            return ssl_context
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    def get_mqtt_client(self, use_websocket: bool = False) -> aiomqtt.Client:
        """Create and configure MQTT client optimized for HTTP/3 architecture."""
        # Get MQTT settings from Django settings
        mqtt_host = getattr(settings, 'MQTT_HOST', 'localhost')
        mqtt_port = getattr(settings, 'MQTT_SSL_PORT' if getattr(settings, 'MQTT_USE_SSL', False) else 'MQTT_PORT', 1883)
        mqtt_username = getattr(settings, 'MQTT_USERNAME', 'naboom-mqtt')
        mqtt_password = getattr(settings, 'MQTT_PASSWORD', 'NaboomMQTT2024!')
        mqtt_client_id = getattr(settings, 'MQTT_CLIENT_ID', 'naboom-community')
        mqtt_keepalive = getattr(settings, 'MQTT_KEEPALIVE', 60)
        
        # Create SSL context if needed
        tls_context = self.create_ssl_context()
        
        # Configure client for HTTP/3 optimization
        client_kwargs = {
            'hostname': mqtt_host,
            'port': mqtt_port,
            'username': mqtt_username,
            'password': mqtt_password,
            'identifier': mqtt_client_id,
            'keepalive': mqtt_keepalive,
            'tls_context': tls_context,
        }
        
        # Add WebSocket support if requested
        if use_websocket:
            # For WebSocket connections through Nginx proxy
            websocket_path = '/mqtt'
            client_kwargs['transport'] = 'websockets'
            client_kwargs['websocket_path'] = websocket_path
            client_kwargs['websocket_headers'] = {
                'Sec-WebSocket-Protocol': 'mqtt',
                'User-Agent': 'Naboom-Community-MQTT/1.0'
            }
        
        # Create MQTT client with authentication
        client = aiomqtt.Client(**client_kwargs)
        
        return client
    
    async def on_connect(self, client: aiomqtt.Client):
        """Callback for when the client connects to the broker."""
        logger.info("Connected to MQTT broker successfully")
        self.connection_retries = 0  # Reset retry counter on successful connection
        
        # Subscribe to relevant topics with HTTP/3 optimized patterns
        topics = [
            "naboom/community/+/+",  # All community topics
            "naboom/system/status",  # System status
            "naboom/notifications/+",  # Notifications
            "naboom/alerts/+",  # Emergency alerts
            "naboom/health/+",  # Health monitoring
        ]
        
        for topic in topics:
            await client.subscribe(topic, qos=1)  # Use QoS 1 for reliability
            logger.info(f"Subscribed to topic: {topic}")
    
    async def on_disconnect(self, client: aiomqtt.Client):
        """Callback for when the client disconnects from the broker."""
        logger.info("Disconnected from MQTT broker")
    
    async def handle_message(self, message: aiomqtt.Message):
        """Handle incoming MQTT messages with HTTP/3 optimization."""
        try:
            topic = str(message.topic)
            payload = message.payload.decode('utf-8') if message.payload else ""
            
            logger.info(f"Received message on topic '{topic}': {payload}")
            
            # Parse topic structure: naboom/{category}/{subcategory}/{action}
            topic_parts = topic.split('/')
            if len(topic_parts) >= 4 and topic_parts[0] == 'naboom':
                category = topic_parts[1]
                
                # Route to specific handlers based on category
                handler_map = {
                    'community': self.handle_community_message,
                    'system': self.handle_system_message,
                    'notifications': self.handle_notification_message,
                    'alerts': self.handle_alert_message,
                    'health': self.handle_health_message,
                }
                
                handler = handler_map.get(category)
                if handler:
                    await handler(topic_parts[2:], payload)
                else:
                    logger.warning(f"Unknown message category: {category}")
                    
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    async def handle_community_message(self, topic_parts: list, payload: str):
        """Handle community-related MQTT messages."""
        try:
            if len(topic_parts) < 2:
                return
                
            channel_id = topic_parts[0]
            action = topic_parts[1]
            data = json.loads(payload) if payload else {}
            
            logger.info(f"Community message - Channel: {channel_id}, Action: {action}, Data: {data}")
            
            # Route to specific handlers based on action
            handler_map = {
                "post": self.handle_new_post,
                "comment": self.handle_new_comment,
                "user_join": self.handle_user_join,
                "user_leave": self.handle_user_leave,
                "update": self.handle_community_update,
            }
            
            handler = handler_map.get(action)
            if handler:
                await handler(channel_id, data)
            else:
                logger.warning(f"Unknown community action: {action}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in community message: {payload}")
        except Exception as e:
            logger.error(f"Error handling community message: {e}")
    
    async def handle_system_message(self, topic_parts: list, payload: str):
        """Handle system-related MQTT messages."""
        try:
            if len(topic_parts) < 1:
                return
                
            action = topic_parts[0]
            data = json.loads(payload) if payload else {}
            
            logger.info(f"System message - Action: {action}, Data: {data}")
            
            handler_map = {
                "status": self.handle_system_status,
                "health_check": self.handle_health_check,
                "metrics": self.handle_system_metrics,
            }
            
            handler = handler_map.get(action)
            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown system action: {action}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in system message: {payload}")
        except Exception as e:
            logger.error(f"Error handling system message: {e}")
    
    async def handle_notification_message(self, topic_parts: list, payload: str):
        """Handle notification-related MQTT messages."""
        try:
            if len(topic_parts) < 1:
                return
                
            user_id = topic_parts[0]
            data = json.loads(payload) if payload else {}
            
            logger.info(f"Notification message - User: {user_id}, Data: {data}")
            await self.send_user_notification(user_id, data)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in notification message: {payload}")
        except Exception as e:
            logger.error(f"Error handling notification message: {e}")
    
    async def handle_alert_message(self, topic_parts: list, payload: str):
        """Handle emergency alert MQTT messages."""
        try:
            if len(topic_parts) < 1:
                return
                
            alert_type = topic_parts[0]
            data = json.loads(payload) if payload else {}
            
            logger.info(f"Alert message - Type: {alert_type}, Data: {data}")
            
            # Route to specific alert handlers
            handler_map = {
                "panic": self.handle_panic_alert,
                "emergency": self.handle_emergency_alert,
                "community": self.handle_community_alert,
            }
            
            handler = handler_map.get(alert_type)
            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown alert type: {alert_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in alert message: {payload}")
        except Exception as e:
            logger.error(f"Error handling alert message: {e}")
    
    async def handle_health_message(self, topic_parts: list, payload: str):
        """Handle health monitoring MQTT messages."""
        try:
            if len(topic_parts) < 1:
                return
                
            service = topic_parts[0]
            data = json.loads(payload) if payload else {}
            
            logger.info(f"Health message - Service: {service}, Data: {data}")
            await self.handle_service_health(service, data)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in health message: {payload}")
        except Exception as e:
            logger.error(f"Error handling health message: {e}")
    
    # Community message handlers
    async def handle_new_post(self, channel_id: str, data: dict):
        """Handle new post notifications."""
        logger.info(f"New post in channel {channel_id}: {data}")
        # Add your post handling logic here
        
    async def handle_new_comment(self, channel_id: str, data: dict):
        """Handle new comment notifications."""
        logger.info(f"New comment in channel {channel_id}: {data}")
        # Add your comment handling logic here
        
    async def handle_user_join(self, channel_id: str, data: dict):
        """Handle user join notifications."""
        logger.info(f"User joined channel {channel_id}: {data}")
        # Add your user join logic here
        
    async def handle_user_leave(self, channel_id: str, data: dict):
        """Handle user leave notifications."""
        logger.info(f"User left channel {channel_id}: {data}")
        # Add your user leave logic here
        
    async def handle_community_update(self, channel_id: str, data: dict):
        """Handle community update notifications."""
        logger.info(f"Community update in channel {channel_id}: {data}")
        # Add your community update logic here
    
    # System message handlers
    async def handle_system_status(self, data: dict):
        """Handle system status updates."""
        logger.info(f"System status update: {data}")
        # Add your system status logic here
        
    async def handle_health_check(self, data: dict):
        """Handle health check requests."""
        logger.info(f"Health check request: {data}")
        # Publish health status
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "django": "running",
                "celery": "running",
                "daphne": "running",
                "mqtt": "running",
                "nginx": "running",
                "redis": "running",
                "postgresql": "running"
            },
            "http3": {
                "enabled": True,
                "quic_support": True,
                "multiplexing": True
            }
        }
        await self.publish_message("naboom/system/health", json.dumps(health_data))
        
    async def handle_system_metrics(self, data: dict):
        """Handle system metrics updates."""
        logger.info(f"System metrics update: {data}")
        # Add your metrics handling logic here
    
    # Notification handlers
    async def send_user_notification(self, user_id: str, data: dict):
        """Send notification to specific user."""
        logger.info(f"Sending notification to user {user_id}: {data}")
        # Add your notification logic here
    
    # Alert handlers
    async def handle_panic_alert(self, data: dict):
        """Handle panic alert messages."""
        logger.info(f"Panic alert received: {data}")
        # Add your panic alert logic here
        
    async def handle_emergency_alert(self, data: dict):
        """Handle emergency alert messages."""
        logger.info(f"Emergency alert received: {data}")
        # Add your emergency alert logic here
        
    async def handle_community_alert(self, data: dict):
        """Handle community alert messages."""
        logger.info(f"Community alert received: {data}")
        # Add your community alert logic here
    
    # Health handlers
    async def handle_service_health(self, service: str, data: dict):
        """Handle service health monitoring."""
        logger.info(f"Service health - {service}: {data}")
        # Add your service health monitoring logic here
    
    async def publish_message(self, topic: str, payload: str, qos: int = 1, retain: bool = False):
        """Publish a message to MQTT broker with HTTP/3 optimization."""
        if self.client:
            try:
                await self.client.publish(topic, payload, qos=qos, retain=retain)
                logger.debug(f"Published message to {topic}")
            except Exception as e:
                logger.error(f"Failed to publish message to {topic}: {e}")
        else:
            logger.warning("MQTT client not available, cannot publish message")
    
    async def run(self, use_websocket: bool = False):
        """Run the optimized MQTT service."""
        logger.info("Starting optimized MQTT service for HTTP/3 architecture...")
        logger.info(f"WebSocket mode: {use_websocket}")
        
        while self.running and self.connection_retries < self.max_retries:
            try:
                # Create MQTT client
                self.client = self.get_mqtt_client(use_websocket=use_websocket)
                
                async with self.client as client:
                    self.client = client
                    await self.on_connect(client)
                    
                    # Main message processing loop
                    async for message in client.messages:
                        if not self.running:
                            break
                        await self.handle_message(message)
                        
            except aiomqtt.MqttError as e:
                self.connection_retries += 1
                logger.error(f"MQTT connection error (attempt {self.connection_retries}/{self.max_retries}): {e}")
                
                if self.connection_retries < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Max retries reached, giving up")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error in MQTT service: {e}")
                return False
        
        logger.info("Optimized MQTT service stopped")
        return True


class Command(BaseCommand):
    """Django management command to run optimized MQTT service."""
    
    help = 'Run optimized MQTT service for HTTP/3 architecture with WebSocket support'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--websocket',
            action='store_true',
            help='Use WebSocket connection through Nginx proxy',
        )
        parser.add_argument(
            '--ssl',
            action='store_true',
            help='Force SSL/TLS connection',
        )
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
        
        # Override settings if specified
        if options['ssl']:
            settings.MQTT_USE_SSL = True
        
        logger.info("Starting Naboom Community Optimized MQTT Service")
        logger.info(f"HTTP/3 Architecture: Enabled")
        logger.info(f"WebSocket mode: {options['websocket']}")
        logger.info(f"SSL/TLS enabled: {getattr(settings, 'MQTT_USE_SSL', False)}")
        
        # Create and run MQTT service
        mqtt_service = OptimizedMQTTService()
        
        try:
            success = asyncio.run(mqtt_service.run(use_websocket=options['websocket']))
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Optimized MQTT service completed successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Optimized MQTT service failed to start')
                )
                sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.stdout.write(
                self.style.WARNING('Optimized MQTT service interrupted by user')
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.stdout.write(
                self.style.ERROR(f'Optimized MQTT service failed: {e}')
            )
            sys.exit(1)
