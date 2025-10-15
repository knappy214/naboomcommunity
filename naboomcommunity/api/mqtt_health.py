"""
MQTT Health Check and Monitoring System

This module provides comprehensive health monitoring for the MQTT service,
including connection status, metrics collection, and health check endpoints.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from django.core.cache import cache
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)


@dataclass
class MQTTHealthMetrics:
    """Data class for MQTT health metrics."""
    connected: bool
    uptime: float
    messages_processed: int
    messages_per_minute: float
    subscribed_topics: List[str]
    last_activity: Optional[datetime]
    connection_retries: int
    error_count: int
    last_error: Optional[str]
    broker_host: str
    broker_port: int
    client_id: str
    keepalive: int


class MQTTHealthTracker:
    """Singleton class to track MQTT service health and metrics."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.start_time = time.time()
            self.message_count = 0
            self.connection_retries = 0
            self.error_count = 0
            self.last_error = None
            self.last_activity = None
            self.connected = False
            self.subscribed_topics = []
            self.broker_host = getattr(settings, 'MQTT_HOST', 'localhost')
            self.broker_port = getattr(settings, 'MQTT_PORT', 1883)
            self.client_id = getattr(settings, 'MQTT_CLIENT_ID', 'naboom-community')
            self.keepalive = getattr(settings, 'MQTT_KEEPALIVE', 60)
            self._initialized = True
    
    def update_connection_status(self, connected: bool):
        """Update MQTT connection status."""
        self.connected = connected
        if connected:
            self.last_activity = datetime.now(timezone.utc)
        self._cache_metrics()
    
    def increment_message_count(self):
        """Increment processed message count."""
        self.message_count += 1
        self.last_activity = datetime.now(timezone.utc)
        self._cache_metrics()
    
    def increment_connection_retries(self):
        """Increment connection retry count."""
        self.connection_retries += 1
        self._cache_metrics()
    
    def record_error(self, error_message: str):
        """Record an error occurrence."""
        self.error_count += 1
        self.last_error = error_message
        self._cache_metrics()
        logger.error(f"MQTT Error: {error_message}")
    
    def update_subscribed_topics(self, topics: List[str]):
        """Update list of subscribed topics."""
        self.subscribed_topics = topics
        self._cache_metrics()
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self.start_time
    
    def get_messages_per_minute(self) -> float:
        """Calculate messages processed per minute."""
        uptime_minutes = self.get_uptime() / 60
        return self.message_count / uptime_minutes if uptime_minutes > 0 else 0.0
    
    def get_health_metrics(self) -> MQTTHealthMetrics:
        """Get comprehensive health metrics."""
        return MQTTHealthMetrics(
            connected=self.connected,
            uptime=self.get_uptime(),
            messages_processed=self.message_count,
            messages_per_minute=self.get_messages_per_minute(),
            subscribed_topics=self.subscribed_topics.copy(),
            last_activity=self.last_activity,
            connection_retries=self.connection_retries,
            error_count=self.error_count,
            last_error=self.last_error,
            broker_host=self.broker_host,
            broker_port=self.broker_port,
            client_id=self.client_id,
            keepalive=self.keepalive
        )
    
    def _cache_metrics(self):
        """Cache metrics in Django cache for quick access."""
        metrics = self.get_health_metrics()
        cache.set('mqtt_health_metrics', asdict(metrics), timeout=300)  # 5 minutes
    
    def get_cached_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cached metrics from Django cache."""
        return cache.get('mqtt_health_metrics')


# Global health tracker instance
health_tracker = MQTTHealthTracker()


class MQTTHealthView(APIView):
    """
    MQTT Health Check API View
    
    Provides comprehensive health status and metrics for the MQTT service.
    This endpoint can be used by monitoring systems, load balancers, and
    operational dashboards to check MQTT service health.
    """
    
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    
    def get(self, request, format=None):
        """
        Return MQTT service health status and metrics.
        
        Returns:
            Response: JSON response containing health status, connection info,
                     metrics, and service details.
        """
        try:
            # Get current health metrics
            metrics = health_tracker.get_health_metrics()
            
            # Determine overall health status
            health_status = self._determine_health_status(metrics)
            
            # Prepare response data
            response_data = {
                'status': health_status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'mqtt',
                'version': '1.0.0',
                'connected': metrics.connected,
                'uptime_seconds': round(metrics.uptime, 2),
                'uptime_human': self._format_uptime(metrics.uptime),
                'metrics': {
                    'messages_processed': metrics.messages_processed,
                    'messages_per_minute': round(metrics.messages_per_minute, 2),
                    'connection_retries': metrics.connection_retries,
                    'error_count': metrics.error_count,
                    'last_error': metrics.last_error,
                },
                'connection': {
                    'broker_host': metrics.broker_host,
                    'broker_port': metrics.broker_port,
                    'client_id': metrics.client_id,
                    'keepalive': metrics.keepalive,
                },
                'subscriptions': {
                    'topics': metrics.subscribed_topics,
                    'count': len(metrics.subscribed_topics),
                },
                'activity': {
                    'last_activity': metrics.last_activity.isoformat() if metrics.last_activity else None,
                    'time_since_last_activity': self._get_time_since_activity(metrics.last_activity),
                }
            }
            
            # Set appropriate HTTP status code based on health
            http_status = self._get_http_status(health_status)
            
            return Response(response_data, status=http_status)
            
        except Exception as e:
            logger.error(f"Error in MQTT health check: {e}")
            return Response(
                {
                    'status': 'error',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'error': str(e),
                    'service': 'mqtt'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _determine_health_status(self, metrics: MQTTHealthMetrics) -> str:
        """
        Determine overall health status based on metrics.
        
        Returns:
            str: 'healthy', 'degraded', or 'unhealthy'
        """
        if not metrics.connected:
            return 'unhealthy'
        
        # Check for high error rate
        if metrics.error_count > 10:
            return 'degraded'
        
        # Check for recent activity (within last 5 minutes)
        if metrics.last_activity:
            time_since_activity = (datetime.now(timezone.utc) - metrics.last_activity).total_seconds()
            if time_since_activity > 300:  # 5 minutes
                return 'degraded'
        
        # Check for excessive connection retries
        if metrics.connection_retries > 5:
            return 'degraded'
        
        return 'healthy'
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format."""
        if uptime_seconds < 60:
            return f"{int(uptime_seconds)}s"
        elif uptime_seconds < 3600:
            minutes = int(uptime_seconds // 60)
            seconds = int(uptime_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _get_time_since_activity(self, last_activity: Optional[datetime]) -> Optional[str]:
        """Get human-readable time since last activity."""
        if not last_activity:
            return None
        
        time_diff = datetime.now(timezone.utc) - last_activity
        total_seconds = int(time_diff.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        else:
            hours = total_seconds // 3600
            return f"{hours}h ago"
    
    def _get_http_status(self, health_status: str) -> int:
        """Get appropriate HTTP status code for health status."""
        if health_status == 'healthy':
            return status.HTTP_200_OK
        elif health_status == 'degraded':
            return status.HTTP_200_OK  # Still operational but with warnings
        else:  # unhealthy
            return status.HTTP_503_SERVICE_UNAVAILABLE


class MQTTMetricsView(APIView):
    """
    MQTT Metrics API View
    
    Provides detailed metrics and statistics for the MQTT service.
    This endpoint is useful for monitoring dashboards and analytics.
    """
    
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    
    def get(self, request, format=None):
        """
        Return detailed MQTT service metrics.
        
        Returns:
            Response: JSON response containing detailed metrics and statistics.
        """
        try:
            metrics = health_tracker.get_health_metrics()
            
            # Calculate additional metrics
            uptime_hours = metrics.uptime / 3600
            error_rate = (metrics.error_count / max(metrics.messages_processed, 1)) * 100
            
            response_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'mqtt',
                'uptime': {
                    'seconds': round(metrics.uptime, 2),
                    'hours': round(uptime_hours, 2),
                    'human': self._format_uptime(metrics.uptime),
                },
                'performance': {
                    'messages_processed': metrics.messages_processed,
                    'messages_per_minute': round(metrics.messages_per_minute, 2),
                    'messages_per_hour': round(metrics.messages_per_minute * 60, 2),
                },
                'reliability': {
                    'connection_retries': metrics.connection_retries,
                    'error_count': metrics.error_count,
                    'error_rate_percent': round(error_rate, 2),
                    'last_error': metrics.last_error,
                },
                'connection': {
                    'status': 'connected' if metrics.connected else 'disconnected',
                    'broker': f"{metrics.broker_host}:{metrics.broker_port}",
                    'client_id': metrics.client_id,
                    'keepalive': metrics.keepalive,
                },
                'subscriptions': {
                    'topics': metrics.subscribed_topics,
                    'count': len(metrics.subscribed_topics),
                },
                'activity': {
                    'last_activity': metrics.last_activity.isoformat() if metrics.last_activity else None,
                    'time_since_last_activity': self._get_time_since_activity(metrics.last_activity),
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in MQTT metrics: {e}")
            return Response(
                {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'error': str(e),
                    'service': 'mqtt'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format."""
        if uptime_seconds < 60:
            return f"{int(uptime_seconds)}s"
        elif uptime_seconds < 3600:
            minutes = int(uptime_seconds // 60)
            seconds = int(uptime_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _get_time_since_activity(self, last_activity: Optional[datetime]) -> Optional[str]:
        """Get human-readable time since last activity."""
        if not last_activity:
            return None
        
        time_diff = datetime.now(timezone.utc) - last_activity
        total_seconds = int(time_diff.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        else:
            hours = total_seconds // 3600
            return f"{hours}h ago"
