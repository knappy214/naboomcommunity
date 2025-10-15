"""
Production settings for naboomcommunity project.
Optimized for HTTP/3 and high-performance deployment.
"""

from .base import *
from urllib.parse import quote_plus

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

DEBUG = False
ALLOWED_HOSTS = ['naboomneighbornet.net.za', 'www.naboomneighbornet.net.za']

# Enhanced security for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL configuration with enhanced connection pooling for emergency response system
# Inherits optimized settings from base.py with production-specific overrides
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME', 'naboomcommunity'),
        'USER': os.getenv('DB_USER', 'naboom_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
        # Enhanced connection pooling for production emergency response system
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL in production
            'connect_timeout': 10,
            # Temporarily disable connection pooling to fix Celery Beat issues
            # 'pool': {
            #     'min_size': 10,  # Higher minimum for production load
            #     'max_size': 50,  # Higher maximum for emergency response capacity
            #     'timeout': 20,   # Longer timeout for production stability
            #     'max_lifetime': 3600,  # Connection lifetime in seconds
            #     'max_idle': 300,  # Max idle time before connection cleanup
            # },
            # PostgreSQL production optimizations
            'application_name': 'naboom_emergency_system_prod',
            'keepalives_idle': '600',
            'keepalives_interval': '30', 
            'keepalives_count': '3',
        }
    }
}

# ============================================================================
# REDIS CONFIGURATION - USING EXISTING OPTIMIZED SETUP
# ============================================================================

# Load Redis credentials with username mapping
redis_users = {
    'REDIS_MASTER_PASSWORD': {'user': 'default', 'password': 'O9sHIXiVKXHIe14DLJ0kkHKwpjf2PghaO9Y+f6WfFr4='},
    'DJANGO_APP_PASSWORD': {'user': 'app_user', 'password': 'YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY'},
    'WEBSOCKET_PASSWORD': {'user': 'websocket_user', 'password': 'QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM'},
    'REALTIME_PASSWORD': {'user': 'realtime_user', 'password': 'LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z'},
    'MONITORING_PASSWORD': {'user': 'monitoring_user', 'password': 'cYzwdiPoN4taA1jBwFJZqhbQAuUR1ykb'},
    # Emergency Response Redis Users (Databases 8, 9, 10)
    'EMERGENCY_DB8_PASSWORD': {'user': 'emergency_db8_user', 'password': 'YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY'},
    'EMERGENCY_DB9_PASSWORD': {'user': 'emergency_db9_user', 'password': 'QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM'},
    'EMERGENCY_DB10_PASSWORD': {'user': 'emergency_db10_user', 'password': 'LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z'},
}

# Redis caching with HTTP/3 optimizations
# Use environment variables for Redis authentication (from systemd service)
redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
redis_port = os.getenv('REDIS_PORT', '6379')
redis_password = os.getenv('REDIS_PASSWORD', '')
redis_user = os.getenv('REDIS_USER', '')

# Build Redis URL with authentication from environment variables
if redis_user and redis_password:
    redis_url = f"redis://{redis_user}:{quote_plus(redis_password)}@{redis_host}:{redis_port}/0"
elif redis_password:
    redis_url = f"redis://:{quote_plus(redis_password)}@{redis_host}:{redis_port}/0"
else:
    redis_url = f"redis://{redis_host}:{redis_port}/0"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': redis_url,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,  # HTTP/3 optimized
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'naboom',
        'TIMEOUT': 300,
        'VERSION': 1,
    },
    # Emergency Response Caching - Database 8
    'emergency_location': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["EMERGENCY_DB8_PASSWORD"]["user"]}:{quote_plus(redis_users["EMERGENCY_DB8_PASSWORD"]["password"])}@127.0.0.1:6379/8',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,  # High concurrency for location data
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'emergency_location',
        'TIMEOUT': 60,  # Short timeout for real-time location data
        'VERSION': 1,
    },
    # Emergency Medical Data Caching - Database 9
    'emergency_medical': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["EMERGENCY_DB9_PASSWORD"]["user"]}:{quote_plus(redis_users["EMERGENCY_DB9_PASSWORD"]["password"])}@127.0.0.1:6379/9',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,  # Moderate concurrency for medical data
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'emergency_medical',
        'TIMEOUT': 3600,  # Longer timeout for medical data
        'VERSION': 1,
    },
    # Emergency Notifications Caching - Database 10
    'emergency_notifications': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["EMERGENCY_DB10_PASSWORD"]["user"]}:{quote_plus(redis_users["EMERGENCY_DB10_PASSWORD"]["password"])}@127.0.0.1:6379/10',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 75,  # High concurrency for notifications
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'emergency_notifications',
        'TIMEOUT': 1800,  # Medium timeout for notification data
        'VERSION': 1,
    },
    # Emergency Rate Limiting Cache
    'emergency_rate_limit': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["EMERGENCY_DB8_PASSWORD"]["user"]}:{quote_plus(redis_users["EMERGENCY_DB8_PASSWORD"]["password"])}@127.0.0.1:6379/8',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 200,  # Very high concurrency for rate limiting
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': None,  # No compression for rate limiting data
            'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
        },
        'KEY_PREFIX': 'emergency_rate_limit',
        'TIMEOUT': 300,  # Short timeout for rate limiting data
        'VERSION': 1,
    },
    # Emergency WebSocket Cache
    'emergency_websocket': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["EMERGENCY_DB9_PASSWORD"]["user"]}:{quote_plus(redis_users["EMERGENCY_DB9_PASSWORD"]["password"])}@127.0.0.1:6379/9',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 150,  # High concurrency for WebSocket data
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'emergency_websocket',
        'TIMEOUT': 30,  # Very short timeout for WebSocket data
        'VERSION': 1,
    },
}

# ============================================================================
# CELERY CONFIGURATION - HTTP/3 OPTIMIZED
# ============================================================================

# Enhanced Celery configuration for HTTP/3 performance
CELERY_BROKER_URL = f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/2'
CELERY_RESULT_BACKEND = f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/2'

# Celery Beat configuration to prevent database connection pool issues
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE_FILENAME = '/var/run/celery/beat-schedule'


# HTTP/3 Celery optimizations
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Aligned with systemd config
CELERY_WORKER_CONCURRENCY = 6  # Aligned with systemd config
CELERY_WORKER_POOL = 'prefork'
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_DISABLE_RATE_LIMITS = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True

# HTTP/3 specific optimizations
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
CELERY_TASK_IGNORE_RESULT = False
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_TASK_DEFAULT_RETRY_DELAY = 60
CELERY_TASK_MAX_RETRIES = 3

# Task routing for HTTP/3 optimization
CELERY_TASK_ROUTES = {
    'communityhub.tasks.fan_out_alert': {
        'queue': 'community-alerts',
        'routing_key': 'community.alert',
        'priority': 5,
    },
    'communityhub.tasks.*': {
        'queue': 'community-tasks',
        'routing_key': 'community.task',
        'priority': 3,
    },
    # Emergency Response Task Routing
    'panic.tasks.emergency_*': {
        'queue': 'emergency-high-priority',
        'routing_key': 'emergency.high',
        'priority': 10,
    },
    'panic.tasks.location_*': {
        'queue': 'emergency-location',
        'routing_key': 'emergency.location',
        'priority': 8,
    },
    'panic.tasks.medical_*': {
        'queue': 'emergency-medical',
        'routing_key': 'emergency.medical',
        'priority': 9,
    },
    'panic.tasks.notification_*': {
        'queue': 'emergency-notifications',
        'routing_key': 'emergency.notification',
        'priority': 7,
    },
    'panic.tasks.sync_*': {
        'queue': 'emergency-sync',
        'routing_key': 'emergency.sync',
        'priority': 6,
    },
}

# ============================================================================
# DJANGO CHANNELS CONFIGURATION - HTTP/3 OPTIMIZED
# ============================================================================

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [{
                'address': ('127.0.0.1', 6379),
                'db': 1,  # DB 1: Channels Layer
                'username': redis_users['WEBSOCKET_PASSWORD']['user'],
                'password': redis_users['WEBSOCKET_PASSWORD']['password'],
            }],
            'capacity': 16000,  # Doubled for HTTP/3 concurrent connections
            'expiry': 30,  # Reduced for better memory usage
            'group_expiry': 3600,  # 1 hour
            'symmetric_encryption_keys': [SECRET_KEY],
            'channel_capacity': {
                'http.request': 2000,
                'http.response': 2000,
                'websocket.connect': 2000,
                'websocket.receive': 2000,
                'websocket.disconnect': 2000,
            },
        },
    },
}

# ============================================================================
# HTTP/3 SPECIFIC OPTIMIZATIONS
# ============================================================================

# HTTP/3 connection optimizations
CONN_MAX_AGE = 600  # 10 minutes
CONN_HEALTH_CHECKS = True

# Template optimizations for HTTP/3
TEMPLATES[0]['APP_DIRS'] = False  # Disable APP_DIRS when using custom loaders
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Static files optimization
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Session optimization for HTTP/3
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Simplified logging configuration to avoid file permission issues with Celery
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'naboomcommunity': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'communityhub': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# PERFORMANCE OPTIMIZATIONS
# ============================================================================

# Database query optimization
DATABASE_ROUTERS = []

# Enhanced database performance monitoring for emergency response system
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG' if DEBUG else 'INFO',
    'propagate': False,
}

# Database query performance monitoring
if not DEBUG:
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['console'],
        'level': 'WARNING',  # Only log slow queries in production
        'propagate': False,
    }

# Cache optimization with emergency response system tuning
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'naboom'

# Enhanced Redis configuration for emergency response system
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'].update({
    'max_connections': 1000,  # Increased for emergency response load
    'retry_on_timeout': True,
    'socket_keepalive': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'health_check_interval': 30,  # Health check every 30 seconds
})

# File upload optimization
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Email optimization
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

# ============================================================================
# MONITORING AND HEALTH CHECKS
# ============================================================================

# Health check endpoint
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,  # in MB
}

# ============================================================================
# HTTP/3 SPECIFIC MIDDLEWARE
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',  # HTTP/3 optimization
    'django.middleware.gzip.GZipMiddleware',  # HTTP/3 optimization
]

# ============================================================================
# WAGTAIL CONFIGURATION
# ============================================================================

WAGTAIL_SITE_NAME = "Naboom Community"
WAGTAILADMIN_BASE_URL = "https://naboomneighbornet.net.za"

# ============================================================================
# EMERGENCY STORAGE CONFIGURATION
# ============================================================================

# Emergency-specific MinIO storage configuration
EMERGENCY_STORAGE_BUCKET_NAME = os.getenv('EMERGENCY_STORAGE_BUCKET_NAME', 'naboom-emergency-media')
EMERGENCY_STORAGE_ENDPOINT_URL = os.getenv('EMERGENCY_STORAGE_ENDPOINT_URL', 'https://s3.naboomneighbornet.net.za')
EMERGENCY_STORAGE_CUSTOM_DOMAIN = os.getenv('EMERGENCY_STORAGE_CUSTOM_DOMAIN', 's3.naboomneighbornet.net.za')

# Emergency storage settings
EMERGENCY_STORAGE_SETTINGS = {
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID', 'immunothreat'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY', 'INikbgTflu34yWjJHZYi'),
    'AWS_STORAGE_BUCKET_NAME': EMERGENCY_STORAGE_BUCKET_NAME,
    'AWS_S3_ENDPOINT_URL': EMERGENCY_STORAGE_ENDPOINT_URL,
    'AWS_S3_CUSTOM_DOMAIN': EMERGENCY_STORAGE_CUSTOM_DOMAIN,
    'AWS_DEFAULT_ACL': 'private',  # Emergency files should be private
    'AWS_S3_FILE_OVERWRITE': False,
    'AWS_QUERYSTRING_AUTH': True,  # Use signed URLs for security
    'AWS_S3_REGION_NAME': os.getenv('AWS_S3_REGION_NAME', 'us-east-1'),
    'AWS_S3_OBJECT_PARAMETERS': {
        'CacheControl': 'max-age=3600',  # 1 hour cache for emergency files
        'ContentDisposition': 'attachment',  # Force download for security
    },
}

# Emergency media URL configuration
EMERGENCY_MEDIA_URL = f"{EMERGENCY_STORAGE_ENDPOINT_URL}/{EMERGENCY_STORAGE_BUCKET_NAME}/emergency/"

# ============================================================================
# FINAL CONFIGURATION
# ============================================================================

# Ensure all settings are properly configured
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'Africa/Johannesburg'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

# Admin configuration (inherits from base.py but can be overridden)
LOGIN_REDIRECT_URL = '/django-admin/'
LOGIN_URL = '/django-admin/login/'
ADMIN_URL = '/django-admin/'
