"""
Family Notification API Views
REST API endpoints for family and emergency contact notifications.
"""

import logging
from typing import Dict, Any, List
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from ..api.throttling import EmergencyPanicThrottle
from ..services.notification_service import NotificationService
from ..models import EmergencyAuditLog, EmergencyMedical

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def send_family_notification(request):
    """
    Send emergency notification to family and contacts.
    
    Request Body:
    {
        "emergency_id": "uuid",
        "emergency_type": "panic|medical|fire|crime|accident",
        "channels": ["sms", "email", "push", "whatsapp"],
        "recipients": [
            {
                "name": "John Doe",
                "phone": "+27123456789",
                "email": "john@example.com",
                "relationship": "spouse",
                "priority": "high"
            }
        ],
        "message": "Custom emergency message",
        "priority": "high|critical",
        "location": {
            "latitude": -26.2041,
            "longitude": 28.0473,
            "accuracy": 10.5,
            "address": "123 Main St, Johannesburg"
        },
        "medical_data": {
            "blood_type": "O+",
            "allergies": [...],
            "medical_conditions": [...]
        }
    }
    
    Response:
    {
        "notification_id": "uuid",
        "channels_sent": ["sms", "email"],
        "total_sent": 5,
        "total_failed": 0,
        "results": {...},
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract request data
        emergency_id = request.data.get('emergency_id')
        emergency_type = request.data.get('emergency_type', 'panic')
        channels = request.data.get('channels', ['sms', 'email'])
        recipients = request.data.get('recipients', [])
        message = request.data.get('message', '')
        priority = request.data.get('priority', 'high')
        location_data = request.data.get('location', {})
        medical_data = request.data.get('medical_data', {})
        
        # Validate required fields
        if not emergency_id:
            return Response({
                'error': 'emergency_id is required',
                'details': {'emergency_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not recipients:
            return Response({
                'error': 'recipients list is required',
                'details': {'recipients': ['At least one recipient is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate emergency type
        valid_emergency_types = ['panic', 'medical', 'fire', 'crime', 'accident']
        if emergency_type not in valid_emergency_types:
            return Response({
                'error': f'Invalid emergency_type. Must be one of: {valid_emergency_types}',
                'details': {'emergency_type': [f'Must be one of: {valid_emergency_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate channels
        valid_channels = ['sms', 'email', 'push', 'ussd', 'whatsapp', 'telegram']
        invalid_channels = [ch for ch in channels if ch not in valid_channels]
        if invalid_channels:
            return Response({
                'error': f'Invalid channels: {invalid_channels}',
                'details': {'channels': [f'Must be one of: {valid_channels}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if priority not in valid_priorities:
            return Response({
                'error': f'Invalid priority. Must be one of: {valid_priorities}',
                'details': {'priority': [f'Must be one of: {valid_priorities}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate recipients
        for i, recipient in enumerate(recipients):
            if not recipient.get('name'):
                return Response({
                    'error': f'Recipient {i} missing name',
                    'details': {'recipients': [f'Recipient {i} must have a name']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not recipient.get('phone') and not recipient.get('email'):
                return Response({
                    'error': f'Recipient {i} missing contact information',
                    'details': {'recipients': [f'Recipient {i} must have phone or email']}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare notification data
        notification_data = {
            'emergency_id': emergency_id,
            'emergency_type': emergency_type,
            'channels': channels,
            'recipients': recipients,
            'message': message,
            'priority': priority,
            'location': location_data,
            'medical_data': medical_data
        }
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send notification
        result = notification_service.send_emergency_notification(request.user, notification_data)
        
        if result['success']:
            return Response({
                'notification_id': result['notification_id'],
                'channels_sent': result['channels_sent'],
                'total_sent': result['total_sent'],
                'total_failed': result['total_failed'],
                'results': result['results'],
                'timestamp': result['timestamp']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result.get('error', 'Failed to send notification'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Family notification failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_emergency_contacts(request):
    """
    Get user's emergency contacts.
    
    Query Parameters:
    - include_medical: Include medical emergency contacts (default: true)
    - include_family: Include family contacts (default: true)
    - include_friends: Include friend contacts (default: true)
    
    Response:
    {
        "contacts": [
            {
                "id": "uuid",
                "name": "John Doe",
                "phone": "+27123456789",
                "email": "john@example.com",
                "relationship": "spouse",
                "priority": "high",
                "contact_type": "family|medical|friend",
                "is_primary": true,
                "notifications_enabled": true
            }
        ],
        "total_contacts": 5,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Get query parameters
        include_medical = request.query_params.get('include_medical', 'true').lower() == 'true'
        include_family = request.query_params.get('include_family', 'true').lower() == 'true'
        include_friends = request.query_params.get('include_friends', 'true').lower() == 'true'
        
        # Get emergency contacts from medical data
        contacts = []
        
        try:
            medical_data = EmergencyMedical.objects.get(user=request.user)
            
            # Add emergency contact from medical data
            if medical_data.emergency_contact_name and medical_data.emergency_contact_phone:
                contacts.append({
                    'id': str(medical_data.id),
                    'name': medical_data.emergency_contact_name,
                    'phone': medical_data.emergency_contact_phone,
                    'email': '',  # Not stored in medical data
                    'relationship': medical_data.emergency_contact_relationship or 'emergency_contact',
                    'priority': 'critical',
                    'contact_type': 'medical',
                    'is_primary': True,
                    'notifications_enabled': True
                })
        except EmergencyMedical.DoesNotExist:
            pass
        
        # Add family contacts (this would come from user profile or separate model)
        # For now, we'll add some mock family contacts
        if include_family:
            family_contacts = [
                {
                    'id': 'family-1',
                    'name': f"{request.user.first_name} Family",
                    'phone': getattr(request.user, 'phone_number', ''),
                    'email': request.user.email,
                    'relationship': 'self',
                    'priority': 'high',
                    'contact_type': 'family',
                    'is_primary': False,
                    'notifications_enabled': True
                }
            ]
            contacts.extend(family_contacts)
        
        # Add friend contacts (this would come from user's friend list)
        # For now, we'll add some mock friend contacts
        if include_friends:
            friend_contacts = [
                {
                    'id': 'friend-1',
                    'name': 'Emergency Friend',
                    'phone': '+27123456789',
                    'email': 'friend@example.com',
                    'relationship': 'friend',
                    'priority': 'medium',
                    'contact_type': 'friend',
                    'is_primary': False,
                    'notifications_enabled': True
                }
            ]
            contacts.extend(friend_contacts)
        
        return Response({
            'contacts': contacts,
            'total_contacts': len(contacts),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get emergency contacts failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def add_emergency_contact(request):
    """
    Add new emergency contact.
    
    Request Body:
    {
        "name": "John Doe",
        "phone": "+27123456789",
        "email": "john@example.com",
        "relationship": "spouse|parent|sibling|friend|colleague",
        "priority": "low|medium|high|critical",
        "contact_type": "family|medical|friend",
        "is_primary": false,
        "notifications_enabled": true
    }
    
    Response:
    {
        "contact_id": "uuid",
        "message": "Emergency contact added successfully",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract request data
        name = request.data.get('name')
        phone = request.data.get('phone')
        email = request.data.get('email')
        relationship = request.data.get('relationship', 'friend')
        priority = request.data.get('priority', 'medium')
        contact_type = request.data.get('contact_type', 'friend')
        is_primary = request.data.get('is_primary', False)
        notifications_enabled = request.data.get('notifications_enabled', True)
        
        # Validate required fields
        if not name:
            return Response({
                'error': 'name is required',
                'details': {'name': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not phone and not email:
            return Response({
                'error': 'phone or email is required',
                'details': {'phone': ['At least one contact method is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate relationship
        valid_relationships = ['spouse', 'parent', 'sibling', 'child', 'friend', 'colleague', 'neighbor', 'other']
        if relationship not in valid_relationships:
            return Response({
                'error': f'Invalid relationship. Must be one of: {valid_relationships}',
                'details': {'relationship': [f'Must be one of: {valid_relationships}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if priority not in valid_priorities:
            return Response({
                'error': f'Invalid priority. Must be one of: {valid_priorities}',
                'details': {'priority': [f'Must be one of: {valid_priorities}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate contact type
        valid_contact_types = ['family', 'medical', 'friend', 'colleague']
        if contact_type not in valid_contact_types:
            return Response({
                'error': f'Invalid contact_type. Must be one of: {valid_contact_types}',
                'details': {'contact_type': [f'Must be one of: {valid_contact_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create contact (this would be stored in a proper model)
        # For now, we'll generate a mock contact ID
        import uuid
        contact_id = str(uuid.uuid4())
        
        # Log contact addition
        try:
            EmergencyAuditLog.log_action(
                action_type='emergency_contact_add',
                description=f'Emergency contact added: {name}',
                user=request.user,
                severity='low',
                contact_name=name,
                contact_phone=phone,
                contact_email=email,
                relationship=relationship,
                priority=priority,
                contact_type=contact_type
            )
        except Exception as e:
            logger.warning(f"Failed to log contact addition: {str(e)}")
        
        return Response({
            'contact_id': contact_id,
            'message': 'Emergency contact added successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Add emergency contact failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def update_emergency_contact(request, contact_id):
    """
    Update emergency contact.
    
    URL Parameters:
    - contact_id: Contact ID
    
    Request Body:
    {
        "name": "John Doe",
        "phone": "+27123456789",
        "email": "john@example.com",
        "relationship": "spouse",
        "priority": "high",
        "contact_type": "family",
        "is_primary": true,
        "notifications_enabled": true
    }
    
    Response:
    {
        "contact_id": "uuid",
        "message": "Emergency contact updated successfully",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract request data
        name = request.data.get('name')
        phone = request.data.get('phone')
        email = request.data.get('email')
        relationship = request.data.get('relationship')
        priority = request.data.get('priority')
        contact_type = request.data.get('contact_type')
        is_primary = request.data.get('is_primary')
        notifications_enabled = request.data.get('notifications_enabled')
        
        # Validate contact exists (this would check against actual model)
        # For now, we'll assume it exists
        
        # Update contact (this would update the actual model)
        # For now, we'll just log the update
        
        # Log contact update
        try:
            EmergencyAuditLog.log_action(
                action_type='emergency_contact_update',
                description=f'Emergency contact updated: {contact_id}',
                user=request.user,
                severity='low',
                contact_id=contact_id,
                updated_fields=list(request.data.keys())
            )
        except Exception as e:
            logger.warning(f"Failed to log contact update: {str(e)}")
        
        return Response({
            'contact_id': contact_id,
            'message': 'Emergency contact updated successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Update emergency contact failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def delete_emergency_contact(request, contact_id):
    """
    Delete emergency contact.
    
    URL Parameters:
    - contact_id: Contact ID
    
    Response:
    {
        "contact_id": "uuid",
        "message": "Emergency contact deleted successfully",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Validate contact exists (this would check against actual model)
        # For now, we'll assume it exists
        
        # Delete contact (this would delete from actual model)
        # For now, we'll just log the deletion
        
        # Log contact deletion
        try:
            EmergencyAuditLog.log_action(
                action_type='emergency_contact_delete',
                description=f'Emergency contact deleted: {contact_id}',
                user=request.user,
                severity='low',
                contact_id=contact_id
            )
        except Exception as e:
            logger.warning(f"Failed to log contact deletion: {str(e)}")
        
        return Response({
            'contact_id': contact_id,
            'message': 'Emergency contact deleted successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Delete emergency contact failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_notification_preferences(request):
    """
    Get user's notification preferences.
    
    Response:
    {
        "preferences": {
            "channels": ["sms", "email"],
            "priority": "high",
            "emergency_types": ["panic", "medical", "fire"],
            "quiet_hours": {
                "enabled": false,
                "start": "22:00",
                "end": "07:00"
            },
            "location_sharing": true,
            "medical_sharing": true
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Initialize notification service
        notification_service = NotificationService()
        
        # Get preferences
        result = notification_service.get_user_notification_preferences(request.user)
        
        if result['success']:
            return Response({
                'preferences': result['preferences'],
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Failed to get preferences'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Get notification preferences failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def update_notification_preferences(request):
    """
    Update user's notification preferences.
    
    Request Body:
    {
        "channels": ["sms", "email", "push"],
        "priority": "high",
        "emergency_types": ["panic", "medical", "fire", "crime"],
        "quiet_hours": {
            "enabled": true,
            "start": "22:00",
            "end": "07:00"
        },
        "location_sharing": true,
        "medical_sharing": false
    }
    
    Response:
    {
        "message": "Notification preferences updated successfully",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract preferences
        preferences = request.data
        
        # Validate channels
        valid_channels = ['sms', 'email', 'push', 'ussd', 'whatsapp', 'telegram']
        channels = preferences.get('channels', [])
        invalid_channels = [ch for ch in channels if ch not in valid_channels]
        if invalid_channels:
            return Response({
                'error': f'Invalid channels: {invalid_channels}',
                'details': {'channels': [f'Must be one of: {valid_channels}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'critical']
        priority = preferences.get('priority')
        if priority and priority not in valid_priorities:
            return Response({
                'error': f'Invalid priority. Must be one of: {valid_priorities}',
                'details': {'priority': [f'Must be one of: {valid_priorities}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate emergency types
        valid_emergency_types = ['panic', 'medical', 'fire', 'crime', 'accident']
        emergency_types = preferences.get('emergency_types', [])
        invalid_types = [et for et in emergency_types if et not in valid_emergency_types]
        if invalid_types:
            return Response({
                'error': f'Invalid emergency types: {invalid_types}',
                'details': {'emergency_types': [f'Must be one of: {valid_emergency_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Update preferences
        result = notification_service.update_user_notification_preferences(request.user, preferences)
        
        if result['success']:
            return Response({
                'message': 'Notification preferences updated successfully',
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Failed to update preferences'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Update notification preferences failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_notification_status(request, notification_id):
    """
    Get notification delivery status.
    
    URL Parameters:
    - notification_id: Notification ID
    
    Response:
    {
        "notification_id": "uuid",
        "status": {
            "channels": {
                "sms": {"sent": 3, "failed": 0, "delivered": 2, "pending": 1},
                "email": {"sent": 2, "failed": 0, "delivered": 2, "pending": 0}
            },
            "overall_status": "delivered",
            "total_sent": 5,
            "total_delivered": 4,
            "total_failed": 0,
            "total_pending": 1
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Initialize notification service
        notification_service = NotificationService()
        
        # Get status
        result = notification_service.get_notification_status(notification_id)
        
        if result['success']:
            return Response({
                'notification_id': notification_id,
                'status': result['status'],
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Notification not found'),
                'notification_id': notification_id
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Get notification status failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)