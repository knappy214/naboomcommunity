"""
Emergency WebSocket Authentication
Authentication and authorization for emergency WebSocket connections.
"""

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import json
import logging

from ..auth.emergency_permissions import EmergencyUserPermission, EmergencyUserRole
from ..rate_limiting.emergency_rate_limits import emergency_rate_limiter

User = get_user_model()
logger = logging.getLogger(__name__)


class EmergencyWebSocketAuthMixin:
    """
    Mixin for emergency WebSocket authentication and authorization.
    """
    
    async def authenticate_user(self, token: str = None, user_id: str = None) -> User:
        """
        Authenticate user for WebSocket connection.
        
        Args:
            token: Authentication token
            user_id: User ID for direct authentication
            
        Returns:
            Authenticated user or AnonymousUser
        """
        try:
            if user_id:
                user = await self.get_user_by_id(user_id)
                if user and user.is_authenticated:
                    return user
            
            if token:
                user = await self.get_user_by_token(token)
                if user and user.is_authenticated:
                    return user
            
            return AnonymousUser()
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {str(e)}")
            return AnonymousUser()
    
    @database_sync_to_async
    def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_user_by_token(self, token: str) -> User:
        """Get user by authentication token."""
        try:
            # This would integrate with your token authentication system
            # For now, we'll use a simple approach
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_decode
            
            # Decode token and get user
            # This is a simplified example - implement proper token validation
            return None
            
        except Exception as e:
            logger.error(f"Token authentication error: {str(e)}")
            return None
    
    async def check_websocket_permission(self, user: User, permission_type: str = 'websocket_connect') -> bool:
        """
        Check if user has WebSocket permission.
        
        Args:
            user: User to check
            permission_type: Type of permission required
            
        Returns:
            True if user has permission
        """
        try:
            if not user.is_authenticated:
                return False
            
            # Check emergency override
            if await self.has_emergency_override(user):
                return True
            
            # Check user permissions
            has_permission = await self.check_user_permission(user, permission_type, 'own')
            if has_permission:
                return True
            
            # Check role permissions
            has_role_permission = await self.check_role_permission(user, permission_type, 'own')
            if has_role_permission:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"WebSocket permission check error: {str(e)}")
            return False
    
    @database_sync_to_async
    def has_emergency_override(self, user: User) -> bool:
        """Check if user has emergency override permissions."""
        try:
            return user.emergency_roles.filter(
                role__role_type__in=['responder', 'coordinator', 'admin'],
                is_active=True
            ).exists()
        except Exception:
            return False
    
    @database_sync_to_async
    def check_user_permission(self, user: User, permission_type: str, scope_level: str) -> bool:
        """Check user-specific permissions."""
        try:
            permissions = EmergencyUserPermission.objects.filter(
                user=user,
                permission__permission_type=permission_type,
                permission__scope_level=scope_level,
                is_active=True
            )
            
            for perm in permissions:
                if perm.is_valid():
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"User permission check error: {str(e)}")
            return False
    
    @database_sync_to_async
    def check_role_permission(self, user: User, permission_type: str, scope_level: str) -> bool:
        """Check role-based permissions."""
        try:
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
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Role permission check error: {str(e)}")
            return False
    
    async def check_rate_limit(self, user: User, action: str = 'websocket_connect') -> bool:
        """
        Check rate limit for WebSocket connection.
        
        Args:
            user: User making connection
            action: Action being rate limited
            
        Returns:
            True if within rate limits
        """
        try:
            if not user.is_authenticated:
                return True  # Anonymous users have different limits
            
            user_id = str(user.id)
            identifier = self.scope.get('client', ['unknown'])[0]
            
            # Check emergency override
            if emergency_rate_limiter.get_emergency_override(user_id, action):
                return True
            
            # Check rate limit
            is_allowed, rate_info = emergency_rate_limiter.check_rate_limit(
                user_id, action, identifier=identifier
            )
            
            if not is_allowed:
                logger.warning(f"WebSocket rate limit exceeded for user {user_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket rate limit check error: {str(e)}")
            return True  # Fail open for emergency situations
    
    async def log_websocket_connection(self, user: User, action: str, success: bool, error: str = None):
        """
        Log WebSocket connection event.
        
        Args:
            user: User making connection
            action: Connection action
            success: Whether connection was successful
            error: Error message if any
        """
        try:
            from ..models.emergency_audit import EmergencyAuditLog
            
            await database_sync_to_async(EmergencyAuditLog.log_action)(
                action_type=action,
                description=f"WebSocket {action}",
                user=user if user.is_authenticated else None,
                severity='medium' if success else 'high',
                ip_address=self.scope.get('client', ['unknown'])[0],
                user_agent=self.scope.get('headers', {}).get(b'user-agent', b'').decode('utf-8', errors='ignore'),
                session_id=self.scope.get('session', {}).get('session_key'),
                metadata={
                    'websocket_channel': self.channel_name,
                    'success': success,
                    'error': error
                }
            )
            
        except Exception as e:
            logger.error(f"WebSocket logging error: {str(e)}")
    
    async def send_error_message(self, error_type: str, message: str, code: int = 4000):
        """
        Send error message to WebSocket client.
        
        Args:
            error_type: Type of error
            message: Error message
            code: Error code
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error_type': error_type,
                'message': message,
                'code': code,
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
    
    async def send_success_message(self, message_type: str, data: dict = None):
        """
        Send success message to WebSocket client.
        
        Args:
            message_type: Type of message
            data: Additional data
        """
        try:
            message = {
                'type': 'success',
                'message_type': message_type,
                'timestamp': timezone.now().isoformat()
            }
            
            if data:
                message.update(data)
            
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket success message: {str(e)}")


class EmergencyWebSocketConsumer(EmergencyWebSocketAuthMixin, AsyncWebsocketConsumer):
    """
    Base WebSocket consumer for emergency operations with authentication.
    """
    
    async def connect(self):
        """Handle WebSocket connection with authentication."""
        try:
            # Extract authentication from query parameters or headers
            token = self.scope.get('query_string', b'').decode('utf-8')
            user_id = self.scope.get('url_route', {}).get('kwargs', {}).get('user_id')
            
            # Authenticate user
            self.user = await self.authenticate_user(token, user_id)
            
            if not self.user.is_authenticated:
                await self.log_websocket_connection(
                    self.user, 'websocket_connect', False, 'Authentication required'
                )
                await self.send_error_message('authentication_required', 'Authentication required', 4001)
                await self.close()
                return
            
            # Check WebSocket permission
            has_permission = await self.check_websocket_permission(self.user)
            if not has_permission:
                await self.log_websocket_connection(
                    self.user, 'websocket_connect', False, 'Permission denied'
                )
                await self.send_error_message('permission_denied', 'WebSocket permission required', 4003)
                await self.close()
                return
            
            # Check rate limit
            rate_limit_ok = await self.check_rate_limit(self.user)
            if not rate_limit_ok:
                await self.log_websocket_connection(
                    self.user, 'websocket_connect', False, 'Rate limit exceeded'
                )
                await self.send_error_message('rate_limit_exceeded', 'Rate limit exceeded', 4029)
                await self.close()
                return
            
            # Accept connection
            await self.accept()
            
            # Log successful connection
            await self.log_websocket_connection(
                self.user, 'websocket_connect', True
            )
            
            # Send welcome message
            await self.send_success_message('connected', {
                'user_id': str(self.user.id),
                'username': self.user.username,
                'channel': self.channel_name
            })
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.send_error_message('connection_error', 'Connection failed', 4500)
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            if hasattr(self, 'user') and self.user.is_authenticated:
                await self.log_websocket_connection(
                    self.user, 'websocket_disconnect', True
                )
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if not message_type:
                await self.send_error_message('invalid_message', 'Message type required', 4000)
                return
            
            # Route message to appropriate handler
            handler_name = f"handle_{message_type}"
            if hasattr(self, handler_name):
                await getattr(self, handler_name)(data)
            else:
                await self.send_error_message('unknown_message_type', f'Unknown message type: {message_type}', 4000)
                
        except json.JSONDecodeError:
            await self.send_error_message('invalid_json', 'Invalid JSON format', 4000)
        except Exception as e:
            logger.error(f"WebSocket message handling error: {str(e)}")
            await self.send_error_message('message_error', 'Message processing failed', 4500)
    
    async def handle_ping(self, data):
        """Handle ping messages."""
        await self.send_success_message('pong', {
            'timestamp': timezone.now().isoformat()
        })
    
    async def handle_authenticate(self, data):
        """Handle authentication messages."""
        # This could be used for re-authentication during the session
        await self.send_success_message('authenticated', {
            'user_id': str(self.user.id),
            'username': self.user.username
        })
