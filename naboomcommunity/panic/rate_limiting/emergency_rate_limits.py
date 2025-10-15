"""
Emergency Response Rate Limiting
Advanced rate limiting for emergency response operations with Redis integration.
"""

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import time
import json
import hashlib
from typing import Dict, Optional, Tuple, Any
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class EmergencyRateLimiter:
    """
    Advanced rate limiter for emergency response operations.
    Uses Redis for distributed rate limiting with multiple strategies.
    """
    
    def __init__(self):
        self.redis_client = cache.get_client()
        self.default_limits = {
            'panic_activate': {'requests': 5, 'window': 300},  # 5 per 5 minutes
            'location_update': {'requests': 60, 'window': 60},  # 60 per minute
            'medical_access': {'requests': 10, 'window': 300},  # 10 per 5 minutes
            'notification_send': {'requests': 20, 'window': 60},  # 20 per minute
            'websocket_connect': {'requests': 10, 'window': 60},  # 10 per minute
            'offline_sync': {'requests': 3, 'window': 300},  # 3 per 5 minutes
            'external_api': {'requests': 100, 'window': 3600},  # 100 per hour
        }
    
    def _get_cache_key(self, user_id: str, action: str, identifier: str = None) -> str:
        """
        Generate cache key for rate limiting.
        
        Args:
            user_id: User ID
            action: Action being rate limited
            identifier: Additional identifier (IP, device, etc.)
            
        Returns:
            Cache key string
        """
        key_parts = ['emergency_rate_limit', action, str(user_id)]
        if identifier:
            key_parts.append(identifier)
        
        return ':'.join(key_parts)
    
    def _get_window_key(self, base_key: str, window_start: int) -> str:
        """Get window-specific cache key."""
        return f"{base_key}:{window_start}"
    
    def _get_current_window(self, window_seconds: int) -> int:
        """Get current time window."""
        return int(time.time() // window_seconds) * window_seconds
    
    def check_rate_limit(self, user_id: str, action: str, 
                        custom_limits: Dict = None, 
                        identifier: str = None) -> Tuple[bool, Dict]:
        """
        Check if action is within rate limits.
        
        Args:
            user_id: User ID
            action: Action being performed
            custom_limits: Custom rate limits (overrides defaults)
            identifier: Additional identifier for rate limiting
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            # Get rate limits
            limits = custom_limits or self.default_limits.get(action, {'requests': 10, 'window': 60})
            max_requests = limits['requests']
            window_seconds = limits['window']
            
            # Generate cache keys
            base_key = self._get_cache_key(user_id, action, identifier)
            current_window = self._get_current_window(window_seconds)
            window_key = self._get_window_key(base_key, current_window)
            
            # Get current count
            current_count = self.redis_client.get(window_key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            # Check if limit exceeded
            is_allowed = current_count < max_requests
            
            # Prepare response
            rate_limit_info = {
                'action': action,
                'current_count': current_count,
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'window_start': current_window,
                'window_end': current_window + window_seconds,
                'is_allowed': is_allowed,
                'remaining': max(0, max_requests - current_count),
                'reset_time': current_window + window_seconds,
            }
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail open for emergency situations
            return True, {'error': str(e), 'is_allowed': True}
    
    def increment_rate_limit(self, user_id: str, action: str, 
                           custom_limits: Dict = None,
                           identifier: str = None) -> Tuple[bool, Dict]:
        """
        Increment rate limit counter and check if allowed.
        
        Args:
            user_id: User ID
            action: Action being performed
            custom_limits: Custom rate limits
            identifier: Additional identifier
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            # Get rate limits
            limits = custom_limits or self.default_limits.get(action, {'requests': 10, 'window': 60})
            max_requests = limits['requests']
            window_seconds = limits['window']
            
            # Generate cache keys
            base_key = self._get_cache_key(user_id, action, identifier)
            current_window = self._get_current_window(window_seconds)
            window_key = self._get_window_key(base_key, current_window)
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Increment counter
            pipe.incr(window_key)
            pipe.expire(window_key, window_seconds)
            
            # Execute pipeline
            results = pipe.execute()
            current_count = results[0]
            
            # Check if limit exceeded
            is_allowed = current_count <= max_requests
            
            # Prepare response
            rate_limit_info = {
                'action': action,
                'current_count': current_count,
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'window_start': current_window,
                'window_end': current_window + window_seconds,
                'is_allowed': is_allowed,
                'remaining': max(0, max_requests - current_count),
                'reset_time': current_window + window_seconds,
            }
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit increment failed: {str(e)}")
            # Fail open for emergency situations
            return True, {'error': str(e), 'is_allowed': True}
    
    def get_rate_limit_status(self, user_id: str, action: str, 
                            identifier: str = None) -> Dict:
        """
        Get current rate limit status without incrementing.
        
        Args:
            user_id: User ID
            action: Action to check
            identifier: Additional identifier
            
        Returns:
            Rate limit status information
        """
        is_allowed, rate_limit_info = self.check_rate_limit(
            user_id, action, identifier=identifier
        )
        return rate_limit_info
    
    def reset_rate_limit(self, user_id: str, action: str, 
                        identifier: str = None) -> bool:
        """
        Reset rate limit for user and action.
        
        Args:
            user_id: User ID
            action: Action to reset
            identifier: Additional identifier
            
        Returns:
            Success status
        """
        try:
            base_key = self._get_cache_key(user_id, action, identifier)
            
            # Get all window keys for this base key
            pattern = f"{base_key}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit reset failed: {str(e)}")
            return False
    
    def get_emergency_override(self, user_id: str, action: str) -> bool:
        """
        Check if user has emergency override for rate limits.
        
        Args:
            user_id: User ID
            action: Action being performed
            
        Returns:
            True if emergency override is available
        """
        try:
            # Check for emergency role or admin status
            user = User.objects.get(id=user_id)
            
            # Check for emergency roles
            emergency_roles = user.emergency_roles.filter(
                role__role_type__in=['responder', 'coordinator', 'admin', 'medical'],
                is_active=True
            )
            
            if emergency_roles.exists():
                return True
            
            # Check for emergency override permission
            override_key = f"emergency_override:{user_id}:{action}"
            return self.redis_client.exists(override_key)
            
        except Exception as e:
            logger.error(f"Emergency override check failed: {str(e)}")
            return False
    
    def set_emergency_override(self, user_id: str, action: str, 
                             duration_seconds: int = 3600) -> bool:
        """
        Set emergency override for rate limits.
        
        Args:
            user_id: User ID
            action: Action to override
            duration_seconds: Override duration
            
        Returns:
            Success status
        """
        try:
            override_key = f"emergency_override:{user_id}:{action}"
            self.redis_client.setex(override_key, duration_seconds, "1")
            return True
            
        except Exception as e:
            logger.error(f"Emergency override set failed: {str(e)}")
            return False


class EmergencyBurstLimiter:
    """
    Burst rate limiter for emergency situations.
    Allows temporary bursts above normal limits during emergencies.
    """
    
    def __init__(self):
        self.redis_client = cache.get_client()
        self.burst_limits = {
            'panic_activate': {'burst_requests': 10, 'burst_window': 60},  # 10 in 1 minute
            'location_update': {'burst_requests': 120, 'burst_window': 60},  # 120 in 1 minute
            'notification_send': {'burst_requests': 50, 'burst_window': 60},  # 50 in 1 minute
        }
    
    def check_burst_limit(self, user_id: str, action: str, 
                         identifier: str = None) -> Tuple[bool, Dict]:
        """
        Check burst rate limit.
        
        Args:
            user_id: User ID
            action: Action being performed
            identifier: Additional identifier
            
        Returns:
            Tuple of (is_allowed, burst_info)
        """
        try:
            limits = self.burst_limits.get(action, {'burst_requests': 20, 'burst_window': 60})
            max_requests = limits['burst_requests']
            window_seconds = limits['burst_window']
            
            # Generate cache key
            base_key = f"emergency_burst:{action}:{user_id}"
            if identifier:
                base_key += f":{identifier}"
            
            current_window = int(time.time() // window_seconds) * window_seconds
            window_key = f"{base_key}:{current_window}"
            
            # Get current count
            current_count = self.redis_client.get(window_key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            # Check if limit exceeded
            is_allowed = current_count < max_requests
            
            burst_info = {
                'action': action,
                'current_count': current_count,
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'is_allowed': is_allowed,
                'remaining': max(0, max_requests - current_count),
            }
            
            return is_allowed, burst_info
            
        except Exception as e:
            logger.error(f"Burst limit check failed: {str(e)}")
            return True, {'error': str(e), 'is_allowed': True}
    
    def increment_burst_limit(self, user_id: str, action: str, 
                            identifier: str = None) -> Tuple[bool, Dict]:
        """
        Increment burst rate limit counter.
        
        Args:
            user_id: User ID
            action: Action being performed
            identifier: Additional identifier
            
        Returns:
            Tuple of (is_allowed, burst_info)
        """
        try:
            limits = self.burst_limits.get(action, {'burst_requests': 20, 'burst_window': 60})
            max_requests = limits['burst_requests']
            window_seconds = limits['burst_window']
            
            # Generate cache key
            base_key = f"emergency_burst:{action}:{user_id}"
            if identifier:
                base_key += f":{identifier}"
            
            current_window = int(time.time() // window_seconds) * window_seconds
            window_key = f"{base_key}:{current_window}"
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, window_seconds)
            results = pipe.execute()
            
            current_count = results[0]
            is_allowed = current_count <= max_requests
            
            burst_info = {
                'action': action,
                'current_count': current_count,
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'is_allowed': is_allowed,
                'remaining': max(0, max_requests - current_count),
            }
            
            return is_allowed, burst_info
            
        except Exception as e:
            logger.error(f"Burst limit increment failed: {str(e)}")
            return True, {'error': str(e), 'is_allowed': True}


# Global rate limiter instances
emergency_rate_limiter = EmergencyRateLimiter()
emergency_burst_limiter = EmergencyBurstLimiter()
