from .base import *
import os
from datetime import timedelta
from urllib.parse import quote_plus

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

# ============================================================================
# HTTP/3 OPTIMIZED PRODUCTION SETTINGS - WAGTAIL 7.1.1 + DJANGO 5.2
# ============================================================================
# Optimized for Vue frontend and Expo mobile app with HTTP/3 performance
# ============================================================================

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True

# Ensure static files are served correctly
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Production CSRF and security settings
CSRF_TRUSTED_ORIGINS = [
    'https://naboomneighbornet.net.za',
    'https://www.naboomneighbornet.net.za',
    'http://localhost:8081',  # For Expo development
    'http://localhost:3000',  # For development
    'http://localhost:5173',  # For Vue development
]

# Production security headers
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS settings for development and production
CORS_ALLOWED_ORIGINS = [
    "https://naboomneighbornet.net.za",
    "https://www.naboomneighbornet.net.za",
    "http://localhost:8081",  # For Expo development
    "http://localhost:3000",  # For development
    "http://localhost:5173",  # For Vue development
]

# CORS Configuration for authentication
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Set to True only for development
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

# ============================================================================
# HTTP/3 OPTIMIZED MIDDLEWARE STACK
# ============================================================================

# Override MIDDLEWARE to add HTTP/3 optimizations and Wagtail API v2 CORS support
MIDDLEWARE = [
    # HTTP/3 Performance Middleware
    "django.middleware.cache.UpdateCacheMiddleware",  # Must be first for HTTP/3 caching
    "django.middleware.gzip.GZipMiddleware",  # Compression for HTTP/3 efficiency
    "django.middleware.http.ConditionalGetMiddleware",  # ETag/Last-Modified for HTTP/3
    
    # Security and CORS
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "panic.wagtail_cors_middleware.WagtailAPICorsMiddleware",  # Handle CORS for Wagtail API v2
    
    # Session and Locale
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    
    # Common and Rate Limiting
    "django.middleware.common.CommonMiddleware",
    "panic.middleware.VehiclePingRateLimitMiddleware",
    
    # Authentication and CSRF
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # Wagtail and Custom Middleware
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "home.middleware.CSPMiddleware",  # Re-enabled to fix CSP image loading issues
    
    # HTTP/3 Cache Middleware (must be last)
    "django.middleware.cache.FetchFromCacheMiddleware",
]

# ============================================================================
# HTTP/3 OPTIMIZED WAGTAIL API v2 CONFIGURATION
# ============================================================================

# Enhanced Wagtail API v2 settings for HTTP/3 performance
WAGTAILAPI_BASE_URL = "https://naboomneighbornet.net.za"
WAGTAILAPI_SEARCH_ENABLED = True
WAGTAILAPI_LIMIT_MAX = 50  # Increased for HTTP/3 efficiency
WAGTAILAPI_LIMIT_DEFAULT = 20

# HTTP/3 Optimized Wagtail Search Backend
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
        "OPTIONS": {
            "AUTO_UPDATE": True,
            "ATOMIC_REBUILD": True,
        },
    },
}

# HTTP/3 Image Optimization
WAGTAILIMAGES_JPEG_QUALITY = 85
WAGTAILIMAGES_WEBP_QUALITY = 85
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    'bmp': 'jpeg',
    'webp': 'webp',
    'png': 'webp',  # Convert PNG to WebP for HTTP/3 efficiency
}

# HTTP/3 Frontend Cache Configuration
WAGTAILFRONTENDCACHE = {
    'default': {
        'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
        'LOCATION': 'https://s3.naboomneighbornet.net.za',
        'OPTIONS': {
            'TIMEOUT': 300,  # 5 minutes for HTTP/3 efficiency
        },
    },
}

# ============================================================================
# HTTP/3 OPTIMIZED REST FRAMEWORK CONFIGURATION
# ============================================================================

# Enhanced REST Framework settings for HTTP/3 performance
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "community_post_burst": "30/min",  # Increased for HTTP/3
        "community_alert": "2/30min",  # Slightly increased
        "api_general": "1000/hour",  # General API rate limit
        "panic_incident": "10/min",  # Panic incident rate limit
    },
    # HTTP/3 Performance Optimizations
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # HTTP/3 Caching
    "DEFAULT_CACHE_RESPONSE_TIMEOUT": 300,  # 5 minutes
    "DEFAULT_CACHE_KEY_FUNC": "naboomcommunity.utils.cache_key_func",
}

# ============================================================================
# HTTP/3 OPTIMIZED JWT CONFIGURATION
# ============================================================================

# Enhanced JWT settings for HTTP/3 performance
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # Reduced for security
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    # HTTP/3 Performance Optimizations
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
}

# ============================================================================
# HTTP/3 OPTIMIZED CORS CONFIGURATION
# ============================================================================

# Enhanced CORS settings for HTTP/3 performance
CORS_ALLOWED_ORIGINS = [
    "https://naboomneighbornet.net.za",
    "https://www.naboomneighbornet.net.za",
    "http://localhost:8081",  # For Expo development
    "http://localhost:3000",  # For development
    "http://localhost:5173",  # For Vue development
]

# CORS Configuration for authentication
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Set to True only for development
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-http3-active',  # HTTP/3 specific header
    'x-quic-version',  # QUIC version header
]
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
    'x-http3-active',  # HTTP/3 specific header
    'x-quic-version',  # QUIC version header
]

# HTTP/3 CORS optimizations
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours for HTTP/3 efficiency
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
# ============================================================================
# HTTP/3 OPTIMIZED STATIC FILES CONFIGURATION
# ============================================================================

# Enhanced static files configuration for HTTP/3 performance
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# HTTP/3 Optimized File Storage
STORAGES = {
    "default": {
        "BACKEND": "naboomcommunity.custom_storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# HTTP/3 Image Optimization
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    'bmp': 'jpeg',
    'webp': 'webp',
    'png': 'webp',  # Convert PNG to WebP for HTTP/3 efficiency
}

# ============================================================================
# HTTP/3 OPTIMIZED SESSION CONFIGURATION
# ============================================================================

# Enhanced session configuration for HTTP/3 performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = False  # Performance optimization
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============================================================================
# HTTP/3 OPTIMIZED CACHE CONFIGURATION
# ============================================================================

# Per-site cache settings for HTTP/3
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'naboom_http3'

# ============================================================================
# HTTP/3 OPTIMIZED LOGGING CONFIGURATION
# ============================================================================

# Enhanced logging for HTTP/3 performance monitoring
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'http3.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'naboomcommunity': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'wagtail': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ============================================================================
# HTTP/3 OPTIMIZED SECURITY SETTINGS
# ============================================================================

# Enhanced security settings for HTTP/3
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTP/3 specific security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ============================================================================
# HTTP/3 OPTIMIZED PERFORMANCE SETTINGS
# ============================================================================

# Enhanced performance settings for HTTP/3
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# HTTP/3 Connection optimizations
CONN_MAX_AGE = 600  # 10 minutes
CONN_HEALTH_CHECKS = True

# ============================================================================
# HTTP/3 OPTIMIZED EMAIL CONFIGURATION
# ============================================================================

# Enhanced email configuration for HTTP/3
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@naboomneighbornet.net.za')

# ============================================================================
# MQTT CONFIGURATION
# ============================================================================

# MQTT Broker Settings
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'naboom-community')
MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', '60'))

# MQTT Topic Configuration
MQTT_TOPIC_PREFIX = 'naboom'
MQTT_COMMUNITY_TOPIC = f'{MQTT_TOPIC_PREFIX}/community'
MQTT_SYSTEM_TOPIC = f'{MQTT_TOPIC_PREFIX}/system'
MQTT_NOTIFICATION_TOPIC = f'{MQTT_TOPIC_PREFIX}/notifications'

# ============================================================================
# HTTP/3 OPTIMIZED CELERY CONFIGURATION
# ============================================================================

# Load Redis credentials with username mapping
redis_users = {
    'REDIS_MASTER_PASSWORD': {'user': 'default', 'password': 'O9sHIXiVKXHIe14DLJ0kkHKwpjf2PghaO9Y+f6WfFr4='},
    'DJANGO_APP_PASSWORD': {'user': 'app_user', 'password': 'YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY'},
    'WEBSOCKET_PASSWORD': {'user': 'websocket_user', 'password': 'QnBEWsaYvDNOnihFW/sWChAZ81MZc2eM'},
    'REALTIME_PASSWORD': {'user': 'realtime_user', 'password': 'LvxG45/ArFSZVOOrWfzQoYbc+Jc8lB2Z'},
    'MONITORING_PASSWORD': {'user': 'monitoring_user', 'password': 'cYzwdiPoN4taA1jBwFJZqhbQAuUR1ykb'},
}

# Enhanced Celery configuration for HTTP/3 performance
CELERY_BROKER_URL = f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/2'
CELERY_RESULT_BACKEND = f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/2'

# HTTP/3 Celery optimizations
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 8  # Increased for HTTP/3 efficiency
CELERY_WORKER_CONCURRENCY = 8
CELERY_WORKER_POOL = 'prefork'
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_DISABLE_RATE_LIMITS = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================================
# HTTP/3 OPTIMIZED DATABASE CONFIGURATION
# ============================================================================

# Override base database settings with HTTP/3 optimized configuration
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("POSTGRES_DB", "naboomneighbornetdb"),
        "USER": os.getenv("POSTGRES_USER", "naboomneighbornetdb_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "hpG8R0bIQpS@&5yO"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        
        # HTTP/3 Optimized Connection Settings
        "CONN_MAX_AGE": 600,  # 10 minutes for HTTP/3 connection reuse
        "CONN_HEALTH_CHECKS": True,  # Django 5.2 feature
        "ATOMIC_REQUESTS": False,  # Better for HTTP/3 concurrency
        
        # PostgreSQL 16 Performance Optimizations
        "OPTIONS": {
            "sslmode": "prefer",
            "connect_timeout": 10,
            # HTTP/3 specific PostgreSQL optimizations
            "application_name": "naboom_http3",
            "keepalives_idle": "600",
            "keepalives_interval": "30",
            "keepalives_count": "3",
        },
        
        "TEST": {
            "NAME": "test_naboomcommunity_http3",
        },
    }
}

# ============================================================================
# HTTP/3 OPTIMIZED REDIS CONFIGURATION
# ============================================================================

# HTTP/3 OPTIMIZED REDIS CACHE CONFIGURATION
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/0',  # DB 0: Django Cache
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # 'PARSER_CLASS': 'redis.connection.HiredisParser',  # Removed - not compatible with current redis-py version
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 500,  # Increased for HTTP/3 multiplexing
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
            # HTTP/3 Performance Optimizations
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'COMPRESSOR_LEVEL': 6,  # Balanced compression
            'IGNORE_EXCEPTIONS': True,
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'naboom:http3:cache',
        'TIMEOUT': 300,
        'VERSION': 1,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/3',  # DB 3: Django Sessions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # 'PARSER_CLASS': 'redis.connection.HiredisParser',  # Removed - not compatible with current redis-py version
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 200,  # Dedicated pool for sessions
                'retry_on_timeout': True,
                'socket_keepalive': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'naboom:http3:sessions',
        'TIMEOUT': 86400,  # 24 hours for HTTP/3 session persistence
    },
    'realtime': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/4',  # DB 4: Real-time streams
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'USERNAME': redis_users['REALTIME_PASSWORD']['user'],
            'PASSWORD': redis_users['REALTIME_PASSWORD']['password'],
            # 'PARSER_CLASS': 'redis.connection.HiredisParser',  # Removed - not compatible with current redis-py version
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 300,  # High concurrency for real-time
                'retry_on_timeout': True,
                'socket_keepalive': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'naboom:http3:realtime',
        'TIMEOUT': 60,
    },
    # HTTP/3 API Response Cache
    'api_responses': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/5',  # DB 5: API Response Cache
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # 'PARSER_CLASS': 'redis.connection.HiredisParser',  # Removed - not compatible with current redis-py version
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 400,
                'retry_on_timeout': True,
                'socket_keepalive': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'naboom:http3:api',
        'TIMEOUT': 1800,  # 30 minutes for API responses
    },
    # Wagtail Image Renditions Cache (uses pickle for complex objects)
    'renditions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_users["DJANGO_APP_PASSWORD"]["user"]}:{quote_plus(redis_users["DJANGO_APP_PASSWORD"]["password"])}@127.0.0.1:6379/6',  # DB 6: Wagtail Image Renditions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 200,
                'retry_on_timeout': True,
                'socket_keepalive': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',  # Use pickle for complex objects
        },
        'KEY_PREFIX': 'naboom:http3:renditions',
        'TIMEOUT': 86400,  # 24 hours for image renditions
    },
}

# ============================================================================
# WAGTAIL IMAGE RENDITIONS CACHE CONFIGURATION
# ============================================================================

# Configure Wagtail to use the dedicated renditions cache backend
WAGTAILIMAGES_RENDITION_CACHE = 'renditions'

# ============================================================================
# HTTP/3 OPTIMIZED CHANNEL LAYERS CONFIGURATION
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
            'expiry': 300,
            'group_expiry': 86400,
            'symmetric_encryption_keys': [SECRET_KEY],
            # HTTP/3 WebSocket optimizations
            'channel_layer': {
                'capacity': 16000,
                'expiry': 300,
            },
        },
    },
}

try:
    from .local import *
except ImportError:
    pass
