"""
WebSocket API Views
REST API endpoints for WebSocket connection management and status.
"""

import logging
import json
from typing import Dict, Any
from django.utils import timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from ..api.throttling import EmergencyPanicThrottle
from ..models import EmergencyAuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def websocket_status(request):
    """
    Get WebSocket connection status and statistics.
    
    Query Parameters:
    - room: Room name for status (optional)
    
    Response:
    {
        "status": "active",
        "connections": 15,
        "rooms": ["emergency_general", "emergency_123"],
        "user_connections": 2,
        "last_activity": "2024-01-01T12:00:00Z"
    }
    """
    try:
        room = request.query_params.get('room', 'general')
        
        # Get connection statistics
        stats = get_websocket_statistics(room)
        
        return Response({
            'status': 'active',
            'connections': stats.get('total_connections', 0),
            'rooms': stats.get('active_rooms', []),
            'user_connections': stats.get('user_connections', 0),
            'last_activity': stats.get('last_activity', timezone.now().isoformat()),
            'room': room
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"WebSocket status retrieval failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def websocket_subscribe(request):
    """
    Subscribe to emergency updates via WebSocket.
    
    Request Body:
    {
        "emergency_id": "uuid",
        "room": "emergency_general",
        "subscription_type": "emergency|location|medical|all"
    }
    
    Response:
    {
        "subscription_id": "uuid",
        "status": "subscribed",
        "room": "emergency_general",
        "subscription_type": "emergency",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        emergency_id = request.data.get('emergency_id')
        room = request.data.get('room', 'general')
        subscription_type = request.data.get('subscription_type', 'emergency')
        
        # Validate subscription type
        valid_types = ['emergency', 'location', 'medical', 'all']
        if subscription_type not in valid_types:
            return Response({
                'error': f'Invalid subscription_type. Must be one of: {valid_types}',
                'details': {'subscription_type': [f'Must be one of: {valid_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create subscription
        subscription_id = create_websocket_subscription(
            request.user, emergency_id, room, subscription_type
        )
        
        # Log subscription
        try:
            EmergencyAuditLog.log_action(
                action_type='websocket_subscribe',
                description=f'WebSocket subscription created for {subscription_type}',
                user=request.user,
                severity='low',
                emergency_id=emergency_id,
                room=room,
                subscription_type=subscription_type
            )
        except Exception as e:
            logger.warning(f"Failed to log WebSocket subscription: {str(e)}")
        
        return Response({
            'subscription_id': subscription_id,
            'status': 'subscribed',
            'room': room,
            'subscription_type': subscription_type,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"WebSocket subscription failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def websocket_unsubscribe(request):
    """
    Unsubscribe from emergency updates via WebSocket.
    
    Request Body:
    {
        "subscription_id": "uuid",
        "emergency_id": "uuid"
    }
    
    Response:
    {
        "subscription_id": "uuid",
        "status": "unsubscribed",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        subscription_id = request.data.get('subscription_id')
        emergency_id = request.data.get('emergency_id')
        
        if not subscription_id:
            return Response({
                'error': 'subscription_id is required',
                'details': {'subscription_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove subscription
        result = remove_websocket_subscription(
            request.user, subscription_id, emergency_id
        )
        
        if not result['success']:
            return Response({
                'error': result['error'],
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log unsubscription
        try:
            EmergencyAuditLog.log_action(
                action_type='websocket_unsubscribe',
                description='WebSocket subscription removed',
                user=request.user,
                severity='low',
                emergency_id=emergency_id,
                subscription_id=subscription_id
            )
        except Exception as e:
            logger.warning(f"Failed to log WebSocket unsubscription: {str(e)}")
        
        return Response({
            'subscription_id': subscription_id,
            'status': 'unsubscribed',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"WebSocket unsubscription failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def websocket_subscriptions(request):
    """
    Get user's WebSocket subscriptions.
    
    Query Parameters:
    - emergency_id: Filter by emergency ID (optional)
    - subscription_type: Filter by subscription type (optional)
    
    Response:
    {
        "subscriptions": [
            {
                "subscription_id": "uuid",
                "emergency_id": "uuid",
                "room": "emergency_general",
                "subscription_type": "emergency",
                "created_at": "2024-01-01T12:00:00Z",
                "status": "active"
            }
        ],
        "total": 1
    }
    """
    try:
        emergency_id = request.query_params.get('emergency_id')
        subscription_type = request.query_params.get('subscription_type')
        
        # Get user subscriptions
        subscriptions = get_user_websocket_subscriptions(
            request.user, emergency_id, subscription_type
        )
        
        return Response({
            'subscriptions': subscriptions,
            'total': len(subscriptions)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"WebSocket subscriptions retrieval failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def websocket_broadcast(request):
    """
    Broadcast message to WebSocket subscribers.
    
    Request Body:
    {
        "room": "emergency_general",
        "message_type": "emergency_status_update",
        "data": {...},
        "target_users": [1, 2, 3]  # Optional: specific user IDs
    }
    
    Response:
    {
        "broadcast_id": "uuid",
        "status": "sent",
        "recipients": 15,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        room = request.data.get('room')
        message_type = request.data.get('message_type')
        data = request.data.get('data', {})
        target_users = request.data.get('target_users', [])
        
        # Validate required fields
        if not room:
            return Response({
                'error': 'room is required',
                'details': {'room': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not message_type:
            return Response({
                'error': 'message_type is required',
                'details': {'message_type': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Broadcast message
        result = broadcast_websocket_message(
            room, message_type, data, target_users
        )
        
        # Log broadcast
        try:
            EmergencyAuditLog.log_action(
                action_type='websocket_broadcast',
                description=f'WebSocket message broadcast to {room}',
                user=request.user,
                severity='low',
                room=room,
                message_type=message_type,
                recipients=result.get('recipients', 0)
            )
        except Exception as e:
            logger.warning(f"Failed to log WebSocket broadcast: {str(e)}")
        
        return Response({
            'broadcast_id': result['broadcast_id'],
            'status': 'sent',
            'recipients': result['recipients'],
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"WebSocket broadcast failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_websocket_statistics(room: str) -> Dict[str, Any]:
    """
    Get WebSocket connection statistics.
    
    Args:
        room: Room name
        
    Returns:
        Statistics dictionary
    """
    try:
        # This would typically query the WebSocket connection manager
        # For now, return mock data
        return {
            'total_connections': 15,
            'active_rooms': ['emergency_general', 'emergency_123'],
            'user_connections': 2,
            'last_activity': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get WebSocket statistics: {str(e)}")
        return {
            'total_connections': 0,
            'active_rooms': [],
            'user_connections': 0,
            'last_activity': timezone.now().isoformat()
        }


def create_websocket_subscription(user: User, emergency_id: str, room: str, 
                                subscription_type: str) -> str:
    """
    Create WebSocket subscription.
    
    Args:
        user: User instance
        emergency_id: Emergency ID
        room: Room name
        subscription_type: Type of subscription
        
    Returns:
        Subscription ID
    """
    try:
        import uuid
        subscription_id = str(uuid.uuid4())
        
        # Store subscription in cache
        cache_key = f"websocket_subscription:{subscription_id}"
        cache.set(cache_key, {
            'subscription_id': subscription_id,
            'user_id': user.id,
            'emergency_id': emergency_id,
            'room': room,
            'subscription_type': subscription_type,
            'created_at': timezone.now().isoformat(),
            'status': 'active'
        }, 3600)  # 1 hour
        
        # Add to user's subscription list
        user_subscriptions_key = f"user_websocket_subscriptions:{user.id}"
        user_subscriptions = cache.get(user_subscriptions_key, [])
        user_subscriptions.append(subscription_id)
        cache.set(user_subscriptions_key, user_subscriptions, 3600)
        
        return subscription_id
        
    except Exception as e:
        logger.error(f"Failed to create WebSocket subscription: {str(e)}")
        raise


def remove_websocket_subscription(user: User, subscription_id: str, 
                                emergency_id: str) -> Dict[str, Any]:
    """
    Remove WebSocket subscription.
    
    Args:
        user: User instance
        subscription_id: Subscription ID
        emergency_id: Emergency ID
        
    Returns:
        Result dictionary
    """
    try:
        # Get subscription
        cache_key = f"websocket_subscription:{subscription_id}"
        subscription = cache.get(cache_key)
        
        if not subscription:
            return {
                'success': False,
                'error': 'Subscription not found'
            }
        
        # Check ownership
        if subscription['user_id'] != user.id:
            return {
                'success': False,
                'error': 'Unauthorized to remove this subscription'
            }
        
        # Remove subscription
        cache.delete(cache_key)
        
        # Remove from user's subscription list
        user_subscriptions_key = f"user_websocket_subscriptions:{user.id}"
        user_subscriptions = cache.get(user_subscriptions_key, [])
        if subscription_id in user_subscriptions:
            user_subscriptions.remove(subscription_id)
            cache.set(user_subscriptions_key, user_subscriptions, 3600)
        
        return {
            'success': True,
            'message': 'Subscription removed successfully'
        }
        
    except Exception as e:
        logger.error(f"Failed to remove WebSocket subscription: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to remove subscription',
            'details': str(e)
        }


def get_user_websocket_subscriptions(user: User, emergency_id: str = None, 
                                   subscription_type: str = None) -> list:
    """
    Get user's WebSocket subscriptions.
    
    Args:
        user: User instance
        emergency_id: Filter by emergency ID
        subscription_type: Filter by subscription type
        
    Returns:
        List of subscriptions
    """
    try:
        user_subscriptions_key = f"user_websocket_subscriptions:{user.id}"
        subscription_ids = cache.get(user_subscriptions_key, [])
        
        subscriptions = []
        for subscription_id in subscription_ids:
            cache_key = f"websocket_subscription:{subscription_id}"
            subscription = cache.get(cache_key)
            
            if subscription:
                # Apply filters
                if emergency_id and subscription.get('emergency_id') != emergency_id:
                    continue
                if subscription_type and subscription.get('subscription_type') != subscription_type:
                    continue
                
                subscriptions.append(subscription)
        
        return subscriptions
        
    except Exception as e:
        logger.error(f"Failed to get user WebSocket subscriptions: {str(e)}")
        return []


def broadcast_websocket_message(room: str, message_type: str, data: Dict[str, Any], 
                              target_users: list = None) -> Dict[str, Any]:
    """
    Broadcast message to WebSocket subscribers.
    
    Args:
        room: Room name
        message_type: Type of message
        data: Message data
        target_users: Specific user IDs (optional)
        
    Returns:
        Broadcast result
    """
    try:
        import uuid
        broadcast_id = str(uuid.uuid4())
        
        # This would typically send the message through the WebSocket channel layer
        # For now, return mock data
        return {
            'broadcast_id': broadcast_id,
            'recipients': 15,
            'status': 'sent'
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast WebSocket message: {str(e)}")
        return {
            'broadcast_id': str(uuid.uuid4()),
            'recipients': 0,
            'status': 'failed'
        }