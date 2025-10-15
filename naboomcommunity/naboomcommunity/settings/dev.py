from .base import *
from urllib.parse import quote_plus

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-8gem37f7c)%5q*f#2!mo_6zgra8u=*q5a3h#ln^v*qj&^iq=+j"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Redis configuration for development (using production credentials for consistency)
redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
redis_port = os.getenv('REDIS_PORT', '6379')
redis_password = os.getenv('REDIS_PASSWORD', 'YkdcugPLQyHZw+8P7ElFG9a/nroiKWwY')
redis_user = os.getenv('REDIS_USER', 'app_user')

# Build Redis URL with authentication
if redis_user and redis_password:
    redis_url = f"redis://{redis_user}:{quote_plus(redis_password)}@{redis_host}:{redis_port}/0"
elif redis_password:
    redis_url = f"redis://:{quote_plus(redis_password)}@{redis_host}:{redis_port}/0"
else:
    redis_url = f"redis://{redis_host}:{redis_port}/0"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 500,
                "retry_on_timeout": True,
                "socket_keepalive": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
        },
    }
}


try:
    from .local import *
except ImportError:
    pass
