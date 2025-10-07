from __future__ import annotations

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class WagtailAPICorsMiddleware(MiddlewareMixin):
    """
    Custom middleware to handle CORS for Wagtail API v2 endpoints.
    Wagtail API v2 doesn't handle OPTIONS requests by default, so we need to
    intercept them and return proper CORS headers.
    """
    
    def process_request(self, request):
        # Only handle OPTIONS requests for Wagtail API v2 endpoints
        if (request.method == 'OPTIONS' and 
            request.path.startswith('/api/v2/')):
            
            # Get CORS headers from django-cors-headers settings
            cors_headers = self._get_cors_headers(request)
            
            # Return a 200 response with CORS headers
            response = JsonResponse({})
            for header, value in cors_headers.items():
                response[header] = value
            
            return response
        
        return None
    
    def _get_cors_headers(self, request):
        """Generate CORS headers based on django-cors-headers settings."""
        origin = request.META.get('HTTP_ORIGIN')
        
        # Check if origin is allowed
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if origin in allowed_origins:
            headers = {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Credentials': 'true',
            }
        else:
            # If no origin or not allowed, don't set CORS headers
            return {}
        
        # Add other CORS headers
        headers.update({
            'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': ', '.join(getattr(settings, 'CORS_ALLOWED_HEADERS', [])),
            'Access-Control-Expose-Headers': ', '.join(getattr(settings, 'CORS_EXPOSE_HEADERS', [])),
            'Access-Control-Max-Age': '86400',
        })
        
        return headers
