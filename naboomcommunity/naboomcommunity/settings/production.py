from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

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

try:
    from .local import *
except ImportError:
    pass
