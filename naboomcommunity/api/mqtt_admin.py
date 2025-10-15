"""
Django Admin Integration for MQTT Monitoring

This module provides Django admin interface for monitoring MQTT service health,
viewing metrics, and managing MQTT service configuration.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings

from .mqtt_health import health_tracker, MQTTHealthMetrics


class MQTTServiceAdmin(admin.ModelAdmin):
    """
    Django Admin interface for MQTT service monitoring.
    
    This admin interface provides:
    - Real-time MQTT service status
    - Health metrics dashboard
    - Service configuration management
    - Alert management
    """
    
    list_display = [
        'get_status_badge',
        'get_connection_status',
        'get_uptime',
        'get_messages_processed',
        'get_messages_per_minute',
        'get_error_count',
        'get_last_activity',
        'get_actions'
    ]
    
    list_filter = ['status']
    
    search_fields = ['client_id', 'broker_host']
    
    readonly_fields = [
        'status',
        'connected',
        'uptime',
        'messages_processed',
        'messages_per_minute',
        'subscribed_topics',
        'last_activity',
        'connection_retries',
        'error_count',
        'last_error',
        'broker_host',
        'broker_port',
        'client_id',
        'keepalive'
    ]
    
    fieldsets = (
        ('Service Status', {
            'fields': ('status', 'connected', 'uptime', 'last_activity')
        }),
        ('Performance Metrics', {
            'fields': ('messages_processed', 'messages_per_minute', 'connection_retries')
        }),
        ('Error Tracking', {
            'fields': ('error_count', 'last_error')
        }),
        ('Connection Details', {
            'fields': ('broker_host', 'broker_port', 'client_id', 'keepalive')
        }),
        ('Subscriptions', {
            'fields': ('subscribed_topics',)
        }),
    )
    
    def get_urls(self):
        """Add custom URLs for MQTT monitoring."""
        urls = super().get_urls()
        custom_urls = [
            path('mqtt-dashboard/', self.admin_site.admin_view(self.mqtt_dashboard), name='mqtt_dashboard'),
            path('mqtt-health-json/', self.admin_site.admin_view(self.mqtt_health_json), name='mqtt_health_json'),
            path('mqtt-metrics-json/', self.admin_site.admin_view(self.mqtt_metrics_json), name='mqtt_metrics_json'),
        ]
        return custom_urls + urls
    
    def get_status_badge(self, obj):
        """Display status as a colored badge."""
        metrics = health_tracker.get_health_metrics()
        status = self._determine_health_status(metrics)
        
        color_map = {
            'healthy': 'green',
            'degraded': 'orange',
            'unhealthy': 'red',
            'error': 'red'
        }
        
        color = color_map.get(status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            status.upper()
        )
    get_status_badge.short_description = 'Status'
    
    def get_connection_status(self, obj):
        """Display connection status."""
        metrics = health_tracker.get_health_metrics()
        if metrics.connected:
            return format_html('<span style="color: green;">✓ Connected</span>')
        else:
            return format_html('<span style="color: red;">✗ Disconnected</span>')
    get_connection_status.short_description = 'Connection'
    
    def get_uptime(self, obj):
        """Display service uptime."""
        metrics = health_tracker.get_health_metrics()
        return self._format_uptime(metrics.uptime)
    get_uptime.short_description = 'Uptime'
    
    def get_messages_processed(self, obj):
        """Display total messages processed."""
        metrics = health_tracker.get_health_metrics()
        return f"{metrics.messages_processed:,}"
    get_messages_processed.short_description = 'Messages'
    
    def get_messages_per_minute(self, obj):
        """Display messages per minute rate."""
        metrics = health_tracker.get_health_metrics()
        return f"{metrics.messages_per_minute:.2f}"
    get_messages_per_minute.short_description = 'Msg/Min'
    
    def get_error_count(self, obj):
        """Display error count with color coding."""
        metrics = health_tracker.get_health_metrics()
        if metrics.error_count == 0:
            return format_html('<span style="color: green;">0</span>')
        elif metrics.error_count < 5:
            return format_html('<span style="color: orange;">{}</span>', metrics.error_count)
        else:
            return format_html('<span style="color: red;">{}</span>', metrics.error_count)
    get_error_count.short_description = 'Errors'
    
    def get_last_activity(self, obj):
        """Display last activity time."""
        metrics = health_tracker.get_health_metrics()
        if metrics.last_activity:
            return metrics.last_activity.strftime('%Y-%m-%d %H:%M:%S')
        return 'Never'
    get_last_activity.short_description = 'Last Activity'
    
    def get_actions(self, obj):
        """Display action buttons."""
        return format_html(
            '<a class="button" href="{}">Dashboard</a> '
            '<a class="button" href="{}">Health JSON</a> '
            '<a class="button" href="{}">Metrics JSON</a>',
            reverse('admin:mqtt_dashboard'),
            reverse('admin:mqtt_health_json'),
            reverse('admin:mqtt_metrics_json')
        )
    get_actions.short_description = 'Actions'
    
    def mqtt_dashboard(self, request):
        """Render MQTT monitoring dashboard."""
        metrics = health_tracker.get_health_metrics()
        context = {
            'title': 'MQTT Service Dashboard',
            'metrics': metrics,
            'health_status': self._determine_health_status(metrics),
            'uptime_formatted': self._format_uptime(metrics.uptime),
            'time_since_activity': self._get_time_since_activity(metrics.last_activity),
        }
        return render(request, 'admin/mqtt_dashboard.html', context)
    
    def mqtt_health_json(self, request):
        """Return MQTT health data as JSON."""
        metrics = health_tracker.get_health_metrics()
        health_status = self._determine_health_status(metrics)
        
        data = {
            'status': health_status,
            'timestamp': timezone.now().isoformat(),
            'connected': metrics.connected,
            'uptime': metrics.uptime,
            'uptime_formatted': self._format_uptime(metrics.uptime),
            'messages_processed': metrics.messages_processed,
            'messages_per_minute': metrics.messages_per_minute,
            'connection_retries': metrics.connection_retries,
            'error_count': metrics.error_count,
            'last_error': metrics.last_error,
            'subscribed_topics': metrics.subscribed_topics,
            'last_activity': metrics.last_activity.isoformat() if metrics.last_activity else None,
            'broker_host': metrics.broker_host,
            'broker_port': metrics.broker_port,
            'client_id': metrics.client_id,
            'keepalive': metrics.keepalive,
        }
        
        return JsonResponse(data)
    
    def mqtt_metrics_json(self, request):
        """Return MQTT metrics data as JSON."""
        metrics = health_tracker.get_health_metrics()
        
        data = {
            'timestamp': timezone.now().isoformat(),
            'uptime': {
                'seconds': metrics.uptime,
                'formatted': self._format_uptime(metrics.uptime),
            },
            'performance': {
                'messages_processed': metrics.messages_processed,
                'messages_per_minute': metrics.messages_per_minute,
                'messages_per_hour': metrics.messages_per_minute * 60,
            },
            'reliability': {
                'connection_retries': metrics.connection_retries,
                'error_count': metrics.error_count,
                'error_rate_percent': (metrics.error_count / max(metrics.messages_processed, 1)) * 100,
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
                'time_since_activity': self._get_time_since_activity(metrics.last_activity),
            }
        }
        
        return JsonResponse(data)
    
    def _determine_health_status(self, metrics: MQTTHealthMetrics) -> str:
        """Determine overall health status based on metrics."""
        if not metrics.connected:
            return 'unhealthy'
        
        if metrics.error_count > 10:
            return 'degraded'
        
        if metrics.last_activity:
            time_since_activity = (timezone.now() - metrics.last_activity).total_seconds()
            if time_since_activity > 300:  # 5 minutes
                return 'degraded'
        
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
    
    def _get_time_since_activity(self, last_activity) -> str:
        """Get human-readable time since last activity."""
        if not last_activity:
            return 'Never'
        
        time_diff = timezone.now() - last_activity
        total_seconds = int(time_diff.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        else:
            hours = total_seconds // 3600
            return f"{hours}h ago"


# Register the admin interface
admin.site.register(type('MQTTService', (), {}), MQTTServiceAdmin)
