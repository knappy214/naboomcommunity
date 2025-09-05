"""
Custom middleware for handling Content Security Policy headers.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CSPMiddleware:
    """
    Middleware to set Content Security Policy headers that allow images from S3.
    This middleware runs after all other middleware to override any existing CSP headers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log existing CSP headers for debugging
        existing_csp = response.get('Content-Security-Policy', 'None')
        logger.info(f"Existing CSP header: {existing_csp}")
        
        # Remove any existing CSP headers to ensure our policy takes precedence
        # Handle both HttpResponse and TemplateResponse objects
        if hasattr(response, 'pop'):
            # Regular HttpResponse object
            response.pop('Content-Security-Policy', None)
            response.pop('Content-Security-Policy-Report-Only', None)
        else:
            # TemplateResponse object - use del instead of pop
            if 'Content-Security-Policy' in response:
                del response['Content-Security-Policy']
            if 'Content-Security-Policy-Report-Only' in response:
                del response['Content-Security-Policy-Report-Only']
        
        # Set comprehensive CSP header to allow images from S3 and Gravatar
        csp_policy = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https://s3.naboomneighbornet.net.za https://www.gravatar.com https://*.gravatar.com; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # For admin pages, be more permissive with image sources
        if request.path.startswith('/admin/'):
            csp_policy = (
                "default-src 'self'; "
                "img-src 'self' data: blob: https: http:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        
        # Set the CSP header
        response['Content-Security-Policy'] = csp_policy
        logger.info(f"Set CSP header: {csp_policy}")
        
        return response
