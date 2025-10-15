"""
Emergency Response Throttling System
Advanced throttling for emergency response operations with Redis integration.
"""

from rest_framework.throttling import BaseThrottle, UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import time
import logging
from typing import Optional, Dict, Any

from ..rate_limiting.emergency_rate_limits import emergency_rate_limiter, emergency_burst_limiter

User = get_user_model()
logger = logging.getLogger(__name__)


class EmergencyBaseThrottle(BaseThrottle):
    """
    Base throttle class for emergency response operations.
    Provides common functionality for emergency-specific throttling.
    """
    
    def get_cache_key(self, request, view):
        """
        Generate cache key for throttling.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Cache key string
        """
        if request.user.is_authenticated:
            return f"emergency_throttle_user_{request.user.id}_{self.get_scope()}"
        else:
            ip = self.get_ident(request)
            return f"emergency_throttle_anon_{ip}_{self.get_scope()}"
    
    def get_scope(self):
        """Get throttle scope - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement get_scope()")
    
    def get_ident(self, request):
        """
        Identify the client making the request.
        
        Args:
            request: Django request object
            
        Returns:
            Client identifier string
        """
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def get_rate_info(self, request, view):
        """
        Get rate limiting information.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Rate limiting information dict
        """
        user_id = str(request.user.id) if request.user.is_authenticated else 'anonymous'
        action = self.get_action_for_view(view)
        identifier = self.get_ident(request)
        
        # Check emergency override
        if emergency_rate_limiter.get_emergency_override(user_id, action):
            return {'is_allowed': True, 'emergency_override': True}
        
        # Check normal rate limit
        is_allowed, rate_info = emergency_rate_limiter.check_rate_limit(
            user_id, action, identifier=identifier
        )
        
        return {
            'is_allowed': is_allowed,
            'rate_info': rate_info,
            'action': action
        }
    
    def get_action_for_view(self, view):
        """
        Get rate limiting action for view.
        
        Args:
            view: View instance
            
        Returns:
            Action string
        """
        # Map view names to actions
        view_name = getattr(view, '__class__', {}).__name__.lower()
        
        action_mapping = {
            'enhancedpanicbuttonview': 'panic_activate',
            'offlinepanicbuttonview': 'offline_sync',
            'familynotificationview': 'notification_send',
            'externalintegrationview': 'external_api',
            'emergencylocationview': 'location_update',
            'emergencymedicalview': 'medical_access',
        }
        
        return action_mapping.get(view_name, 'emergency_access')
    
    def get_wait_time(self, rate_info):
        """
        Calculate wait time before next request.
        
        Args:
            rate_info: Rate limiting information
            
        Returns:
            Wait time in seconds
        """
        if rate_info.get('is_allowed', True):
            return None
        
        reset_time = rate_info.get('rate_info', {}).get('reset_time', 0)
        current_time = int(timezone.now().timestamp())
        
        if reset_time > current_time:
            return reset_time - current_time
        
        return None


class EmergencyPanicThrottle(EmergencyBaseThrottle):
    """
    Throttle for panic button activation.
    Very restrictive to prevent abuse during emergencies.
    """
    
    def get_scope(self):
        return 'panic_activate'
    
    def allow_request(self, request, view):
        """
        Check if panic button request should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"Panic button throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            # Check burst limit for panic button
            if request.user.is_authenticated:
                user_id = str(request.user.id)
                action = 'panic_activate'
                identifier = self.get_ident(request)
                
                burst_allowed, burst_info = emergency_burst_limiter.check_burst_limit(
                    user_id, action, identifier=identifier
                )
                
                if not burst_allowed:
                    logger.warning(f"Panic button burst limit exceeded for user {user_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Panic throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"Panic throttle wait error: {str(e)}")
            return None


class EmergencyLocationThrottle(EmergencyBaseThrottle):
    """
    Throttle for location update operations.
    Moderate restrictions for location tracking.
    """
    
    def get_scope(self):
        return 'location_update'
    
    def allow_request(self, request, view):
        """
        Check if location update request should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"Location update throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Location throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"Location throttle wait error: {str(e)}")
            return None


class EmergencyMedicalThrottle(EmergencyBaseThrottle):
    """
    Throttle for medical data access.
    Strict restrictions for privacy protection.
    """
    
    def get_scope(self):
        return 'medical_access'
    
    def allow_request(self, request, view):
        """
        Check if medical data request should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"Medical access throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Medical throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"Medical throttle wait error: {str(e)}")
            return None


class EmergencyNotificationThrottle(EmergencyBaseThrottle):
    """
    Throttle for notification operations.
    Moderate restrictions for notification sending.
    """
    
    def get_scope(self):
        return 'notification_send'
    
    def allow_request(self, request, view):
        """
        Check if notification request should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"Notification throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Notification throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"Notification throttle wait error: {str(e)}")
            return None


class EmergencyWebSocketThrottle(EmergencyBaseThrottle):
    """
    Throttle for WebSocket connections.
    Moderate restrictions for WebSocket connections.
    """
    
    def get_scope(self):
        return 'websocket_connect'
    
    def allow_request(self, request, view):
        """
        Check if WebSocket connection should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"WebSocket throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"WebSocket throttle wait error: {str(e)}")
            return None


class EmergencyOfflineThrottle(EmergencyBaseThrottle):
    """
    Throttle for offline sync operations.
    Moderate restrictions for offline data synchronization.
    """
    
    def get_scope(self):
        return 'offline_sync'
    
    def allow_request(self, request, view):
        """
        Check if offline sync request should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"Offline sync throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Offline sync throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"Offline sync throttle wait error: {str(e)}")
            return None


class EmergencyExternalThrottle(EmergencyBaseThrottle):
    """
    Throttle for external API operations.
    Strict restrictions for external service calls.
    """
    
    def get_scope(self):
        return 'external_api'
    
    def allow_request(self, request, view):
        """
        Check if external API request should be allowed.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Boolean indicating if request is allowed
        """
        try:
            rate_info = self.get_rate_info(request, view)
            
            if rate_info.get('emergency_override'):
                return True
            
            if not rate_info.get('is_allowed', True):
                logger.warning(f"External API throttled for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"External API throttle error: {str(e)}")
            # Fail open for emergency situations
            return True
    
    def wait(self, request, view):
        """
        Get wait time before next request.
        
        Args:
            request: Django request object
            view: View instance
            
        Returns:
            Wait time in seconds or None
        """
        try:
            rate_info = self.get_rate_info(request, view)
            return self.get_wait_time(rate_info)
        except Exception as e:
            logger.error(f"External API throttle wait error: {str(e)}")
            return None


# Throttle class mappings for easy configuration
EMERGENCY_THROTTLE_CLASSES = {
    'panic_activate': EmergencyPanicThrottle,
    'location_update': EmergencyLocationThrottle,
    'medical_access': EmergencyMedicalThrottle,
    'notification_send': EmergencyNotificationThrottle,
    'websocket_connect': EmergencyWebSocketThrottle,
    'offline_sync': EmergencyOfflineThrottle,
    'external_api': EmergencyExternalThrottle,
}


def get_emergency_throttle_class(action):
    """
    Get throttle class for emergency action.
    
    Args:
        action: Emergency action string
        
    Returns:
        Throttle class
    """
    return EMERGENCY_THROTTLE_CLASSES.get(action, EmergencyBaseThrottle)
