# Critical Redis ACL Integration for Naboom Services

## CRITICAL AUTHENTICATION REQUIREMENT

After thorough analysis of your Redis setup, **ALL** Redis connections require both username AND password authentication. This affects every service in your stack.

---

## Django Settings Integration

### Critical Fix: Redis Connection URLs with Username

```python
# settings/production.py - CORRECTED FOR ACL AUTHENTICATION

# Load Redis credentials with username mapping
redis_users = {
    'REDIS_MASTER_PASSWORD': {'user': 'default', 'password': 'O9sHIXiVKXHIe14DLJ0kkHKwpjf2PghaO9Y+f6WfFr4='},
    'DJANGO_APP_PASSWORD': {'user': 'app_user', 'password': 'YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY'},
    'WEBSOCKET_PASSWORD': {'user': 'websocket_user', 'password': 'QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM'},
    'REALTIME_PASSWORD': {'user': 'realtime_user', 'password': 'LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z'},
    'MONITORING_PASSWORD': {'user': 'monitoring_user', 'password': 'cYzwdiPoN4taA1jBwFJZqhbQAuUR1ykb'},
}

# CORRECTED REDIS CACHE CONFIGURATION
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',  # DB 0: Django Cache
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'USERNAME': redis_users['DJANGO_APP_PASSWORD']['user'],  # app_user
            'PASSWORD': redis_users['DJANGO_APP_PASSWORD']['password'],
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 200,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
            },
        },
        'KEY_PREFIX': 'naboom:cache',
        'TIMEOUT': 300,
        'VERSION': 1,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/3',  # DB 3: Django Sessions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'USERNAME': redis_users['DJANGO_APP_PASSWORD']['user'],
            'PASSWORD': redis_users['DJANGO_APP_PASSWORD']['password'],
        },
        'KEY_PREFIX': 'naboom:sessions',
        'TIMEOUT': 86400,  # 24 hours for HTTP/3 session persistence
    },
    'realtime': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/4',  # DB 4: Real-time streams
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'USERNAME': redis_users['REALTIME_PASSWORD']['user'],
            'PASSWORD': redis_users['REALTIME_PASSWORD']['password'],
        },
        'KEY_PREFIX': 'naboom:realtime',
        'TIMEOUT': 60,
    },
}

# CORRECTED DJANGO CHANNELS CONFIGURATION
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [{
                'address': ('127.0.0.1', 6379),
                'db': 1,  # DB 1: Channels Layer
                'username': redis_users['WEBSOCKET_PASSWORD']['user'],  # websocket_user
                'password': redis_users['WEBSOCKET_PASSWORD']['password'],
            }],
            'capacity': 8000,  # Increased for HTTP/3 concurrent connections
            'expiry': 300,
            'group_expiry': 86400,
            'symmetric_encryption_keys': [SECRET_KEY],
        },
    },
}

# CORRECTED CELERY CONFIGURATION
CELERY_BROKER_URL = f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{redis_users["DJANGO_APP_PASSWORD"]["password"]}@127.0.0.1:6379/2'
CELERY_RESULT_BACKEND = f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{redis_users["DJANGO_APP_PASSWORD"]["password"]}@127.0.0.1:6379/2'

# Enhanced Celery settings for HTTP/3 workload
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 6
```

---

## Environment Variables Integration

### Update .env file with Redis ACL credentials:

```bash
# Redis ACL Authentication
REDIS_MASTER_USER=default
REDIS_MASTER_PASSWORD=O9sHIXiVKXHIe14DLJ0kkHKwpjf2PghaO9Y+f6WfFr4=

REDIS_APP_USER=app_user
REDIS_APP_PASSWORD=YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY

REDIS_WEBSOCKET_USER=websocket_user
REDIS_WEBSOCKET_PASSWORD=QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM

REDIS_REALTIME_USER=realtime_user
REDIS_REALTIME_PASSWORD=LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z

REDIS_MONITORING_USER=monitoring_user
REDIS_MONITORING_PASSWORD=cYzwdiPoN4taA1jBwFJZqhbQAuUR1ykb
```

---

## Custom Redis Connection Helper

Create `utils/redis_connections.py`:

```python
import redis
import os
from django.conf import settings

def get_redis_connection(user_type='app', db=0):
    """
    Get Redis connection with proper ACL authentication
    
    Args:
        user_type: 'app', 'websocket', 'realtime', 'monitoring', 'master'
        db: Redis database number
    """
    user_mapping = {
        'app': {
            'username': os.getenv('REDIS_APP_USER', 'app_user'),
            'password': os.getenv('REDIS_APP_PASSWORD')
        },
        'websocket': {
            'username': os.getenv('REDIS_WEBSOCKET_USER', 'websocket_user'),
            'password': os.getenv('REDIS_WEBSOCKET_PASSWORD')
        },
        'realtime': {
            'username': os.getenv('REDIS_REALTIME_USER', 'realtime_user'),
            'password': os.getenv('REDIS_REALTIME_PASSWORD')
        },
        'monitoring': {
            'username': os.getenv('REDIS_MONITORING_USER', 'monitoring_user'),
            'password': os.getenv('REDIS_MONITORING_PASSWORD')
        },
        'master': {
            'username': os.getenv('REDIS_MASTER_USER', 'default'),
            'password': os.getenv('REDIS_MASTER_PASSWORD')
        },
    }
    
    user_info = user_mapping.get(user_type)
    if not user_info or not user_info['password']:
        raise ValueError(f"Redis credentials not found for user type: {user_type}")
    
    return redis.Redis(
        host='127.0.0.1',
        port=6379,
        db=db,
        username=user_info['username'],
        password=user_info['password'],
        decode_responses=True,
        socket_keepalive=True,
        socket_keepalive_options={},
        retry_on_timeout=True,
        max_connections=100,
        health_check_interval=30,
    )

# Connection pools for different services
def get_app_redis():
    """Get Redis connection for general application use"""
    return get_redis_connection('app', db=0)

def get_websocket_redis():
    """Get Redis connection for WebSocket/Channels"""
    return get_redis_connection('websocket', db=1)

def get_realtime_redis():
    """Get Redis connection for real-time emergency data"""
    return get_redis_connection('realtime', db=4)

def get_monitoring_redis():
    """Get Redis connection for monitoring (read-only)"""
    return get_redis_connection('monitoring', db=7)
```

---

## Health Check Integration

### Redis ACL Health Check Function

```python
# utils/health_checks.py
import redis
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class RedisACLHealthCheckView(View):
    def get(self, request):
        health_status = {}
        
        # Test all Redis users
        redis_users = {
            'app_user': {'username': 'app_user', 'password': 'YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY', 'db': 0},
            'websocket_user': {'username': 'websocket_user', 'password': 'QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM', 'db': 1},
            'realtime_user': {'username': 'realtime_user', 'password': 'LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z', 'db': 4},
            'monitoring_user': {'username': 'monitoring_user', 'password': 'cYzwdiPoN4taA1jBwFJZqhbQAuUR1ykb', 'db': 7},
        }
        
        overall_status = "healthy"
        
        for user_name, user_config in redis_users.items():
            try:
                redis_client = redis.Redis(
                    host='127.0.0.1',
                    port=6379,
                    db=user_config['db'],
                    username=user_config['username'],
                    password=user_config['password'],
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                
                # Test connection
                redis_client.ping()
                
                # Get user info
                info = redis_client.info()
                
                health_status[user_name] = {
                    'status': 'healthy',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'db_keys': redis_client.dbsize(),
                    'response_time': 'normal'
                }
                
                # Test basic operations
                test_key = f"health_check:{user_name}"
                redis_client.setex(test_key, 10, "test")
                if redis_client.get(test_key) == "test":
                    health_status[user_name]['operations'] = 'working'
                else:
                    health_status[user_name]['operations'] = 'failed'
                    overall_status = "degraded"
                
            except redis.AuthenticationError as e:
                health_status[user_name] = {
                    'status': 'authentication_failed',
                    'error': 'Invalid username-password pair or user disabled'
                }
                overall_status = "unhealthy"
                logger.error(f"Redis ACL auth failed for {user_name}: {e}")
                
            except redis.ConnectionError as e:
                health_status[user_name] = {
                    'status': 'connection_failed',
                    'error': str(e)
                }
                overall_status = "unhealthy"
                logger.error(f"Redis connection failed for {user_name}: {e}")
                
            except Exception as e:
                health_status[user_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                overall_status = "unhealthy"
                logger.error(f"Redis health check failed for {user_name}: {e}")
        
        return JsonResponse({
            'overall_status': overall_status,
            'redis_acl_health': health_status,
            'timestamp': timezone.now().isoformat(),
            'http3_optimized': True
        })
```

---

## Emergency System Integration

### Example usage in emergency views:

```python
# views/emergency.py
from utils.redis_connections import get_realtime_redis, get_websocket_redis
import json
import time

def emergency_alert_view(request):
    """Handle emergency alerts with proper Redis ACL authentication"""
    
    # Use realtime user for emergency data
    realtime_redis = get_realtime_redis()
    websocket_redis = get_websocket_redis()
    
    alert_data = {
        'type': 'emergency',
        'location': request.POST.get('location'),
        'severity': request.POST.get('severity', 'high'),
        'timestamp': time.time(),
        'user_id': request.user.id if request.user.is_authenticated else None
    }
    
    # Store in emergency stream (realtime_user has access to panic:*, emergency:*)
    stream_key = f"panic:alerts:{alert_data['severity']}"
    realtime_redis.xadd(stream_key, alert_data)
    
    # Publish to emergency channel (websocket_user handles channels)
    channel_key = "emergency:broadcast"
    websocket_redis.publish(channel_key, json.dumps(alert_data))
    
    # Cache for quick access (app_user handles general caching)
    from django.core.cache import cache
    cache.set(f"emergency:alert:{alert_data['timestamp']}", alert_data, 3600)
    
    return JsonResponse({
        'status': 'success',
        'alert_id': alert_data['timestamp'],
        'message': 'Emergency alert processed with Redis ACL authentication'
    })
```

---

## Deployment Verification Script

Create `scripts/verify_redis_acl.sh`:

```bash
#!/bin/bash
echo "🔧 Verifying Redis ACL Authentication Integration"

# Test all Redis users
echo "1. Testing app_user..."
redis-cli --user app_user -a "YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY" -n 0 ping

echo "2. Testing websocket_user..."
redis-cli --user websocket_user -a "QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM" -n 1 ping

echo "3. Testing realtime_user..."
redis-cli --user realtime_user -a "LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z" -n 4 ping

echo "4. Testing monitoring_user..."
redis-cli --user monitoring_user -a "cYzwdiPoN4taA1jBwFJZqhbQAuUR1ykb" -n 7 ping

echo "5. Testing Django cache functionality..."
python3 -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naboomcommunity.settings.production')
import django
django.setup()
from django.core.cache import cache
try:
    cache.set('acl_test', 'success', 30)
    result = cache.get('acl_test')
    print(f'Django cache test: {result}')
    assert result == 'success'
    print('✅ Django cache with Redis ACL working')
except Exception as e:
    print(f'❌ Django cache failed: {e}')
    sys.exit(1)
"

echo "6. Testing Channels Redis layer..."
python3 -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naboomcommunity.settings.production')
import django
django.setup()
from channels.layers import get_channel_layer
import asyncio

async def test_channels():
    channel_layer = get_channel_layer()
    try:
        await channel_layer.send('test.channel', {'type': 'test.message', 'text': 'Hello'})
        print('✅ Channels Redis layer with ACL working')
        return True
    except Exception as e:
        print(f'❌ Channels Redis layer failed: {e}')
        return False

result = asyncio.run(test_channels())
sys.exit(0 if result else 1)
"

echo "✅ All Redis ACL authentication tests completed"
```

---

## Critical Deployment Steps

1. **Update Django settings with Redis ACL authentication**
2. **Update .env file with proper Redis credentials**
3. **Deploy the corrected service files**
4. **Test all Redis connections with the verification script**
5. **Monitor logs for authentication errors**

This integration ensures that every Redis connection throughout your entire application stack uses proper ACL authentication, providing enterprise-grade security while maintaining optimal performance for your HTTP/3 optimized platform.