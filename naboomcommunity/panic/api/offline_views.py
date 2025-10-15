"""
Offline Sync API Views
REST API endpoints for offline data synchronization.
"""

import logging
from typing import Dict, Any
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from ..api.throttling import EmergencyPanicThrottle
from ..services.offline_sync_service import OfflineSyncService
from ..models import EmergencyAuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def offline_panic_button(request):
    """
    Handle panic button activation when offline.
    
    Request Body:
    {
        "emergency_type": "panic|medical|fire|crime|accident",
        "location": {
            "latitude": -26.2041,
            "longitude": 28.0473,
            "accuracy": 10.5,
            "altitude": 1500.0,
            "heading": 45.0,
            "speed": 0.0
        },
        "device_info": {
            "device_id": "device-123",
            "platform": "android|ios|web",
            "app_version": "1.0.0",
            "os_version": "11.0"
        },
        "context": {
            "description": "Emergency description",
            "severity": "low|medium|high|critical",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        "offline_data": {
            "emergency_location": [...],
            "emergency_medical": [...]
        }
    }
    
    Response:
    {
        "offline_id": "uuid",
        "status": "queued",
        "sync_required": true,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract request data
        emergency_type = request.data.get('emergency_type', 'panic')
        location_data = request.data.get('location', {})
        device_info = request.data.get('device_info', {})
        context = request.data.get('context', {})
        offline_data = request.data.get('offline_data', {})
        
        # Validate required fields
        if not device_info.get('device_id'):
            return Response({
                'error': 'device_id is required in device_info',
                'details': {'device_info': ['device_id field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not context.get('description'):
            return Response({
                'error': 'description is required in context',
                'details': {'context': ['description field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Create offline panic record
        offline_id = sync_service.create_offline_panic_record(
            request.user, emergency_type, location_data, device_info, context, offline_data
        )
        
        # Log offline panic activation
        try:
            EmergencyAuditLog.log_action(
                action_type='offline_panic_activated',
                description=f'Offline panic button activated for {emergency_type}',
                user=request.user,
                severity='critical',
                emergency_type=emergency_type,
                offline_id=offline_id,
                device_info=device_info
            )
        except Exception as e:
            logger.warning(f"Failed to log offline panic activation: {str(e)}")
        
        return Response({
            'offline_id': offline_id,
            'status': 'queued',
            'sync_required': True,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Offline panic button activation failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def sync_offline_data(request):
    """
    Sync offline data with server.
    
    Request Body:
    {
        "session_id": "uuid",
        "device_id": "device-123",
        "sync_type": "full|incremental|emergency_only",
        "offline_data": {
            "emergency_location": [
                {
                    "id": "uuid",
                    "operation": "create|update|delete",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "latitude": -26.2041,
                    "longitude": 28.0473,
                    "accuracy": 10.5,
                    "emergency_type": "panic"
                }
            ],
            "emergency_medical": [
                {
                    "id": "uuid",
                    "operation": "create|update|delete",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "blood_type": "O+",
                    "allergies": [],
                    "medications": []
                }
            ]
        },
        "checksum": "md5_checksum"
    }
    
    Response:
    {
        "session_id": "uuid",
        "status": "synced",
        "synced_items": 5,
        "conflicts": 1,
        "errors": 0,
        "conflict_resolutions": [...],
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        session_id = request.data.get('session_id')
        device_id = request.data.get('device_id')
        sync_type = request.data.get('sync_type', 'full')
        offline_data = request.data.get('offline_data', {})
        checksum = request.data.get('checksum')
        
        # Validate required fields
        if not session_id:
            return Response({
                'error': 'session_id is required',
                'details': {'session_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not device_id:
            return Response({
                'error': 'device_id is required',
                'details': {'device_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Validate sync data
        validation = sync_service.validate_sync_data(offline_data)
        if not validation['valid']:
            return Response({
                'error': 'Invalid sync data',
                'details': validation['errors'],
                'warnings': validation.get('warnings', [])
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify checksum if provided
        if checksum:
            expected_checksum = sync_service.generate_sync_checksum(offline_data)
            if checksum != expected_checksum:
                return Response({
                    'error': 'Checksum mismatch',
                    'details': {'checksum': ['Data integrity check failed']}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Sync offline data
        result = sync_service.sync_offline_data(request.user, session_id, offline_data)
        
        if result['success']:
            # Log sync operation
            try:
                EmergencyAuditLog.log_action(
                    action_type='offline_sync',
                    description=f'Offline data synced successfully',
                    user=request.user,
                    severity='low',
                    session_id=session_id,
                    synced_items=result.get('synced_items', 0),
                    conflicts=result.get('conflicts', 0),
                    errors=result.get('errors', 0)
                )
            except Exception as e:
                logger.warning(f"Failed to log offline sync: {str(e)}")
            
            return Response({
                'session_id': session_id,
                'status': 'synced',
                'synced_items': result.get('synced_items', 0),
                'conflicts': result.get('conflicts', 0),
                'errors': result.get('errors', 0),
                'conflict_resolutions': result.get('conflict_resolutions', []),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Sync failed'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Offline data sync failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def create_sync_session(request):
    """
    Create a new offline sync session.
    
    Request Body:
    {
        "device_id": "device-123",
        "sync_type": "full|incremental|emergency_only"
    }
    
    Response:
    {
        "session_id": "uuid",
        "sync_type": "full",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        device_id = request.data.get('device_id')
        sync_type = request.data.get('sync_type', 'full')
        
        # Validate required fields
        if not device_id:
            return Response({
                'error': 'device_id is required',
                'details': {'device_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate sync type
        valid_sync_types = ['full', 'incremental', 'emergency_only']
        if sync_type not in valid_sync_types:
            return Response({
                'error': f'Invalid sync_type. Must be one of: {valid_sync_types}',
                'details': {'sync_type': [f'Must be one of: {valid_sync_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Create sync session
        result = sync_service.create_sync_session(request.user, device_id, sync_type)
        
        if result['success']:
            return Response({
                'session_id': result['session_id'],
                'sync_type': sync_type,
                'timestamp': result['timestamp']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result.get('error', 'Failed to create sync session'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Create sync session failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def close_sync_session(request):
    """
    Close an offline sync session.
    
    Request Body:
    {
        "session_id": "uuid"
    }
    
    Response:
    {
        "session_id": "uuid",
        "status": "closed",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        session_id = request.data.get('session_id')
        
        # Validate required fields
        if not session_id:
            return Response({
                'error': 'session_id is required',
                'details': {'session_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Close sync session
        result = sync_service.close_sync_session(session_id)
        
        if result['success']:
            return Response({
                'session_id': session_id,
                'status': 'closed',
                'timestamp': result['timestamp']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Failed to close sync session'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Close sync session failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_offline_data(request):
    """
    Get user's offline data for synchronization.
    
    Query Parameters:
    - data_types: Comma-separated list of data types (optional)
    - session_id: Sync session ID (optional)
    
    Response:
    {
        "data": {
            "emergency_location": [...],
            "emergency_medical": [...]
        },
        "checksum": "md5_checksum",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        data_types = request.query_params.get('data_types')
        session_id = request.query_params.get('session_id')
        
        # Parse data types
        if data_types:
            data_types = [dt.strip() for dt in data_types.split(',')]
        else:
            data_types = None
        
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Get offline data
        result = sync_service.get_user_offline_data(request.user, data_types)
        
        if result['success']:
            # Generate checksum
            checksum = sync_service.generate_sync_checksum(result['data'])
            
            return Response({
                'data': result['data'],
                'checksum': checksum,
                'timestamp': result['timestamp']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Failed to get offline data'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Get offline data failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_sync_status(request, session_id):
    """
    Get sync session status.
    
    URL Parameters:
    - session_id: Sync session ID
    
    Response:
    {
        "session_id": "uuid",
        "status": "active|closed|error",
        "sync_type": "full",
        "total_items": 10,
        "synced_items": 8,
        "conflicts": 1,
        "errors": 1,
        "created_at": "2024-01-01T12:00:00Z",
        "last_activity": "2024-01-01T12:05:00Z"
    }
    """
    try:
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Get sync session
        session = sync_service.get_sync_session(session_id)
        
        if not session:
            return Response({
                'error': 'Sync session not found',
                'session_id': session_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check ownership
        if session['user_id'] != request.user.id:
            return Response({
                'error': 'Unauthorized access to sync session',
                'session_id': session_id
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'session_id': session_id,
            'status': session['status'],
            'sync_type': session['sync_type'],
            'total_items': session.get('total_items', 0),
            'synced_items': session.get('synced_items', 0),
            'conflicts': session.get('conflicts', 0),
            'errors': session.get('errors', 0),
            'created_at': session['created_at'],
            'last_activity': session['last_activity']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get sync status failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def resolve_sync_conflicts(request):
    """
    Resolve sync conflicts.
    
    Request Body:
    {
        "session_id": "uuid",
        "conflicts": [
            {
                "data_type": "emergency_location",
                "item_id": "uuid",
                "resolution": "server_wins|client_wins|merge"
            }
        ]
    }
    
    Response:
    {
        "session_id": "uuid",
        "resolved_conflicts": 1,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        session_id = request.data.get('session_id')
        conflicts = request.data.get('conflicts', [])
        
        # Validate required fields
        if not session_id:
            return Response({
                'error': 'session_id is required',
                'details': {'session_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not conflicts:
            return Response({
                'error': 'conflicts array is required',
                'details': {'conflicts': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize offline sync service
        sync_service = OfflineSyncService()
        
        # Resolve conflicts
        result = sync_service.resolve_sync_conflicts(request.user, session_id, conflicts)
        
        if result['success']:
            return Response({
                'session_id': session_id,
                'resolved_conflicts': result.get('resolved_conflicts', 0),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Failed to resolve conflicts'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Resolve sync conflicts failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)