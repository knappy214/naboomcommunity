"""
Utility functions for the Naboom Community project.
"""

from drf_spectacular.utils import extend_schema


def spectacular_preprocessing_hook(result, generator, request, public):
    """
    Preprocessing hook for drf-spectacular to customize schema generation.
    """
    # Add custom tags and descriptions for better API documentation
    for path, methods in result.get('paths', {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                # Add custom operation IDs to avoid collisions
                if 'operationId' in operation:
                    operation['operationId'] = f"naboom_community_{operation['operationId']}"
                
                # Add custom tags based on path
                if path.startswith('/api/v2/'):
                    operation.setdefault('tags', []).append('Wagtail API')
                elif path.startswith('/api/panic/'):
                    operation.setdefault('tags', []).append('Emergency Response')
                elif path.startswith('/api/community/'):
                    operation.setdefault('tags', []).append('Community Hub')
                elif path.startswith('/api/user/'):
                    operation.setdefault('tags', []).append('User Management')
    
    return result


def spectacular_postprocessing_hook(result, generator, request, public):
    """
    Postprocessing hook for drf-spectacular to finalize schema generation.
    """
    # Ensure all operation IDs are unique
    operation_ids = set()
    for path, methods in result.get('paths', {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and 'operationId' in operation:
                original_id = operation['operationId']
                counter = 1
                while operation['operationId'] in operation_ids:
                    operation['operationId'] = f"{original_id}_{counter}"
                    counter += 1
                operation_ids.add(operation['operationId'])
    
    return result


def cache_key_func(view_instance, view_method, request, *args, **kwargs):
    """
    Custom cache key function for REST Framework caching.
    """
    # Include user ID in cache key for user-specific responses
    user_id = getattr(request.user, 'id', 'anonymous')
    path = request.path
    query_params = request.GET.urlencode()
    
    return f"naboom_api:{user_id}:{path}:{query_params}"
