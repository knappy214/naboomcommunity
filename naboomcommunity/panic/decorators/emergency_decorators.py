"""
Emergency Response Decorators
Decorators for rate limiting, permissions, and emergency response operations.
"""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from ..rate_limiting.emergency_rate_limits import emergency_rate_limiter, emergency_burst_limiter
from ..auth.emergency_permissions import EmergencyUserPermission, EmergencyUserRole

User = get_user_model()
logger = logging.getLogger(__name__)


def emergency_rate_limit(action: str, burst_allowed: bool = False, custom_limits: dict = None):
    """
    Decorator for emergency rate limiting.
    
    Args:
        action: Action being rate limited
        burst_allowed: Whether burst limiting is allowed
        custom_limits: Custom rate limits
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                user_id = str(request.user.id) if request.user.is_authenticated else 'anonymous'
                identifier = request.META.get('REMOTE_ADDR', 'unknown')
                
                # Check emergency override first
                if emergency_rate_limiter.get_emergency_override(user_id, action):
                    return view_func(request, *args, **kwargs)
                
                # Check normal rate limit
                is_allowed, rate_info = emergency_rate_limiter.increment_rate_limit(
                    user_id, action, custom_limits, identifier
                )
                
                if not is_allowed:
                    logger.warning(f"Rate limit exceeded for user {user_id}, action {action}")
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'rate_limit_info': rate_info,
                        'retry_after': rate_info.get('reset_time', 0) - int(timezone.now().timestamp())
                    }, status=429)
                
                # Check burst limit if allowed
                if burst_allowed:
                    burst_allowed, burst_info = emergency_burst_limiter.increment_burst_limit(
                        user_id, action, identifier
                    )
                    
                    if not burst_allowed:
                        logger.warning(f"Burst limit exceeded for user {user_id}, action {action}")
                        return JsonResponse({
                            'error': 'Burst rate limit exceeded',
                            'burst_info': burst_info,
                            'retry_after': burst_info.get('window_seconds', 60)
                        }, status=429)
                
                # Add rate limit info to request
                request.rate_limit_info = rate_info
                if burst_allowed:
                    request.burst_limit_info = burst_info
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Rate limiting error: {str(e)}")
                # Fail open for emergency situations
                return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def emergency_permission_required(permission_type: str, scope_level: str = 'own', 
                                require_consent: bool = True, emergency_override: bool = True):
    """
    Decorator for emergency permission checking.
    
    Args:
        permission_type: Type of permission required
        scope_level: Scope level required
        require_consent: Whether consent is required
        emergency_override: Whether emergency override is allowed
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                if not request.user.is_authenticated:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                
                # Check emergency override
                if emergency_override and _has_emergency_override(request.user):
                    return view_func(request, *args, **kwargs)
                
                # Check user permissions
                has_permission = _check_emergency_permission(
                    request.user, permission_type, scope_level, require_consent
                )
                
                if not has_permission:
                    logger.warning(f"Permission denied for user {request.user.id}, permission {permission_type}")
                    return JsonResponse({
                        'error': 'Insufficient permissions',
                        'required_permission': permission_type,
                        'required_scope': scope_level
                    }, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Permission check error: {str(e)}")
                return JsonResponse({'error': 'Permission check failed'}, status=500)
        
        return wrapper
    return decorator


def emergency_consent_required(consent_level: str = 'basic'):
    """
    Decorator for emergency consent checking.
    
    Args:
        consent_level: Required consent level
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                if not request.user.is_authenticated:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                
                # Check consent level
                has_consent = _check_emergency_consent(request.user, consent_level)
                
                if not has_consent:
                    return JsonResponse({
                        'error': 'Consent required',
                        'required_consent': consent_level,
                        'consent_url': '/api/emergency/consent/'
                    }, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Consent check error: {str(e)}")
                return JsonResponse({'error': 'Consent check failed'}, status=500)
        
        return wrapper
    return decorator


def emergency_audit_log(action_type: str, severity: str = 'medium', 
                       log_request: bool = True, log_response: bool = False):
    """
    Decorator for emergency audit logging.
    
    Args:
        action_type: Type of action being logged
        severity: Severity level
        log_request: Whether to log request data
        log_response: Whether to log response data
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Log action start
                _log_emergency_action(
                    request, action_type, severity, 
                    log_request=log_request, log_response=log_response
                )
                
                response = view_func(request, *args, **kwargs)
                
                # Log action completion
                _log_emergency_action(
                    request, f"{action_type}_completed", severity,
                    log_request=log_request, log_response=log_response,
                    response=response
                )
                
                return response
                
            except Exception as e:
                # Log action error
                _log_emergency_action(
                    request, f"{action_type}_error", 'high',
                    log_request=log_request, log_response=log_response,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


def emergency_websocket_required():
    """
    Decorator for WebSocket emergency operations.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                if not request.user.is_authenticated:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                
                # Check WebSocket permission
                has_websocket_permission = _check_emergency_permission(
                    request.user, 'websocket_connect', 'own', require_consent=False
                )
                
                if not has_websocket_permission:
                    return JsonResponse({'error': 'WebSocket permission required'}, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"WebSocket permission check error: {str(e)}")
                return JsonResponse({'error': 'WebSocket permission check failed'}, status=500)
        
        return wrapper
    return decorator


def emergency_offline_sync_required():
    """
    Decorator for offline sync operations.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                if not request.user.is_authenticated:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                
                # Check offline sync permission
                has_sync_permission = _check_emergency_permission(
                    request.user, 'offline_sync', 'own', require_consent=False
                )
                
                if not has_sync_permission:
                    return JsonResponse({'error': 'Offline sync permission required'}, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Offline sync permission check error: {str(e)}")
                return JsonResponse({'error': 'Offline sync permission check failed'}, status=500)
        
        return wrapper
    return decorator


# Helper functions

def _has_emergency_override(user: User) -> bool:
    """Check if user has emergency override permissions."""
    try:
        return user.emergency_roles.filter(
            role__role_type__in=['responder', 'coordinator', 'admin'],
            is_active=True
        ).exists()
    except Exception:
        return False


def _check_emergency_permission(user: User, permission_type: str, 
                              scope_level: str, require_consent: bool = True) -> bool:
    """Check if user has required emergency permission."""
    try:
        # Check user permissions
        user_permissions = EmergencyUserPermission.objects.filter(
            user=user,
            permission__permission_type=permission_type,
            permission__scope_level=scope_level,
            is_active=True
        )
        
        for perm in user_permissions:
            if perm.is_valid():
                # Check consent requirement
                if require_consent and perm.permission.requires_consent:
                    if not _check_emergency_consent(user, 'basic'):
                        continue
                
                return True
        
        # Check role permissions
        user_roles = EmergencyUserRole.objects.filter(
            user=user,
            is_active=True
        )
        
        for role in user_roles:
            if role.is_valid():
                role_permissions = role.role.permissions.filter(
                    permission_type=permission_type,
                    scope_level=scope_level,
                    is_active=True
                )
                
                for perm in role_permissions:
                    if perm.is_valid():
                        # Check consent requirement
                        if require_consent and perm.requires_consent:
                            if not _check_emergency_consent(user, 'basic'):
                                continue
                        
                        return True
        
        return False
        
    except Exception as e:
        logger.error(f"Permission check error: {str(e)}")
        return False


def _check_emergency_consent(user: User, consent_level: str) -> bool:
    """Check if user has required consent level."""
    try:
        if not hasattr(user, 'emergency_medical'):
            return False
        
        medical_info = user.emergency_medical
        return medical_info.has_valid_consent() and medical_info.consent_level in [
            'basic', 'full', 'emergency_only'
        ]
        
    except Exception as e:
        logger.error(f"Consent check error: {str(e)}")
        return False


def _log_emergency_action(request, action_type: str, severity: str, 
                         log_request: bool = True, log_response: bool = False,
                         response=None, error: str = None):
    """Log emergency action to audit system."""
    try:
        from ..models.emergency_audit import EmergencyAuditLog
        
        # Prepare metadata
        metadata = {}
        
        if log_request:
            metadata.update({
                'request_method': request.method,
                'request_path': request.path,
                'request_data': getattr(request, 'data', {}),
            })
        
        if log_response and response:
            metadata.update({
                'response_status': getattr(response, 'status_code', None),
                'response_data': getattr(response, 'data', {}),
            })
        
        if error:
            metadata['error'] = error
        
        # Log the action
        EmergencyAuditLog.log_action(
            action_type=action_type,
            description=f"Emergency action: {action_type}",
            user=request.user if request.user.is_authenticated else None,
            severity=severity,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key,
            request_method=request.method,
            request_path=request.path,
            response_status=getattr(response, 'status_code', None) if response else None,
            metadata=metadata,
            error_message=error
        )
        
    except Exception as e:
        logger.error(f"Audit logging error: {str(e)}")


# Class-based decorators for Django views

def emergency_view_decorator(permission_type: str = None, rate_limit_action: str = None,
                           consent_level: str = None, audit_action: str = None):
    """
    Combined decorator for emergency views.
    
    Args:
        permission_type: Required permission type
        rate_limit_action: Rate limiting action
        consent_level: Required consent level
        audit_action: Audit action type
    """
    def decorator(view_class):
        # Apply decorators in order
        if audit_action:
            view_class.dispatch = emergency_audit_log(audit_action)(view_class.dispatch)
        
        if consent_level:
            view_class.dispatch = emergency_consent_required(consent_level)(view_class.dispatch)
        
        if permission_type:
            view_class.dispatch = emergency_permission_required(permission_type)(view_class.dispatch)
        
        if rate_limit_action:
            view_class.dispatch = emergency_rate_limit(rate_limit_action)(view_class.dispatch)
        
        return view_class
    
    return decorator
