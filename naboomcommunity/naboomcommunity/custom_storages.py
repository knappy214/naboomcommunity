"""
Custom storage backends for MinIO/S3 integration with Wagtail.
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage for media files (images, videos, etc.).
    These files are publicly accessible.
    """
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    querystring_auth = False


class DocumentStorage(S3Boto3Storage):
    """
    Custom storage for documents (PDFs, Word docs, etc.).
    These files are kept private and require authentication.
    """
    location = 'documents'
    default_acl = 'private'
    file_overwrite = False
    querystring_auth = True  # Enable signed URLs for private documents


class StaticStorage(S3Boto3Storage):
    """
    Custom storage for static files (CSS, JS, images).
    These files are publicly accessible and cached.
    """
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True  # Allow overwriting for static files
    querystring_auth = False
