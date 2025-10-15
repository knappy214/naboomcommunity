"""
Enhanced Emergency Response API Views
High-performance API endpoints for emergency response operations.
"""

import logging
import time
import uuid
from typing import Dict, Any
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth import get_user_model

from ..models import EmergencyLocation, EmergencyMedical, EmergencyAuditLog
from ..services.location_service import LocationService
from ..services.medical_service import MedicalService
from ..api.throttling import EmergencyPanicThrottle
from ..tasks.emergency_tasks import (
    process_panic_button_activation,
    process_location_update,
    process_medical_data,
    send_emergency_notification
)

User = get_user_model()
logger = logging.getLogger(__name__)


class EmergencyPanicThrottleView:
    """Custom throttle class for emergency panic button."""
    throttle_classes = [EmergencyPanicThrottle]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def enhanced_panic_button(request):
    """
    Enhanced panic button activation endpoint.
    
    Processes panic button activation with location data, medical information,
    and emergency notifications in under 5 seconds.
    
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
        }
    }
    
    Response:
    {
        "emergency_id": "uuid",
        "status": "activated",
        "timestamp": "2024-01-01T12:00:00Z",
        "location_processed": true,
        "medical_data_retrieved": true,
        "notifications_sent": true,
        "response_time_ms": 1500
    }
    """
    start_time = time.time()
    
    try:
        # Extract request data
        emergency_type = request.data.get('emergency_type', 'panic')
        location_data = request.data.get('location', {})
        device_info = request.data.get('device_info', {})
        context = request.data.get('context', {})
        
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
        
        # Validate emergency type
        valid_emergency_types = ['panic', 'medical', 'fire', 'crime', 'accident']
        if emergency_type not in valid_emergency_types:
            return Response({
                'error': f'Invalid emergency_type. Must be one of: {valid_emergency_types}',
                'details': {'emergency_type': [f'Must be one of: {valid_emergency_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate emergency ID
        emergency_id = str(uuid.uuid4())
        
        # Initialize services
        location_service = LocationService()
        medical_service = MedicalService()
        
        # Process location data
        location_processed = False
        location_result = None
        if location_data:
            location_result = location_service.process_location_update(
                request.user, location_data
            )
            location_processed = location_result.get('success', False)
        
        # Retrieve medical data
        medical_data_retrieved = False
        medical_data = None
        try:
            medical_result = medical_service.get_medical_data(request.user, 'emergency_only')
            medical_data_retrieved = medical_result.get('success', False)
            medical_data = medical_result if medical_data_retrieved else None
        except Exception as e:
            logger.warning(f"Failed to retrieve medical data: {str(e)}")
        
        # Send emergency notifications
        notifications_sent = False
        try:
            notification_data = {
                'emergency_id': emergency_id,
                'emergency_type': emergency_type,
                'user_id': request.user.id,
                'location': location_data,
                'medical_data': medical_data,
                'device_info': device_info,
                'context': context
            }
            
            # Queue notification task
            send_emergency_notification.delay(
                request.user.id, notification_data
            )
            notifications_sent = True
        except Exception as e:
            logger.warning(f"Failed to queue emergency notification: {str(e)}")
        
        # Queue background tasks
        try:
            # Queue location processing task
            if location_data:
                process_location_update.delay(
                    request.user.id, location_data
                )
            
            # Queue medical data processing task
            if medical_data:
                process_medical_data.delay(
                    request.user.id, medical_data
                )
            
            # Queue panic button activation task
            process_panic_button_activation.delay(
                request.user.id, {
                    'emergency_id': emergency_id,
                    'emergency_type': emergency_type,
                    'location_data': location_data,
                    'device_info': device_info,
                    'context': context
                }
            )
        except Exception as e:
            logger.warning(f"Failed to queue background tasks: {str(e)}")
        
        # Log emergency activation
        try:
            EmergencyAuditLog.log_panic_activation(
                user=request.user,
                location_data=location_data,
                emergency_type=emergency_type,
                emergency_id=emergency_id,
                device_info=device_info,
                context=context
            )
        except Exception as e:
            logger.warning(f"Failed to log panic activation: {str(e)}")
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Prepare response
        response_data = {
            'emergency_id': emergency_id,
            'status': 'activated',
            'timestamp': timezone.now().isoformat(),
            'location_processed': location_processed,
            'medical_data_retrieved': medical_data_retrieved,
            'notifications_sent': notifications_sent,
            'response_time_ms': response_time_ms
        }
        
        # Add location details if processed
        if location_processed and location_result:
            response_data['location_details'] = {
                'accuracy_level': location_result.get('accuracy_level'),
                'warnings': location_result.get('warnings', [])
            }
        
        # Add medical details if retrieved
        if medical_data_retrieved and medical_data:
            response_data['medical_details'] = {
                'consent_level': medical_data.get('consent_level'),
                'has_emergency_contact': bool(medical_data.get('emergency_contact', {}).get('name')),
                'critical_allergies': len(medical_data.get('allergies', [])),
                'critical_conditions': len(medical_data.get('medical_conditions', []))
            }
        
        logger.info(f"Emergency {emergency_id} activated for user {request.user.id} in {response_time_ms}ms")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Enhanced panic button activation failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def location_accuracy_validation(request):
    """
    Validate GPS accuracy for emergency location data.
    
    Request Body:
    {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "accuracy": 10.5,
        "altitude": 1500.0,
        "heading": 45.0,
        "speed": 0.0,
        "timestamp": "2024-01-01T12:00:00Z",
        "source": "gps|network|passive|fused"
    }
    
    Response:
    {
        "is_valid": true,
        "accuracy_level": "high",
        "accuracy": 10.5,
        "warnings": [],
        "thresholds": {...}
    }
    """
    try:
        location_service = LocationService()
        
        # Validate location data
        validation_result = location_service.validate_location_data(request.data)
        
        if validation_result['is_valid']:
            return Response(validation_result, status=status.HTTP_200_OK)
        else:
            return Response(validation_result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Location accuracy validation failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def location_batch_accuracy(request):
    """
    Validate GPS accuracy for multiple location data points.
    
    Request Body:
    {
        "locations": [
            {
                "latitude": -26.2041,
                "longitude": 28.0473,
                "accuracy": 10.5,
                "timestamp": "2024-01-01T12:00:00Z",
                "source": "gps"
            },
            ...
        ],
        "user_id": 123
    }
    
    Response:
    {
        "results": [
            {
                "is_valid": true,
                "accuracy_level": "high",
                "accuracy": 10.5,
                "warnings": []
            },
            ...
        ]
    }
    """
    try:
        locations = request.data.get('locations', [])
        user_id = request.data.get('user_id')
        
        if not locations:
            return Response({
                'error': 'locations array is required',
                'details': {'locations': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(locations) > 100:  # Limit batch size
            return Response({
                'error': 'Too many locations in batch',
                'details': {'locations': ['Maximum 100 locations allowed per batch']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        location_service = LocationService()
        results = []
        
        for location_data in locations:
            validation_result = location_service.validate_location_data(location_data)
            results.append({
                'is_valid': validation_result['is_valid'],
                'accuracy_level': validation_result['accuracy_validation']['level'],
                'accuracy': validation_result['accuracy_validation']['accuracy'],
                'warnings': validation_result['warnings'],
                'errors': validation_result['errors']
            })
        
        return Response({'results': results}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Location batch accuracy validation failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def medical_data(request):
    """
    Retrieve medical data for emergency response.
    
    Query Parameters:
    - consent_level: basic|emergency_only|full (default: basic)
    
    Response:
    {
        "success": true,
        "consent_level": "emergency_only",
        "emergency_contact": {...},
        "blood_type": "O+",
        "allergies": [...],
        "medical_conditions": [...],
        "medications": [...]
    }
    """
    try:
        consent_level = request.query_params.get('consent_level', 'basic')
        
        medical_service = MedicalService()
        result = medical_service.get_medical_data(request.user, consent_level)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Medical data retrieval failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def send_emergency_notification(request):
    """
    Send emergency notification to family and contacts.
    
    Request Body:
    {
        "emergency_id": "uuid",
        "emergency_type": "panic",
        "channels": ["sms", "email", "push"],
        "recipients": [
            {
                "type": "emergency_contact",
                "name": "John Doe",
                "phone": "+27123456789",
                "email": "john@example.com"
            }
        ],
        "message": "Emergency situation requiring immediate assistance",
        "priority": "high"
    }
    
    Response:
    {
        "notification_id": "uuid",
        "status": "queued",
        "channels_sent": ["sms", "email"],
        "recipients_notified": 2,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        emergency_id = request.data.get('emergency_id')
        emergency_type = request.data.get('emergency_type', 'panic')
        channels = request.data.get('channels', [])
        recipients = request.data.get('recipients', [])
        message = request.data.get('message', '')
        priority = request.data.get('priority', 'high')
        
        # Validate required fields
        if not emergency_id:
            return Response({
                'error': 'emergency_id is required',
                'details': {'emergency_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not channels:
            return Response({
                'error': 'channels array is required',
                'details': {'channels': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not recipients:
            return Response({
                'error': 'recipients array is required',
                'details': {'recipients': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate channels
        valid_channels = ['sms', 'email', 'push', 'ussd']
        invalid_channels = [ch for ch in channels if ch not in valid_channels]
        if invalid_channels:
            return Response({
                'error': f'Invalid channels: {invalid_channels}',
                'details': {'channels': [f'Must be one of: {valid_channels}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare notification data
        notification_data = {
            'emergency_id': emergency_id,
            'emergency_type': emergency_type,
            'channels': channels,
            'recipients': recipients,
            'message': message,
            'priority': priority,
            'user_id': request.user.id
        }
        
        # Queue notification task
        task_result = send_emergency_notification.delay(
            request.user.id, notification_data
        )
        
        # Generate notification ID
        notification_id = str(uuid.uuid4())
        
        # Log notification
        try:
            EmergencyAuditLog.log_action(
                action_type='notification_send',
                description=f'Emergency notification queued for {emergency_type}',
                user=request.user,
                severity='medium',
                emergency_id=emergency_id,
                notification_id=notification_id,
                channels=channels,
                recipient_count=len(recipients)
            )
        except Exception as e:
            logger.warning(f"Failed to log notification: {str(e)}")
        
        return Response({
            'notification_id': notification_id,
            'status': 'queued',
            'channels_sent': channels,
            'recipients_notified': len(recipients),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Emergency notification sending failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def emergency_status(request, emergency_id):
    """
    Get status of an emergency response.
    
    URL Parameters:
    - emergency_id: UUID of the emergency
    
    Response:
    {
        "emergency_id": "uuid",
        "status": "active|resolved|cancelled",
        "created_at": "2024-01-01T12:00:00Z",
        "location_processed": true,
        "medical_data_retrieved": true,
        "notifications_sent": true,
        "response_time_ms": 1500
    }
    """
    try:
        # This would typically query the database for emergency status
        # For now, return a basic response structure
        
        # Check if emergency exists in cache or database
        cache_key = f"emergency_status:{emergency_id}"
        cached_status = cache.get(cache_key)
        
        if cached_status:
            return Response(cached_status, status=status.HTTP_200_OK)
        
        # Default response if not found
        return Response({
            'emergency_id': emergency_id,
            'status': 'not_found',
            'message': 'Emergency not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Emergency status retrieval failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def update_emergency_status(request, emergency_id):
    """
    Update status of an emergency response.
    
    URL Parameters:
    - emergency_id: UUID of the emergency
    
    Request Body:
    {
        "status": "active|resolved|cancelled",
        "notes": "Status update notes"
    }
    
    Response:
    {
        "emergency_id": "uuid",
        "status": "updated",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        # Validate status
        valid_statuses = ['active', 'resolved', 'cancelled']
        if new_status not in valid_statuses:
            return Response({
                'error': f'Invalid status. Must be one of: {valid_statuses}',
                'details': {'status': [f'Must be one of: {valid_statuses}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update emergency status (this would typically update the database)
        # For now, update cache
        cache_key = f"emergency_status:{emergency_id}"
        cache.set(cache_key, {
            'emergency_id': emergency_id,
            'status': new_status,
            'updated_at': timezone.now().isoformat(),
            'notes': notes
        }, 3600)  # Cache for 1 hour
        
        # Log status update
        try:
            EmergencyAuditLog.log_action(
                action_type='status_changed',
                description=f'Emergency status updated to {new_status}',
                user=request.user,
                severity='medium',
                emergency_id=emergency_id,
                new_status=new_status,
                notes=notes
            )
        except Exception as e:
            logger.warning(f"Failed to log status update: {str(e)}")
        
        return Response({
            'emergency_id': emergency_id,
            'status': 'updated',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Emergency status update failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)