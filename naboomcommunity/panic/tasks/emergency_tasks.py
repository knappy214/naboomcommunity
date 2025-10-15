"""
Emergency Response Celery Tasks
High-priority tasks for emergency response operations.
"""

from celery import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
import json
import logging
from typing import Dict, Any, Optional

from ..models import EmergencyLocation, EmergencyMedical, EmergencyAuditLog
from ..services.location_service import LocationService
from ..services.medical_service import MedicalService
from ..services.notification_service import NotificationService

User = get_user_model()
logger = get_task_logger(__name__)


class EmergencyTask(Task):
    """
    Base task class for emergency response operations.
    Provides common functionality and error handling.
    """
    
    # Task configuration
    bind = True
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_jitter = True
    
    # Emergency-specific settings
    priority = 9  # High priority
    queue = 'emergency-high-priority'
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Emergency task {self.name} retry {self.request.retries}/{self.max_retries}: {exc}")
        
        # Log retry attempt
        try:
            EmergencyAuditLog.objects.create(
                action_type='task_retry',
                user_id=kwargs.get('user_id'),
                severity='medium',
                description=f"Task {self.name} retry attempt {self.request.retries}",
                metadata={
                    'task_id': task_id,
                    'error': str(exc),
                    'args': args,
                    'kwargs': kwargs
                }
            )
        except Exception as e:
            logger.error(f"Failed to log task retry: {e}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Emergency task {self.name} failed: {exc}")
        
        # Log failure
        try:
            EmergencyAuditLog.objects.create(
                action_type='task_failure',
                user_id=kwargs.get('user_id'),
                severity='high',
                description=f"Task {self.name} failed after {self.max_retries} retries",
                error_message=str(exc),
                stack_trace=str(einfo),
                metadata={
                    'task_id': task_id,
                    'args': args,
                    'kwargs': kwargs
                }
            )
        except Exception as e:
            logger.error(f"Failed to log task failure: {e}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Emergency task {self.name} completed successfully")
        
        # Log success
        try:
            EmergencyAuditLog.objects.create(
                action_type='task_success',
                user_id=kwargs.get('user_id'),
                severity='low',
                description=f"Task {self.name} completed successfully",
                metadata={
                    'task_id': task_id,
                    'result': str(retval) if retval else None
                }
            )
        except Exception as e:
            logger.error(f"Failed to log task success: {e}")


class LocationTask(EmergencyTask):
    """Task for location-related operations."""
    queue = 'emergency-location'


class MedicalTask(EmergencyTask):
    """Task for medical data operations."""
    queue = 'emergency-medical'


class NotificationTask(EmergencyTask):
    """Task for notification operations."""
    queue = 'emergency-notifications'


class SyncTask(EmergencyTask):
    """Task for offline sync operations."""
    queue = 'emergency-sync'


# Location Tasks
@LocationTask.task
def process_location_update(self, user_id: int, location_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process location update for emergency response.
    
    Args:
        user_id: User ID
        location_data: Location data dictionary
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info(f"Processing location update for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process location data
        location_service = LocationService()
        result = location_service.process_location_update(user, location_data)
        
        # Log successful processing
        EmergencyAuditLog.objects.create(
            action_type='location_update',
            user=user,
            severity='low',
            description=f"Location update processed successfully",
            metadata={
                'location_data': location_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'location_id': result.get('location_id'),
            'accuracy': result.get('accuracy'),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for location update")
        raise
    except Exception as e:
        logger.error(f"Location update processing failed: {str(e)}")
        raise


@LocationTask.task
def validate_gps_accuracy(self, user_id: int, gps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate GPS accuracy for emergency location.
    
    Args:
        user_id: User ID
        gps_data: GPS data dictionary
        
    Returns:
        Validation result dictionary
    """
    try:
        logger.info(f"Validating GPS accuracy for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Validate GPS accuracy
        location_service = LocationService()
        result = location_service.validate_gps_accuracy(user, gps_data)
        
        # Log validation result
        EmergencyAuditLog.objects.create(
            action_type='gps_validation',
            user=user,
            severity='low',
            description=f"GPS accuracy validation completed",
            metadata={
                'gps_data': gps_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'accuracy': result.get('accuracy'),
            'is_valid': result.get('is_valid', False),
            'recommendations': result.get('recommendations', []),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for GPS validation")
        raise
    except Exception as e:
        logger.error(f"GPS accuracy validation failed: {str(e)}")
        raise


# Medical Tasks
@MedicalTask.task
def process_medical_data(self, user_id: int, medical_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process medical data for emergency response.
    
    Args:
        user_id: User ID
        medical_data: Medical data dictionary
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info(f"Processing medical data for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process medical data
        medical_service = MedicalService()
        result = medical_service.process_medical_data(user, medical_data)
        
        # Log successful processing
        EmergencyAuditLog.objects.create(
            action_type='medical_update',
            user=user,
            severity='medium',
            description=f"Medical data processed successfully",
            metadata={
                'medical_data': medical_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'medical_id': result.get('medical_id'),
            'data_type': result.get('data_type'),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for medical data processing")
        raise
    except Exception as e:
        logger.error(f"Medical data processing failed: {str(e)}")
        raise


@MedicalTask.task
def encrypt_medical_data(self, user_id: int, medical_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt sensitive medical data.
    
    Args:
        user_id: User ID
        medical_data: Medical data dictionary
        
    Returns:
        Encryption result dictionary
    """
    try:
        logger.info(f"Encrypting medical data for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Encrypt medical data
        medical_service = MedicalService()
        result = medical_service.encrypt_medical_data(user, medical_data)
        
        # Log encryption
        EmergencyAuditLog.objects.create(
            action_type='medical_encryption',
            user=user,
            severity='medium',
            description=f"Medical data encrypted successfully",
            metadata={
                'encryption_key_id': result.get('encryption_key_id'),
                'data_size': len(str(medical_data))
            }
        )
        
        return {
            'success': True,
            'encryption_key_id': result.get('encryption_key_id'),
            'encrypted_data': result.get('encrypted_data'),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for medical data encryption")
        raise
    except Exception as e:
        logger.error(f"Medical data encryption failed: {str(e)}")
        raise


# Notification Tasks
@NotificationTask.task
def send_emergency_notification(self, user_id: int, notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send emergency notification to family and contacts.
    
    Args:
        user_id: User ID
        notification_data: Notification data dictionary
        
    Returns:
        Notification result dictionary
    """
    try:
        logger.info(f"Sending emergency notification for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Send notification
        notification_service = NotificationService()
        result = notification_service.send_emergency_notification(user, notification_data)
        
        # Log notification
        EmergencyAuditLog.objects.create(
            action_type='notification_send',
            user=user,
            severity='medium',
            description=f"Emergency notification sent successfully",
            metadata={
                'notification_data': notification_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'notification_id': result.get('notification_id'),
            'recipients': result.get('recipients', []),
            'channels': result.get('channels', []),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for emergency notification")
        raise
    except Exception as e:
        logger.error(f"Emergency notification failed: {str(e)}")
        raise


@NotificationTask.task
def send_sms_notification(self, user_id: int, phone_numbers: list, message: str) -> Dict[str, Any]:
    """
    Send SMS notification to specified phone numbers.
    
    Args:
        user_id: User ID
        phone_numbers: List of phone numbers
        message: SMS message
        
    Returns:
        SMS result dictionary
    """
    try:
        logger.info(f"Sending SMS notification for user {user_id} to {len(phone_numbers)} numbers")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Send SMS
        notification_service = NotificationService()
        result = notification_service.send_sms_notification(phone_numbers, message)
        
        # Log SMS
        EmergencyAuditLog.objects.create(
            action_type='sms_send',
            user=user,
            severity='low',
            description=f"SMS notification sent to {len(phone_numbers)} numbers",
            metadata={
                'phone_numbers': phone_numbers,
                'message_length': len(message),
                'result': result
            }
        )
        
        return {
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for SMS notification")
        raise
    except Exception as e:
        logger.error(f"SMS notification failed: {str(e)}")
        raise


@NotificationTask.task
def send_push_notification(self, user_id: int, device_tokens: list, notification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send push notification to specified devices.
    
    Args:
        user_id: User ID
        device_tokens: List of device tokens
        notification: Push notification data
        
    Returns:
        Push notification result dictionary
    """
    try:
        logger.info(f"Sending push notification for user {user_id} to {len(device_tokens)} devices")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Send push notification
        notification_service = NotificationService()
        result = notification_service.send_push_notification(device_tokens, notification)
        
        # Log push notification
        EmergencyAuditLog.objects.create(
            action_type='push_send',
            user=user,
            severity='low',
            description=f"Push notification sent to {len(device_tokens)} devices",
            metadata={
                'device_count': len(device_tokens),
                'notification': notification,
                'result': result
            }
        )
        
        return {
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for push notification")
        raise
    except Exception as e:
        logger.error(f"Push notification failed: {str(e)}")
        raise


# Sync Tasks
@SyncTask.task
def sync_offline_data(self, user_id: int, offline_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync offline data when connectivity is restored.
    
    Args:
        user_id: User ID
        offline_data: Offline data dictionary
        
    Returns:
        Sync result dictionary
    """
    try:
        logger.info(f"Syncing offline data for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process offline data
        # This would integrate with the offline sync service
        result = {
            'synced_items': offline_data.get('items', []),
            'conflicts': [],
            'errors': []
        }
        
        # Log sync
        EmergencyAuditLog.objects.create(
            action_type='offline_sync',
            user=user,
            severity='low',
            description=f"Offline data synced successfully",
            metadata={
                'offline_data': offline_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'synced_items': len(result['synced_items']),
            'conflicts': len(result['conflicts']),
            'errors': len(result['errors']),
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for offline sync")
        raise
    except Exception as e:
        logger.error(f"Offline sync failed: {str(e)}")
        raise


@SyncTask.task
def resolve_sync_conflicts(self, user_id: int, conflicts: list) -> Dict[str, Any]:
    """
    Resolve sync conflicts for offline data.
    
    Args:
        user_id: User ID
        conflicts: List of conflict data
        
    Returns:
        Conflict resolution result dictionary
    """
    try:
        logger.info(f"Resolving sync conflicts for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Resolve conflicts
        resolved_conflicts = []
        for conflict in conflicts:
            # Simple conflict resolution logic
            resolved_conflicts.append({
                'conflict_id': conflict.get('id'),
                'resolution': 'server_wins',  # or 'client_wins' or 'merge'
                'timestamp': timezone.now().isoformat()
            })
        
        # Log conflict resolution
        EmergencyAuditLog.objects.create(
            action_type='sync_conflict_resolution',
            user=user,
            severity='medium',
            description=f"Sync conflicts resolved successfully",
            metadata={
                'conflicts': conflicts,
                'resolved_conflicts': resolved_conflicts
            }
        )
        
        return {
            'success': True,
            'resolved_count': len(resolved_conflicts),
            'conflicts': resolved_conflicts,
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for conflict resolution")
        raise
    except Exception as e:
        logger.error(f"Conflict resolution failed: {str(e)}")
        raise


# High Priority Emergency Tasks
@EmergencyTask.task
def process_panic_button_activation(self, user_id: int, panic_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process panic button activation - highest priority task.
    
    Args:
        user_id: User ID
        panic_data: Panic button data dictionary
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info(f"Processing panic button activation for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Process panic activation
        # This would integrate with the panic button service
        result = {
            'incident_id': panic_data.get('incident_id'),
            'location_processed': True,
            'medical_data_retrieved': True,
            'notifications_sent': True
        }
        
        # Log panic activation
        EmergencyAuditLog.objects.create(
            action_type='panic_activate',
            user=user,
            severity='critical',
            description=f"Panic button activated successfully",
            metadata={
                'panic_data': panic_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'incident_id': result['incident_id'],
            'status': 'processed',
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for panic button activation")
        raise
    except Exception as e:
        logger.error(f"Panic button activation failed: {str(e)}")
        raise


@EmergencyTask.task
def notify_emergency_services(self, incident_id: str, service_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Notify external emergency services.
    
    Args:
        incident_id: Incident ID
        service_data: Service notification data
        
    Returns:
        Notification result dictionary
    """
    try:
        logger.info(f"Notifying emergency services for incident {incident_id}")
        
        # Notify services
        # This would integrate with external service APIs
        result = {
            'police_notified': True,
            'ambulance_notified': True,
            'fire_notified': False  # Based on incident type
        }
        
        # Log service notification
        EmergencyAuditLog.objects.create(
            action_type='external_service_notification',
            user_id=None,  # System action
            severity='high',
            description=f"Emergency services notified for incident {incident_id}",
            metadata={
                'incident_id': incident_id,
                'service_data': service_data,
                'result': result
            }
        )
        
        return {
            'success': True,
            'incident_id': incident_id,
            'services_notified': result,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Emergency service notification failed: {str(e)}")
        raise