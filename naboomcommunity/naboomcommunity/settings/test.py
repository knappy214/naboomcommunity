from .base import *
import os

# Use in-memory SQLite database for tests to avoid external dependencies
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': ':memory:',
    }
}

SPATIALITE_LIBRARY_PATH = os.getenv('SPATIALITE_LIBRARY_PATH', 'mod_spatialite')

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
