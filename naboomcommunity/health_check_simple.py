#!/usr/bin/env python3
"""Simple health check for HTTP/3 optimized services."""
import os
import sys
import django
import psutil
import redis
from urllib.parse import quote_plus

# Add the project directory to Python path
sys.path.insert(0, '/var/www/naboomcommunity/naboomcommunity')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naboomcommunity.settings.production')

# Configure Django
django.setup()

from django.core.cache import cache
from django.db import connection
from django.conf import settings

def check_health():
    """Check health of all services."""
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

    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['services']['redis_cache'] = 'healthy'
        else:
            health_status['services']['redis_cache'] = 'unhealthy'
    except Exception as e:
        health_status['services']['redis_cache'] = f'unhealthy: {e}'
        health_status['overall'] = 'unhealthy'

    # Check Redis broker
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

    return health_status

if __name__ == '__main__':
    health = check_health()
    
    print(f"Overall Status: {health['overall'].upper()}")
    for service, status in health['services'].items():
        print(f"{service}: {status}")
    
    if health['metrics']:
        print("\nSystem Metrics:")
        for metric, value in health['metrics'].items():
            print(f"  {metric}: {value}")
    
    # Exit with appropriate code
    if health['overall'] == 'healthy':
        sys.exit(0)
    elif health['overall'] == 'degraded':
        sys.exit(1)
    else:
        sys.exit(2)
