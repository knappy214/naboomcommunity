"""
HTTP/3 Optimized Utility Functions for Naboom Community Platform
"""

import hashlib
from django.core.cache import cache
from django.conf import settings


def cache_key_func(request, view_instance, view_method, *args, **kwargs):
    """
    Generate HTTP/3 optimized cache keys for API responses.
    
    This function creates cache keys that include:
    - HTTP/3 specific headers
    - User authentication state
    - Request parameters
    - View method and arguments
    """
    # Get HTTP/3 specific headers
    http3_active = request.META.get('HTTP_X_HTTP3_ACTIVE', 'false')
    quic_version = request.META.get('HTTP_X_QUIC_VERSION', 'unknown')
    
    # Get user info for cache key
    user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
    is_authenticated = getattr(request.user, 'is_authenticated', False) if hasattr(request, 'user') else False
    
    # Get request parameters
    query_params = request.GET.urlencode()
    request_method = request.method
    
    # Create cache key components
    key_components = [
        'http3',
        f'http3_active:{http3_active}',
        f'quic_version:{quic_version}',
        f'user_id:{user_id}',
        f'auth:{is_authenticated}',
        f'method:{request_method}',
        f'params:{query_params}',
        f'view:{view_instance.__class__.__name__}',
        f'action:{view_method}',
    ]
    
    # Add view-specific arguments
    if args:
        key_components.append(f'args:{":".join(str(arg) for arg in args)}')
    
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_components.append(f'kwargs:{":".join(f"{k}:{v}" for k, v in sorted_kwargs)}')
    
    # Create final cache key
    cache_key = ':'.join(key_components)
    
    # Hash the key if it's too long (Redis key length limit)
    if len(cache_key) > 250:
        cache_key = f"http3:{hashlib.md5(cache_key.encode()).hexdigest()}"
    
    return cache_key


def get_http3_cache_timeout(request, default_timeout=300):
    """
    Get HTTP/3 optimized cache timeout based on request characteristics.
    
    Args:
        request: Django HttpRequest object
        default_timeout: Default cache timeout in seconds
    
    Returns:
        int: Optimized cache timeout in seconds
    """
    # Check if HTTP/3 is active
    http3_active = request.META.get('HTTP_X_HTTP3_ACTIVE', 'false').lower() == 'true'
    
    # HTTP/3 connections can handle longer cache times due to better multiplexing
    if http3_active:
        return default_timeout * 2  # Double the cache time for HTTP/3
    
    # Check if it's an API request
    if request.path.startswith('/api/'):
        return default_timeout
    
    # Check if it's a static file request
    if request.path.startswith('/static/') or request.path.startswith('/media/'):
        return 86400  # 24 hours for static files
    
    return default_timeout


def invalidate_http3_cache_pattern(pattern):
    """
    Invalidate cache entries matching a pattern for HTTP/3 optimization.
    
    Args:
        pattern: Cache key pattern to match
    """
    try:
        # Get all cache keys matching the pattern
        cache_keys = cache.keys(f"*{pattern}*")
        
        if cache_keys:
            cache.delete_many(cache_keys)
            return len(cache_keys)
    except Exception as e:
        # Log error but don't raise
        print(f"Cache invalidation error: {e}")
    
    return 0


def get_http3_connection_info(request):
    """
    Extract HTTP/3 connection information from request headers.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        dict: HTTP/3 connection information
    """
    return {
        'http3_active': request.META.get('HTTP_X_HTTP3_ACTIVE', 'false').lower() == 'true',
        'quic_version': request.META.get('HTTP_X_QUIC_VERSION', 'unknown'),
        'connection_id': request.META.get('HTTP_X_CONNECTION_ID', 'unknown'),
        'stream_id': request.META.get('HTTP_X_STREAM_ID', 'unknown'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
        'remote_addr': request.META.get('REMOTE_ADDR', 'unknown'),
    }


def optimize_for_http3(response, request):
    """
    Add HTTP/3 specific headers to response for optimization.
    
    Args:
        response: Django HttpResponse object
        request: Django HttpRequest object
    
    Returns:
        HttpResponse: Response with HTTP/3 headers
    """
    # Add HTTP/3 specific headers
    response['X-HTTP3-Optimized'] = 'true'
    response['X-Cache-Strategy'] = 'http3-multiplexed'
    
    # Add connection reuse hints
    if request.META.get('HTTP_X_HTTP3_ACTIVE', 'false').lower() == 'true':
        response['X-Connection-Reuse'] = 'recommended'
        response['X-Multiplexing'] = 'enabled'
    
    return response
