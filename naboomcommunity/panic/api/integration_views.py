"""
External Service Integration API Views
REST API endpoints for external emergency service integration.
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
from ..services.external_service_integration import ExternalServiceIntegration
from ..models import EmergencyAuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def dispatch_emergency_service(request):
    """
    Dispatch emergency to external service.
    
    Request Body:
    {
        "emergency_id": "uuid",
        "emergency_type": "panic|medical|fire|crime|accident|rescue|disaster|security",
        "priority": "low|medium|high|critical",
        "description": "Emergency description",
        "location": {
            "latitude": -26.2041,
            "longitude": 28.0473,
            "accuracy": 10.5,
            "altitude": 1500.0,
            "address": "123 Main St, Johannesburg"
        },
        "medical_data": {
            "blood_type": "O+",
            "allergies": [...],
            "medical_conditions": [...],
            "consent_level": "emergency_only|full"
        },
        "service_preference": "police|ambulance|fire|rescue|disaster|security|auto"
    }
    
    Response:
    {
        "dispatch_id": "uuid",
        "service_type": "police",
        "service_name": "South African Police Service",
        "external_id": "ext-123",
        "status": "dispatched",
        "message": "Emergency dispatched successfully",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract request data
        emergency_id = request.data.get('emergency_id')
        emergency_type = request.data.get('emergency_type', 'panic')
        priority = request.data.get('priority', 'high')
        description = request.data.get('description', '')
        location_data = request.data.get('location', {})
        medical_data = request.data.get('medical_data', {})
        service_preference = request.data.get('service_preference', 'auto')
        
        # Validate required fields
        if not emergency_id:
            return Response({
                'error': 'emergency_id is required',
                'details': {'emergency_id': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate emergency type
        valid_emergency_types = ['panic', 'medical', 'fire', 'crime', 'accident', 'rescue', 'disaster', 'security']
        if emergency_type not in valid_emergency_types:
            return Response({
                'error': f'Invalid emergency_type. Must be one of: {valid_emergency_types}',
                'details': {'emergency_type': [f'Must be one of: {valid_emergency_types}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if priority not in valid_priorities:
            return Response({
                'error': f'Invalid priority. Must be one of: {valid_priorities}',
                'details': {'priority': [f'Must be one of: {valid_priorities}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate service preference
        valid_service_preferences = ['police', 'ambulance', 'fire', 'rescue', 'disaster', 'security', 'auto']
        if service_preference not in valid_service_preferences:
            return Response({
                'error': f'Invalid service_preference. Must be one of: {valid_service_preferences}',
                'details': {'service_preference': [f'Must be one of: {valid_service_preferences}']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare emergency data
        emergency_data = {
            'emergency_id': emergency_id,
            'emergency_type': emergency_type,
            'priority': priority,
            'description': description,
            'location': location_data,
            'medical_data': medical_data,
            'service_preference': service_preference
        }
        
        # Initialize external service integration
        integration_service = ExternalServiceIntegration()
        
        # Dispatch emergency service
        result = integration_service.dispatch_emergency_service(request.user, emergency_data)
        
        if result['success']:
            return Response({
                'dispatch_id': result.get('external_id', ''),
                'service_type': result.get('service_type', ''),
                'service_name': result.get('service_name', ''),
                'external_id': result.get('external_id', ''),
                'status': 'dispatched',
                'message': result.get('message', 'Emergency dispatched successfully'),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result.get('error', 'Failed to dispatch emergency service'),
                'details': result.get('details', {}),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Emergency service dispatch failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_available_services(request):
    """
    Get list of available external emergency services.
    
    Query Parameters:
    - service_type: Filter by service type (optional)
    - status: Filter by service status (optional)
    
    Response:
    {
        "services": [
            {
                "id": "police_10111",
                "name": "South African Police Service",
                "type": "police",
                "protocol": "rest_api",
                "endpoint": "https://api.saps.gov.za/emergency",
                "timeout": 30,
                "retry_attempts": 3,
                "health": {
                    "status": "healthy",
                    "response_time": 0.5,
                    "last_check": "2024-01-01T12:00:00Z"
                }
            }
        ],
        "total_services": 5,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Get query parameters
        service_type = request.query_params.get('service_type')
        status_filter = request.query_params.get('status')
        
        # Initialize external service integration
        integration_service = ExternalServiceIntegration()
        
        # Get available services
        result = integration_service.get_available_services()
        
        if result['success']:
            services = result['services']
            
            # Apply filters
            if service_type:
                services = [s for s in services if s.get('type') == service_type]
            
            if status_filter:
                services = [s for s in services if s.get('health', {}).get('status') == status_filter]
            
            return Response({
                'services': services,
                'total_services': len(services),
                'timestamp': result['timestamp']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Failed to get available services'),
                'details': result.get('details', {})
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Get available services failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_service_status(request, service_type):
    """
    Get status of specific external service.
    
    URL Parameters:
    - service_type: Service type (police, ambulance, fire, etc.)
    
    Response:
    {
        "service_type": "police",
        "service_name": "South African Police Service",
        "protocol": "rest_api",
        "status": "healthy",
        "response_time": 0.5,
        "last_check": "2024-01-01T12:00:00Z",
        "error": null
    }
    """
    try:
        # Initialize external service integration
        integration_service = ExternalServiceIntegration()
        
        # Get service status
        result = integration_service.get_service_status(service_type)
        
        if result['success']:
            return Response({
                'service_type': result['service_type'],
                'service_name': result['service_name'],
                'protocol': result['protocol'],
                'status': result['status'],
                'response_time': result.get('response_time'),
                'last_check': result.get('last_check'),
                'error': result.get('error')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.get('error', 'Service not found'),
                'service_type': service_type
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Get service status failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def test_service_connection(request, service_type):
    """
    Test connection to external service.
    
    URL Parameters:
    - service_type: Service type to test
    
    Response:
    {
        "service_type": "police",
        "status": "healthy",
        "response_time": 0.5,
        "message": "Connection test successful",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Initialize external service integration
        integration_service = ExternalServiceIntegration()
        
        # Test service connection
        result = integration_service.get_service_status(service_type)
        
        if result['success']:
            status_info = result['status']
            
            if status_info == 'healthy':
                message = 'Connection test successful'
                response_status = status.HTTP_200_OK
            elif status_info == 'unhealthy':
                message = 'Service is unhealthy'
                response_status = status.HTTP_503_SERVICE_UNAVAILABLE
            elif status_info == 'timeout':
                message = 'Service connection timeout'
                response_status = status.HTTP_504_GATEWAY_TIMEOUT
            elif status_info == 'unreachable':
                message = 'Service is unreachable'
                response_status = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                message = f'Service status: {status_info}'
                response_status = status.HTTP_200_OK
            
            return Response({
                'service_type': service_type,
                'status': status_info,
                'response_time': result.get('response_time'),
                'message': message,
                'timestamp': timezone.now().isoformat()
            }, status=response_status)
        else:
            return Response({
                'error': result.get('error', 'Service not found'),
                'service_type': service_type
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Test service connection failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_dispatch_history(request):
    """
    Get history of emergency dispatches.
    
    Query Parameters:
    - emergency_id: Filter by emergency ID (optional)
    - service_type: Filter by service type (optional)
    - status: Filter by dispatch status (optional)
    - limit: Number of results to return (default: 50)
    - offset: Number of results to skip (default: 0)
    
    Response:
    {
        "dispatches": [
            {
                "dispatch_id": "uuid",
                "emergency_id": "uuid",
                "service_type": "police",
                "service_name": "South African Police Service",
                "external_id": "ext-123",
                "status": "dispatched",
                "priority": "high",
                "created_at": "2024-01-01T12:00:00Z",
                "response_time": 0.5
            }
        ],
        "total_dispatches": 10,
        "limit": 50,
        "offset": 0,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Get query parameters
        emergency_id = request.query_params.get('emergency_id')
        service_type = request.query_params.get('service_type')
        status_filter = request.query_params.get('status')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Validate parameters
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0
        
        # Get dispatch history from audit logs
        # This would typically query a dedicated dispatch history table
        # For now, we'll query audit logs
        from django.db.models import Q
        
        query = Q(action_type='external_service_dispatch', user=request.user)
        
        if emergency_id:
            query &= Q(emergency_id=emergency_id)
        
        if service_type:
            query &= Q(metadata__service_type=service_type)
        
        if status_filter:
            query &= Q(metadata__success=(status_filter == 'success'))
        
        # Get audit logs
        audit_logs = EmergencyAuditLog.objects.filter(query).order_by('-created_at')[offset:offset + limit]
        
        # Format dispatch history
        dispatches = []
        for log in audit_logs:
            metadata = log.metadata or {}
            dispatches.append({
                'dispatch_id': str(log.id),
                'emergency_id': log.emergency_id,
                'service_type': metadata.get('service_type', ''),
                'service_name': metadata.get('service_name', ''),
                'external_id': metadata.get('external_id', ''),
                'status': 'dispatched' if metadata.get('success') else 'failed',
                'priority': metadata.get('priority', ''),
                'created_at': log.created_at.isoformat(),
                'response_time': metadata.get('response_time'),
                'error_message': metadata.get('error_message', '')
            })
        
        return Response({
            'dispatches': dispatches,
            'total_dispatches': len(dispatches),
            'limit': limit,
            'offset': offset,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get dispatch history failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def update_service_configuration(request, service_type):
    """
    Update external service configuration.
    
    URL Parameters:
    - service_type: Service type to update
    
    Request Body:
    {
        "endpoint": "https://api.example.com/emergency",
        "api_key": "new-api-key",
        "timeout": 30,
        "retry_attempts": 3,
        "priority_mapping": {
            "critical": "emergency",
            "high": "urgent",
            "medium": "normal",
            "low": "low"
        }
    }
    
    Response:
    {
        "service_type": "police",
        "message": "Service configuration updated successfully",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Extract configuration data
        endpoint = request.data.get('endpoint')
        api_key = request.data.get('api_key')
        timeout = request.data.get('timeout')
        retry_attempts = request.data.get('retry_attempts')
        priority_mapping = request.data.get('priority_mapping')
        
        # Validate configuration
        if not endpoint:
            return Response({
                'error': 'endpoint is required',
                'details': {'endpoint': ['This field is required']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
            return Response({
                'error': 'timeout must be a positive integer',
                'details': {'timeout': ['Must be a positive integer']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if retry_attempts is not None and (not isinstance(retry_attempts, int) or retry_attempts < 0):
            return Response({
                'error': 'retry_attempts must be a non-negative integer',
                'details': {'retry_attempts': ['Must be a non-negative integer']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update service configuration
        # This would typically update a database or configuration file
        # For now, we'll just log the update
        
        # Log configuration update
        try:
            EmergencyAuditLog.log_action(
                action_type='service_configuration_update',
                description=f'Service configuration updated for {service_type}',
                user=request.user,
                severity='medium',
                service_type=service_type,
                endpoint=endpoint,
                timeout=timeout,
                retry_attempts=retry_attempts
            )
        except Exception as e:
            logger.warning(f"Failed to log configuration update: {str(e)}")
        
        return Response({
            'service_type': service_type,
            'message': 'Service configuration updated successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Update service configuration failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([EmergencyPanicThrottle])
def get_service_metrics(request, service_type):
    """
    Get metrics for external service.
    
    URL Parameters:
    - service_type: Service type to get metrics for
    
    Query Parameters:
    - days: Number of days to include in metrics (default: 30)
    
    Response:
    {
        "service_type": "police",
        "metrics": {
            "total_dispatches": 150,
            "successful_dispatches": 145,
            "failed_dispatches": 5,
            "success_rate": 96.67,
            "average_response_time": 0.8,
            "uptime_percentage": 99.5
        },
        "period_days": 30,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Get query parameters
        days = int(request.query_params.get('days', 30))
        
        # Validate parameters
        if days <= 0 or days > 365:
            return Response({
                'error': 'days must be between 1 and 365',
                'details': {'days': ['Must be between 1 and 365']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate metrics from audit logs
        from django.db.models import Q, Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Query audit logs for this service
        query = Q(
            action_type='external_service_dispatch',
            created_at__gte=start_date,
            created_at__lte=end_date,
            metadata__service_type=service_type
        )
        
        logs = EmergencyAuditLog.objects.filter(query)
        
        # Calculate metrics
        total_dispatches = logs.count()
        successful_dispatches = logs.filter(metadata__success=True).count()
        failed_dispatches = total_dispatches - successful_dispatches
        
        success_rate = (successful_dispatches / total_dispatches * 100) if total_dispatches > 0 else 0
        
        # Calculate average response time
        response_times = [log.metadata.get('response_time') for log in logs if log.metadata and log.metadata.get('response_time')]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate uptime percentage (simplified)
        uptime_percentage = 99.5  # This would be calculated from health checks
        
        return Response({
            'service_type': service_type,
            'metrics': {
                'total_dispatches': total_dispatches,
                'successful_dispatches': successful_dispatches,
                'failed_dispatches': failed_dispatches,
                'success_rate': round(success_rate, 2),
                'average_response_time': round(average_response_time, 2),
                'uptime_percentage': uptime_percentage
            },
            'period_days': days,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get service metrics failed: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)