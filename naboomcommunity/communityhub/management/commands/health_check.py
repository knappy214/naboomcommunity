"""Health check command for HTTP/3 optimized services."""
import os
import django
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import psutil
import redis
import logging

# Configure logging to console only
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check health of all HTTP/3 optimized services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed health information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        health_status = {
            'overall': 'healthy',
            'services': {},
            'metrics': {}
        }

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['services']['database'] = 'healthy'
        except Exception as e:
            health_status['services']['database'] = f'unhealthy: {e}'
            health_status['overall'] = 'unhealthy'

        # Check Redis cache using Django cache
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health_status['services']['redis_cache'] = 'healthy'
            else:
                health_status['services']['redis_cache'] = 'unhealthy'
        except Exception as e:
            health_status['services']['redis_cache'] = f'unhealthy: {e}'
            health_status['overall'] = 'unhealthy'

        # Check Redis broker using direct connection
        try:
            broker_url = settings.CELERY_BROKER_URL
            r = redis.from_url(broker_url)
            r.ping()
            health_status['services']['redis_broker'] = 'healthy'
        except Exception as e:
            health_status['services']['redis_broker'] = f'unhealthy: {e}'
            health_status['overall'] = 'unhealthy'

        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['metrics'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
            }
            
            # Check if resources are within limits
            if cpu_percent > 90:
                health_status['overall'] = 'degraded'
                health_status['services']['cpu'] = f'high usage: {cpu_percent}%'
            
            if memory.percent > 90:
                health_status['overall'] = 'degraded'
                health_status['services']['memory'] = f'high usage: {memory.percent}%'
                
            if disk.percent > 90:
                health_status['overall'] = 'unhealthy'
                health_status['services']['disk'] = f'high usage: {disk.percent}%'
                
        except Exception as e:
            health_status['services']['system_resources'] = f'error: {e}'

        # Check Celery workers
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            if active_workers:
                health_status['services']['celery_workers'] = f'healthy: {len(active_workers)} workers'
            else:
                health_status['services']['celery_workers'] = 'unhealthy: no active workers'
                health_status['overall'] = 'unhealthy'
        except Exception as e:
            health_status['services']['celery_workers'] = f'error: {e}'

        # Check WebSocket channels
        try:
            from channels.layers import get_channel_layer
            layer = get_channel_layer()
            if layer:
                health_status['services']['websocket_channels'] = 'healthy'
            else:
                health_status['services']['websocket_channels'] = 'unhealthy'
        except Exception as e:
            health_status['services']['websocket_channels'] = f'error: {e}'

        # Output results
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f"Overall Status: {health_status['overall'].upper()}")
            )
            for service, status in health_status['services'].items():
                color = self.style.SUCCESS if 'healthy' in status else self.style.ERROR
                self.stdout.write(f"{service}: {color(status)}")
            
            if health_status['metrics']:
                self.stdout.write("\nSystem Metrics:")
                for metric, value in health_status['metrics'].items():
                    self.stdout.write(f"  {metric}: {value}")
        else:
            # Simple output for monitoring
            self.stdout.write(health_status['overall'])

        return health_status['overall']
