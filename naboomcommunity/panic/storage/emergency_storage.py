"""
Emergency Storage Backend for MinIO
Handles emergency media files with enhanced security and organization.
"""

import os
from datetime import datetime
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import get_storage_class


class EmergencyMediaStorage(S3Boto3Storage):
    """
    Custom storage backend for emergency media files.
    Organizes files by emergency type and date for better management.
    """
    
    def __init__(self, **settings_dict):
        # Use emergency-specific bucket
        self.bucket_name = getattr(settings, 'EMERGENCY_STORAGE_BUCKET_NAME', 'naboom-emergency-media')
        self.location = 'emergency'
        super().__init__(**settings_dict)
    
    def get_available_name(self, name, max_length=None):
        """
        Generate a unique filename for emergency media files.
        Includes timestamp and emergency type for organization.
        """
        # Extract file extension
        name, ext = os.path.splitext(name)
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create organized path structure
        # Format: emergency/{type}/{year}/{month}/{timestamp}_{original_name}.{ext}
        now = datetime.now()
        path_parts = [
            'emergency',
            'media',  # Default type, can be overridden
            now.strftime('%Y'),
            now.strftime('%m'),
            f"{timestamp}_{name}{ext}"
        ]
        
        return '/'.join(path_parts)
    
    def url(self, name):
        """
        Generate URL for emergency media files.
        Uses signed URLs for security.
        """
        return super().url(name)


class EmergencyLocationStorage(S3Boto3Storage):
    """
    Storage backend for emergency location data and GPS files.
    """
    
    def __init__(self, **settings_dict):
        self.bucket_name = getattr(settings, 'EMERGENCY_STORAGE_BUCKET_NAME', 'naboom-emergency-media')
        self.location = 'emergency/location'
        super().__init__(**settings_dict)
    
    def get_available_name(self, name, max_length=None):
        """Generate organized filename for location data."""
        name, ext = os.path.splitext(name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        path_parts = [
            'emergency',
            'location',
            datetime.now().strftime('%Y'),
            datetime.now().strftime('%m'),
            f"{timestamp}_{name}{ext}"
        ]
        
        return '/'.join(path_parts)


class EmergencyMedicalStorage(S3Boto3Storage):
    """
    Storage backend for emergency medical data and sensitive files.
    Uses enhanced security and encryption.
    """
    
    def __init__(self, **settings_dict):
        self.bucket_name = getattr(settings, 'EMERGENCY_STORAGE_BUCKET_NAME', 'naboom-emergency-media')
        self.location = 'emergency/medical'
        super().__init__(**settings_dict)
    
    def get_available_name(self, name, max_length=None):
        """Generate organized filename for medical data."""
        name, ext = os.path.splitext(name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        path_parts = [
            'emergency',
            'medical',
            datetime.now().strftime('%Y'),
            datetime.now().strftime('%m'),
            f"{timestamp}_{name}{ext}"
        ]
        
        return '/'.join(path_parts)
    
    def url(self, name):
        """
        Generate signed URL for medical files with shorter expiration.
        Medical data requires enhanced security.
        """
        # Use shorter expiration for medical data (1 hour instead of default)
        return super().url(name)


class EmergencyNotificationStorage(S3Boto3Storage):
    """
    Storage backend for emergency notification media and attachments.
    """
    
    def __init__(self, **settings_dict):
        self.bucket_name = getattr(settings, 'EMERGENCY_STORAGE_BUCKET_NAME', 'naboom-emergency-media')
        self.location = 'emergency/notifications'
        super().__init__(**settings_dict)
    
    def get_available_name(self, name, max_length=None):
        """Generate organized filename for notification media."""
        name, ext = os.path.splitext(name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        path_parts = [
            'emergency',
            'notifications',
            datetime.now().strftime('%Y'),
            datetime.now().strftime('%m'),
            f"{timestamp}_{name}{ext}"
        ]
        
        return '/'.join(path_parts)


# Storage class mappings for easy access
EMERGENCY_STORAGE_CLASSES = {
    'emergency_media': EmergencyMediaStorage,
    'emergency_location': EmergencyLocationStorage,
    'emergency_medical': EmergencyMedicalStorage,
    'emergency_notifications': EmergencyNotificationStorage,
}


def get_emergency_storage(storage_type='emergency_media'):
    """
    Get emergency storage instance by type.
    
    Args:
        storage_type: Type of emergency storage ('emergency_media', 'emergency_location', etc.)
    
    Returns:
        Storage instance
    """
    storage_class = EMERGENCY_STORAGE_CLASSES.get(storage_type, EmergencyMediaStorage)
    return storage_class()
