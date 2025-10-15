"""
Offline Sync Service for Emergency Response
Handles offline data synchronization for emergency response operations.
"""

import json
import logging
import hashlib
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone
from django.core.serializers.json import DjangoJSONEncoder

from ..models import EmergencyLocation, EmergencyMedical, EmergencyAuditLog
from ..services.location_service import LocationService
from ..services.medical_service import MedicalService

User = get_user_model()
logger = logging.getLogger(__name__)


class OfflineSyncService:
    """
    Service for handling offline data synchronization in emergency response.
    Provides conflict resolution, data validation, and sync management.
    """
    
    # Sync configuration
    SYNC_BATCH_SIZE = 100
    SYNC_TIMEOUT = 300  # 5 minutes
    CACHE_TIMEOUT = 3600  # 1 hour
    CACHE_PREFIX = 'offline_sync'
    
    # Data types for sync
    DATA_TYPES = {
        'emergency_location': EmergencyLocation,
        'emergency_medical': EmergencyMedical,
    }
    
    def __init__(self):
        self.location_service = LocationService()
        self.medical_service = MedicalService()
    
    def create_sync_session(self, user: User, device_id: str, 
                          sync_type: str = 'full') -> Dict[str, Any]:
        """
        Create a new offline sync session.
        
        Args:
            user: User instance
            device_id: Device identifier
            sync_type: Type of sync (full, incremental, emergency_only)
            
        Returns:
            Sync session information
        """
        try:
            session_id = str(uuid.uuid4())
            timestamp = django_timezone.now()
            
            # Create sync session
            session_data = {
                'session_id': session_id,
                'user_id': user.id,
                'device_id': device_id,
                'sync_type': sync_type,
                'status': 'active',
                'created_at': timestamp.isoformat(),
                'last_activity': timestamp.isoformat(),
                'total_items': 0,
                'synced_items': 0,
                'conflicts': 0,
                'errors': 0
            }
            
            # Store session in cache
            cache_key = f"{self.CACHE_PREFIX}:session:{session_id}"
            cache.set(cache_key, session_data, self.CACHE_TIMEOUT)
            
            # Store user's active sessions
            user_sessions_key = f"{self.CACHE_PREFIX}:user_sessions:{user.id}"
            user_sessions = cache.get(user_sessions_key, [])
            user_sessions.append(session_id)
            cache.set(user_sessions_key, user_sessions, self.CACHE_TIMEOUT)
            
            logger.info(f"Created offline sync session {session_id} for user {user.id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'sync_type': sync_type,
                'timestamp': timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create sync session: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create sync session',
                'details': str(e)
            }
    
    def sync_offline_data(self, user: User, session_id: str, 
                         offline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync offline data with server.
        
        Args:
            user: User instance
            session_id: Sync session ID
            offline_data: Offline data to sync
            
        Returns:
            Sync result dictionary
        """
        try:
            # Get sync session
            session = self.get_sync_session(session_id)
            if not session:
                return {
                    'success': False,
                    'error': 'Sync session not found',
                    'session_id': session_id
                }
            
            # Validate session ownership
            if session['user_id'] != user.id:
                return {
                    'success': False,
                    'error': 'Unauthorized access to sync session',
                    'session_id': session_id
                }
            
            # Process offline data
            sync_result = self.process_offline_data(user, session_id, offline_data)
            
            # Update session
            self.update_sync_session(session_id, sync_result)
            
            return {
                'success': True,
                'session_id': session_id,
                'synced_items': sync_result.get('synced_items', 0),
                'conflicts': sync_result.get('conflicts', 0),
                'errors': sync_result.get('errors', 0),
                'timestamp': django_timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync offline data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to sync offline data',
                'details': str(e)
            }
    
    def process_offline_data(self, user: User, session_id: str, 
                           offline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process offline data for synchronization.
        
        Args:
            user: User instance
            session_id: Sync session ID
            offline_data: Offline data to process
            
        Returns:
            Processing result dictionary
        """
        try:
            synced_items = 0
            conflicts = 0
            errors = 0
            conflict_resolutions = []
            
            # Process each data type
            for data_type, items in offline_data.items():
                if data_type not in self.DATA_TYPES:
                    continue
                
                for item in items:
                    try:
                        # Process individual item
                        result = self.process_sync_item(user, data_type, item)
                        
                        if result['success']:
                            synced_items += 1
                        elif result.get('conflict'):
                            conflicts += 1
                            conflict_resolutions.append(result)
                        else:
                            errors += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to process sync item: {str(e)}")
                        errors += 1
            
            return {
                'synced_items': synced_items,
                'conflicts': conflicts,
                'errors': errors,
                'conflict_resolutions': conflict_resolutions
            }
            
        except Exception as e:
            logger.error(f"Failed to process offline data: {str(e)}")
            return {
                'synced_items': 0,
                'conflicts': 0,
                'errors': 1,
                'conflict_resolutions': []
            }
    
    def process_sync_item(self, user: User, data_type: str, 
                         item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single sync item.
        
        Args:
            user: User instance
            data_type: Type of data being synced
            item: Item data to process
            
        Returns:
            Processing result dictionary
        """
        try:
            # Extract item metadata
            item_id = item.get('id')
            operation = item.get('operation', 'create')  # create, update, delete
            timestamp = item.get('timestamp')
            device_id = item.get('device_id')
            
            if not item_id:
                return {
                    'success': False,
                    'error': 'Item ID is required'
                }
            
            # Check for conflicts
            conflict_check = self.check_sync_conflict(data_type, item_id, timestamp)
            if conflict_check['has_conflict']:
                return self.resolve_sync_conflict(user, data_type, item, conflict_check)
            
            # Process based on data type
            if data_type == 'emergency_location':
                return self.sync_emergency_location(user, item, operation)
            elif data_type == 'emergency_medical':
                return self.sync_emergency_medical(user, item, operation)
            else:
                return {
                    'success': False,
                    'error': f'Unknown data type: {data_type}'
                }
                
        except Exception as e:
            logger.error(f"Failed to process sync item: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process sync item',
                'details': str(e)
            }
    
    def sync_emergency_location(self, user: User, item: Dict[str, Any], 
                              operation: str) -> Dict[str, Any]:
        """
        Sync emergency location data.
        
        Args:
            user: User instance
            item: Location item data
            operation: Sync operation
            
        Returns:
            Sync result dictionary
        """
        try:
            if operation == 'delete':
                # Handle deletion
                try:
                    location = EmergencyLocation.objects.get(id=item['id'], user=user)
                    location.delete()
                    return {'success': True, 'operation': 'deleted'}
                except EmergencyLocation.DoesNotExist:
                    return {'success': True, 'operation': 'already_deleted'}
            
            # Handle create/update
            location_data = {
                'latitude': item.get('latitude'),
                'longitude': item.get('longitude'),
                'accuracy': item.get('accuracy'),
                'emergency_type': item.get('emergency_type', 'panic'),
                'device_id': item.get('device_id', ''),
                'description': item.get('description', ''),
                'altitude': item.get('altitude'),
                'speed': item.get('speed'),
                'heading': item.get('heading'),
                'battery_level': item.get('battery_level'),
                'network_type': item.get('network_type', 'unknown')
            }
            
            # Process location update
            result = self.location_service.process_location_update(user, location_data)
            
            if result['success']:
                return {
                    'success': True,
                    'operation': operation,
                    'location_id': result.get('location_id')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Location sync failed')
                }
                
        except Exception as e:
            logger.error(f"Failed to sync emergency location: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to sync emergency location',
                'details': str(e)
            }
    
    def sync_emergency_medical(self, user: User, item: Dict[str, Any], 
                             operation: str) -> Dict[str, Any]:
        """
        Sync emergency medical data.
        
        Args:
            user: User instance
            item: Medical item data
            operation: Sync operation
            
        Returns:
            Sync result dictionary
        """
        try:
            if operation == 'delete':
                # Handle deletion
                try:
                    medical = EmergencyMedical.objects.get(user=user)
                    medical.delete()
                    return {'success': True, 'operation': 'deleted'}
                except EmergencyMedical.DoesNotExist:
                    return {'success': True, 'operation': 'already_deleted'}
            
            # Handle create/update
            medical_data = {
                'blood_type': item.get('blood_type'),
                'allergies': item.get('allergies', []),
                'medications': item.get('medications', []),
                'medical_conditions': item.get('medical_conditions', []),
                'emergency_contact_name': item.get('emergency_contact_name', ''),
                'emergency_contact_phone': item.get('emergency_contact_phone', ''),
                'emergency_contact_relationship': item.get('emergency_contact_relationship', ''),
                'consent_level': item.get('consent_level', 'none')
            }
            
            # Process medical data update
            result = self.medical_service.update_medical_data(user, medical_data)
            
            if result['success']:
                return {
                    'success': True,
                    'operation': operation,
                    'consent_level': result.get('consent_level')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Medical data sync failed')
                }
                
        except Exception as e:
            logger.error(f"Failed to sync emergency medical: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to sync emergency medical',
                'details': str(e)
            }
    
    def check_sync_conflict(self, data_type: str, item_id: str, 
                          timestamp: str) -> Dict[str, Any]:
        """
        Check for sync conflicts.
        
        Args:
            data_type: Type of data
            item_id: Item identifier
            timestamp: Item timestamp
            
        Returns:
            Conflict check result
        """
        try:
            # Check if item exists and has been modified since timestamp
            if data_type == 'emergency_location':
                try:
                    location = EmergencyLocation.objects.get(id=item_id)
                    if location.updated_at > datetime.fromisoformat(timestamp.replace('Z', '+00:00')):
                        return {
                            'has_conflict': True,
                            'conflict_type': 'server_modified',
                            'server_timestamp': location.updated_at.isoformat(),
                            'client_timestamp': timestamp
                        }
                except EmergencyLocation.DoesNotExist:
                    pass
            
            elif data_type == 'emergency_medical':
                try:
                    medical = EmergencyMedical.objects.get(id=item_id)
                    if medical.updated_at > datetime.fromisoformat(timestamp.replace('Z', '+00:00')):
                        return {
                            'has_conflict': True,
                            'conflict_type': 'server_modified',
                            'server_timestamp': medical.updated_at.isoformat(),
                            'client_timestamp': timestamp
                        }
                except EmergencyMedical.DoesNotExist:
                    pass
            
            return {'has_conflict': False}
            
        except Exception as e:
            logger.error(f"Failed to check sync conflict: {str(e)}")
            return {'has_conflict': False}
    
    def resolve_sync_conflict(self, user: User, data_type: str, item: Dict[str, Any], 
                            conflict_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve sync conflicts.
        
        Args:
            user: User instance
            data_type: Type of data
            item: Item data
            conflict_info: Conflict information
            
        Returns:
            Conflict resolution result
        """
        try:
            # For now, use server-wins strategy
            # In a production system, this would be more sophisticated
            conflict_type = conflict_info.get('conflict_type', 'server_modified')
            
            if conflict_type == 'server_modified':
                return {
                    'success': True,
                    'conflict': True,
                    'resolution': 'server_wins',
                    'message': 'Server version is newer, keeping server data'
                }
            else:
                return {
                    'success': True,
                    'conflict': True,
                    'resolution': 'client_wins',
                    'message': 'Client version accepted'
                }
                
        except Exception as e:
            logger.error(f"Failed to resolve sync conflict: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to resolve sync conflict',
                'details': str(e)
            }
    
    def get_sync_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sync session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        try:
            cache_key = f"{self.CACHE_PREFIX}:session:{session_id}"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get sync session: {str(e)}")
            return None
    
    def update_sync_session(self, session_id: str, update_data: Dict[str, Any]):
        """
        Update sync session information.
        
        Args:
            session_id: Session identifier
            update_data: Data to update
        """
        try:
            cache_key = f"{self.CACHE_PREFIX}:session:{session_id}"
            session = cache.get(cache_key)
            
            if session:
                session.update(update_data)
                session['last_activity'] = django_timezone.now().isoformat()
                cache.set(cache_key, session, self.CACHE_TIMEOUT)
                
        except Exception as e:
            logger.error(f"Failed to update sync session: {str(e)}")
    
    def close_sync_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close a sync session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Close result dictionary
        """
        try:
            session = self.get_sync_session(session_id)
            if not session:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
            
            # Update session status
            self.update_sync_session(session_id, {'status': 'closed'})
            
            # Remove from user's active sessions
            user_sessions_key = f"{self.CACHE_PREFIX}:user_sessions:{session['user_id']}"
            user_sessions = cache.get(user_sessions_key, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
                cache.set(user_sessions_key, user_sessions, self.CACHE_TIMEOUT)
            
            logger.info(f"Closed offline sync session {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'status': 'closed',
                'timestamp': django_timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to close sync session: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to close sync session',
                'details': str(e)
            }
    
    def get_user_offline_data(self, user: User, data_types: List[str] = None) -> Dict[str, Any]:
        """
        Get user's offline data for synchronization.
        
        Args:
            user: User instance
            data_types: Types of data to retrieve
            
        Returns:
            Offline data dictionary
        """
        try:
            if data_types is None:
                data_types = list(self.DATA_TYPES.keys())
            
            offline_data = {}
            
            # Get emergency locations
            if 'emergency_location' in data_types:
                locations = EmergencyLocation.objects.filter(user=user).order_by('-created_at')
                offline_data['emergency_location'] = [
                    {
                        'id': str(location.id),
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'accuracy': location.accuracy,
                        'emergency_type': location.emergency_type,
                        'description': location.description,
                        'device_id': location.device_id,
                        'altitude': location.altitude,
                        'speed': location.speed,
                        'heading': location.heading,
                        'battery_level': location.battery_level,
                        'network_type': location.network_type,
                        'created_at': location.created_at.isoformat(),
                        'updated_at': location.updated_at.isoformat(),
                        'is_active': location.is_active
                    }
                    for location in locations
                ]
            
            # Get emergency medical data
            if 'emergency_medical' in data_types:
                try:
                    medical = EmergencyMedical.objects.get(user=user)
                    offline_data['emergency_medical'] = [{
                        'id': str(medical.id),
                        'blood_type': medical.blood_type,
                        'allergies': medical.allergies,
                        'medications': medical.medications,
                        'medical_conditions': medical.medical_conditions,
                        'emergency_contact_name': medical.emergency_contact_name,
                        'emergency_contact_phone': medical.emergency_contact_phone,
                        'emergency_contact_relationship': medical.emergency_contact_relationship,
                        'consent_level': medical.consent_level,
                        'created_at': medical.created_at.isoformat(),
                        'updated_at': medical.updated_at.isoformat()
                    }]
                except EmergencyMedical.DoesNotExist:
                    offline_data['emergency_medical'] = []
            
            return {
                'success': True,
                'data': offline_data,
                'timestamp': django_timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user offline data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get offline data',
                'details': str(e)
            }
    
    def generate_sync_checksum(self, data: Dict[str, Any]) -> str:
        """
        Generate checksum for sync data.
        
        Args:
            data: Data to generate checksum for
            
        Returns:
            Checksum string
        """
        try:
            # Convert data to JSON string
            json_str = json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder)
            
            # Generate MD5 checksum
            checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
            
            return checksum
            
        except Exception as e:
            logger.error(f"Failed to generate sync checksum: {str(e)}")
            return ''
    
    def validate_sync_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate sync data integrity.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            warnings = []
            
            # Validate data structure
            if not isinstance(data, dict):
                errors.append('Data must be a dictionary')
                return {'valid': False, 'errors': errors, 'warnings': warnings}
            
            # Validate each data type
            for data_type, items in data.items():
                if data_type not in self.DATA_TYPES:
                    warnings.append(f'Unknown data type: {data_type}')
                    continue
                
                if not isinstance(items, list):
                    errors.append(f'Items for {data_type} must be a list')
                    continue
                
                # Validate individual items
                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        errors.append(f'Item {i} in {data_type} must be a dictionary')
                        continue
                    
                    if 'id' not in item:
                        errors.append(f'Item {i} in {data_type} missing ID')
                        continue
                    
                    if 'timestamp' not in item:
                        warnings.append(f'Item {i} in {data_type} missing timestamp')
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Failed to validate sync data: {str(e)}")
            return {
                'valid': False,
                'errors': ['Validation failed'],
                'warnings': []
            }
    
    def create_offline_panic_record(self, user: User, emergency_type: str, 
                                  location_data: Dict[str, Any], device_info: Dict[str, Any],
                                  context: Dict[str, Any], offline_data: Dict[str, Any]) -> str:
        """
        Create offline panic record for later sync.
        
        Args:
            user: User instance
            emergency_type: Type of emergency
            location_data: Location data
            device_info: Device information
            context: Emergency context
            offline_data: Offline data
            
        Returns:
            Offline record ID
        """
        try:
            import uuid
            offline_id = str(uuid.uuid4())
            
            # Create offline panic record
            panic_record = {
                'offline_id': offline_id,
                'user_id': user.id,
                'emergency_type': emergency_type,
                'location_data': location_data,
                'device_info': device_info,
                'context': context,
                'offline_data': offline_data,
                'created_at': django_timezone.now().isoformat(),
                'status': 'pending_sync'
            }
            
            # Store in cache
            cache_key = f"{self.CACHE_PREFIX}:panic:{offline_id}"
            cache.set(cache_key, panic_record, self.CACHE_TIMEOUT)
            
            # Add to user's offline records
            user_records_key = f"{self.CACHE_PREFIX}:user_panic_records:{user.id}"
            user_records = cache.get(user_records_key, [])
            user_records.append(offline_id)
            cache.set(user_records_key, user_records, self.CACHE_TIMEOUT)
            
            logger.info(f"Created offline panic record {offline_id} for user {user.id}")
            
            return offline_id
            
        except Exception as e:
            logger.error(f"Failed to create offline panic record: {str(e)}")
            raise
    
    def resolve_sync_conflicts(self, user: User, session_id: str, 
                             conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve sync conflicts.
        
        Args:
            user: User instance
            session_id: Sync session ID
            conflicts: List of conflicts to resolve
            
        Returns:
            Resolution result
        """
        try:
            resolved_count = 0
            
            for conflict in conflicts:
                data_type = conflict.get('data_type')
                item_id = conflict.get('item_id')
                resolution = conflict.get('resolution')
                
                if not all([data_type, item_id, resolution]):
                    continue
                
                # Apply resolution
                if resolution == 'server_wins':
                    # Keep server version (do nothing)
                    resolved_count += 1
                elif resolution == 'client_wins':
                    # Apply client version
                    # This would be implemented based on specific requirements
                    resolved_count += 1
                elif resolution == 'merge':
                    # Merge client and server versions
                    # This would be implemented based on specific requirements
                    resolved_count += 1
            
            return {
                'success': True,
                'resolved_conflicts': resolved_count
            }
            
        except Exception as e:
            logger.error(f"Failed to resolve sync conflicts: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to resolve sync conflicts',
                'details': str(e)
            }
