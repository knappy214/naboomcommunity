"""
Emergency Rate Limiting Middleware
Middleware for emergency response rate limiting with Redis integration.
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
import logging

from ..rate_limiting.emergency_rate_limits import emergency_rate_limiter, emergency_burst_limiter

logger = logging.getLogger(__name__)


class EmergencyRateLimitingMiddleware(MiddlewareMixin):
    """
    Middleware for emergency response rate limiting.
    
    Applies rate limiting to emergency endpoints with different limits
    for different types of operations and user roles.
    """
    
    # Emergency endpoints that require rate limiting
    EMERGENCY_PATHS = [
        '/api/enhanced/',
        '/api/offline/',
        '/api/family/',
        '/api/integration/',
        '/ws/emergency/',
        '/ws/location/',
    ]
    
    # Rate limit actions based on path patterns
    PATH_ACTIONS = {
        '/api/enhanced/': 'panic_activate',
        '/api/offline/': 'offline_sync',
        '/api/family/': 'notification_send',
        '/api/integration/': 'external_api',
        '/ws/emergency/': 'websocket_connect',
        '/ws/location/': 'websocket_connect',
    }
    
    def process_request(self, request):
        """
        Process incoming request for rate limiting.
        
        Args:
            request: Django request object
            
        Returns:
            JsonResponse if rate limited, None if allowed
        """
        try:
            # Check if this is an emergency endpoint
            if not self._is_emergency_endpoint(request.path):
                return None
            
            # Skip rate limiting for certain user agents (monitoring, health checks)
            if self._should_skip_rate_limiting(request):
                return None
            
            # Get user and action
            user_id = str(request.user.id) if request.user.is_authenticated else 'anonymous'
            action = self._get_action_for_path(request.path)
            identifier = self._get_identifier(request)
            
            # Check emergency override
            if emergency_rate_limiter.get_emergency_override(user_id, action):
                return None
            
            # Check normal rate limit
            is_allowed, rate_info = emergency_rate_limiter.check_rate_limit(
                user_id, action, identifier=identifier
            )
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}, action {action}, path {request.path}")
                return self._create_rate_limit_response(rate_info, 429)
            
            # Check burst limit for emergency operations
            if self._is_emergency_operation(request.path):
                burst_allowed, burst_info = emergency_burst_limiter.check_burst_limit(
                    user_id, action, identifier=identifier
                )
                
                if not burst_allowed:
                    logger.warning(f"Burst limit exceeded for user {user_id}, action {action}, path {request.path}")
                    return self._create_rate_limit_response(burst_info, 429)
            
            # Store rate limit info in request for logging
            request.rate_limit_info = rate_info
            if self._is_emergency_operation(request.path):
                request.burst_limit_info = burst_info
            
            return None
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {str(e)}")
            # Fail open for emergency situations
            return None
    
    def process_response(self, request, response):
        """
        Process outgoing response for rate limiting updates.
        
        Args:
            request: Django request object
            response: Django response object
            
        Returns:
            Modified response object
        """
        try:
            # Only process emergency endpoints
            if not self._is_emergency_endpoint(request.path):
                return response
            
            # Skip if already rate limited
            if isinstance(response, JsonResponse) and response.status_code == 429:
                return response
            
            # Skip for certain user agents
            if self._should_skip_rate_limiting(request):
                return response
            
            # Get user and action
            user_id = str(request.user.id) if request.user.is_authenticated else 'anonymous'
            action = self._get_action_for_path(request.path)
            identifier = self._get_identifier(request)
            
            # Check emergency override
            if emergency_rate_limiter.get_emergency_override(user_id, action):
                return response
            
            # Increment rate limit counter
            is_allowed, rate_info = emergency_rate_limiter.increment_rate_limit(
                user_id, action, identifier=identifier
            )
            
            # Increment burst limit for emergency operations
            if self._is_emergency_operation(request.path):
                burst_allowed, burst_info = emergency_burst_limiter.increment_burst_limit(
                    user_id, action, identifier=identifier
                )
            
            # Add rate limit headers to response
            response = self._add_rate_limit_headers(response, rate_info)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting response processing error: {str(e)}")
            return response
    
    def _is_emergency_endpoint(self, path):
        """Check if path is an emergency endpoint."""
        return any(path.startswith(emergency_path) for emergency_path in self.EMERGENCY_PATHS)
    
    def _is_emergency_operation(self, path):
        """Check if path is an emergency operation (allows burst limits)."""
        emergency_ops = ['/api/enhanced/', '/api/offline/']
        return any(path.startswith(op) for op in emergency_ops)
    
    def _should_skip_rate_limiting(self, request):
        """Check if rate limiting should be skipped for this request."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Skip for monitoring and health check user agents
        skip_agents = [
            'healthcheck',
            'monitoring',
            'uptime',
            'pingdom',
            'newrelic',
            'datadog',
        ]
        
        return any(agent in user_agent for agent in skip_agents)
    
    def _get_action_for_path(self, path):
        """Get rate limiting action for path."""
        for emergency_path, action in self.PATH_ACTIONS.items():
            if path.startswith(emergency_path):
                return action
        return 'emergency_access'  # Default action
    
    def _get_identifier(self, request):
        """Get identifier for rate limiting (IP address)."""
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _create_rate_limit_response(self, rate_info, status_code):
        """Create rate limit exceeded response."""
        retry_after = rate_info.get('reset_time', 0) - int(timezone.now().timestamp())
        
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'rate_limit_info': rate_info,
            'retry_after': max(0, retry_after),
            'message': 'Too many requests. Please try again later.'
        }, status=status_code)
    
    def _add_rate_limit_headers(self, response, rate_info):
        """Add rate limiting headers to response."""
        response['X-RateLimit-Limit'] = rate_info.get('max_requests', 0)
        response['X-RateLimit-Remaining'] = rate_info.get('remaining', 0)
        response['X-RateLimit-Reset'] = rate_info.get('reset_time', 0)
        response['X-RateLimit-Window'] = rate_info.get('window_seconds', 0)
        
        return response


class EmergencyAuditMiddleware(MiddlewareMixin):
    """
    Middleware for emergency audit logging.
    
    Logs all emergency endpoint access for audit purposes.
    """
    
    def process_request(self, request):
        """Log emergency request start."""
        try:
            if self._is_emergency_endpoint(request.path):
                request._emergency_audit_start = timezone.now()
                request._emergency_audit_path = request.path
                request._emergency_audit_method = request.method
        except Exception as e:
            logger.error(f"Emergency audit middleware request error: {str(e)}")
    
    def process_response(self, request, response):
        """Log emergency request completion."""
        try:
            if hasattr(request, '_emergency_audit_start'):
                self._log_emergency_access(request, response)
        except Exception as e:
            logger.error(f"Emergency audit middleware response error: {str(e)}")
        
        return response
    
    def _is_emergency_endpoint(self, path):
        """Check if path is an emergency endpoint."""
        emergency_paths = [
            '/api/enhanced/',
            '/api/offline/',
            '/api/family/',
            '/api/integration/',
            '/ws/emergency/',
            '/ws/location/',
        ]
        return any(path.startswith(ep) for ep in emergency_paths)
    
    def _log_emergency_access(self, request, response):
        """Log emergency access for audit."""
        try:
            from ..models.emergency_audit import EmergencyAuditLog
            
            duration = (timezone.now() - request._emergency_audit_start).total_seconds()
            
            EmergencyAuditLog.log_action(
                action_type='emergency_access',
                description=f"Emergency endpoint access: {request._emergency_audit_method} {request._emergency_audit_path}",
                user=request.user if request.user.is_authenticated else None,
                severity='medium',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=request.session.session_key,
                request_method=request._emergency_audit_method,
                request_path=request._emergency_audit_path,
                response_status=response.status_code,
                metadata={
                    'duration_seconds': duration,
                    'rate_limit_info': getattr(request, 'rate_limit_info', {}),
                    'burst_limit_info': getattr(request, 'burst_limit_info', {}),
                }
            )
        except Exception as e:
            logger.error(f"Emergency audit logging error: {str(e)}")
