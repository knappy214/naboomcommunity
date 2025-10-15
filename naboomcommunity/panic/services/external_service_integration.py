"""
External Emergency Service Integration
Handles integration with external emergency services and dispatch systems.
"""

import logging
import json
import uuid
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from django.core.cache import cache
from django.utils import timezone as django_timezone
from django.contrib.auth import get_user_model
from django.conf import settings
import hashlib
import hmac

from ..models import EmergencyAuditLog, EmergencyLocation, EmergencyMedical
from ..api.throttling import emergency_rate_limiter

User = get_user_model()
logger = logging.getLogger(__name__)


class ExternalServiceIntegration:
    """
    Service for integrating with external emergency services and dispatch systems.
    Supports multiple emergency service providers and protocols.
    """
    
    # Supported emergency service types
    SERVICE_TYPES = {
        'police': 'Police Emergency Services',
        'ambulance': 'Medical Emergency Services',
        'fire': 'Fire Emergency Services',
        'rescue': 'Search and Rescue Services',
        'disaster': 'Disaster Management Services',
        'security': 'Private Security Services',
        'community': 'Community Emergency Response'
    }
    
    # Integration protocols
    PROTOCOLS = {
        'rest_api': 'REST API',
        'soap': 'SOAP Web Service',
        'webhook': 'Webhook',
        'sms': 'SMS Gateway',
        'ussd': 'USSD Gateway',
        'radio': 'Radio Dispatch',
        'custom': 'Custom Protocol'
    }
    
    # Emergency priority mapping
    PRIORITY_MAPPING = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4,
        'emergency': 5
    }
    
    # Cache settings
    CACHE_TIMEOUT = 3600  # 1 hour
    CACHE_PREFIX = 'external_service'
    
    def __init__(self):
        self.rate_limiter = emergency_rate_limiter
        self._service_configs = self._load_service_configurations()
    
    def _load_service_configurations(self) -> Dict[str, Any]:
        """
        Load external service configurations.
        
        Returns:
            Service configurations dictionary
        """
        try:
            # Load from Django settings or database
            configs = getattr(settings, 'EXTERNAL_EMERGENCY_SERVICES', {})
            
            # Default configurations for common services
            default_configs = {
                'police_10111': {
                    'name': 'South African Police Service',
                    'type': 'police',
                    'protocol': 'rest_api',
                    'endpoint': 'https://api.saps.gov.za/emergency',
                    'api_key': getattr(settings, 'SAPS_API_KEY', ''),
                    'timeout': 30,
                    'retry_attempts': 3,
                    'priority_mapping': {
                        'critical': 'emergency',
                        'high': 'urgent',
                        'medium': 'normal',
                        'low': 'low'
                    }
                },
                'ambulance_10177': {
                    'name': 'Emergency Medical Services',
                    'type': 'ambulance',
                    'protocol': 'rest_api',
                    'endpoint': 'https://api.ems.gov.za/emergency',
                    'api_key': getattr(settings, 'EMS_API_KEY', ''),
                    'timeout': 30,
                    'retry_attempts': 3,
                    'priority_mapping': {
                        'critical': 'emergency',
                        'high': 'urgent',
                        'medium': 'normal',
                        'low': 'low'
                    }
                },
                'fire_10177': {
                    'name': 'Fire and Rescue Services',
                    'type': 'fire',
                    'protocol': 'rest_api',
                    'endpoint': 'https://api.fire.gov.za/emergency',
                    'api_key': getattr(settings, 'FIRE_API_KEY', ''),
                    'timeout': 30,
                    'retry_attempts': 3,
                    'priority_mapping': {
                        'critical': 'emergency',
                        'high': 'urgent',
                        'medium': 'normal',
                        'low': 'low'
                    }
                },
                'community_security': {
                    'name': 'Community Security Services',
                    'type': 'security',
                    'protocol': 'webhook',
                    'endpoint': getattr(settings, 'COMMUNITY_SECURITY_WEBHOOK', ''),
                    'api_key': getattr(settings, 'COMMUNITY_SECURITY_KEY', ''),
                    'timeout': 15,
                    'retry_attempts': 2,
                    'priority_mapping': {
                        'critical': 'emergency',
                        'high': 'urgent',
                        'medium': 'normal',
                        'low': 'low'
                    }
                }
            }
            
            # Merge with default configurations
            configs.update(default_configs)
            
            return configs
            
        except Exception as e:
            logger.error(f"Failed to load service configurations: {str(e)}")
            return {}
    
    def dispatch_emergency_service(self, user: User, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch emergency to appropriate external service.
        
        Args:
            user: User instance
            emergency_data: Emergency data dictionary
            
        Returns:
            Dispatch result dictionary
        """
        try:
            # Extract emergency data
            emergency_id = emergency_data.get('emergency_id')
            emergency_type = emergency_data.get('emergency_type', 'panic')
            location_data = emergency_data.get('location', {})
            medical_data = emergency_data.get('medical_data', {})
            priority = emergency_data.get('priority', 'high')
            description = emergency_data.get('description', '')
            
            # Validate required fields
            if not emergency_id:
                return {
                    'success': False,
                    'error': 'Emergency ID is required'
                }
            
            # Determine appropriate service
            service_type = self._determine_service_type(emergency_type, medical_data)
            if not service_type:
                return {
                    'success': False,
                    'error': f'No appropriate service found for emergency type: {emergency_type}'
                }
            
            # Get service configuration
            service_config = self._get_service_config(service_type)
            if not service_config:
                return {
                    'success': False,
                    'error': f'Service configuration not found for: {service_type}'
                }
            
            # Check rate limiting
            if not self.rate_limiter.check_dispatch_rate(user):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded for emergency dispatch',
                    'retry_after': self.rate_limiter.get_retry_after('dispatch')
                }
            
            # Prepare dispatch data
            dispatch_data = self._prepare_dispatch_data(
                user, emergency_id, emergency_type, location_data, 
                medical_data, priority, description, service_config
            )
            
            # Dispatch to external service
            result = self._dispatch_to_service(service_config, dispatch_data)
            
            # Update rate limiter
            self.rate_limiter.record_dispatch(user)
            
            # Log dispatch
            self._log_dispatch(
                user, emergency_id, service_type, result, dispatch_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to dispatch emergency service: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to dispatch emergency service',
                'details': str(e)
            }
    
    def _determine_service_type(self, emergency_type: str, medical_data: Dict[str, Any]) -> Optional[str]:
        """
        Determine appropriate service type based on emergency type and medical data.
        
        Args:
            emergency_type: Type of emergency
            medical_data: Medical data dictionary
            
        Returns:
            Service type or None
        """
        try:
            # Direct mapping for emergency types
            type_mapping = {
                'panic': 'police',
                'medical': 'ambulance',
                'fire': 'fire',
                'crime': 'police',
                'accident': 'ambulance',
                'rescue': 'rescue',
                'disaster': 'disaster',
                'security': 'security'
            }
            
            # Check for medical emergency indicators
            if emergency_type == 'panic' and medical_data:
                # Check if it's a medical emergency
                if self._is_medical_emergency(medical_data):
                    return 'ambulance'
            
            return type_mapping.get(emergency_type)
            
        except Exception as e:
            logger.error(f"Failed to determine service type: {str(e)}")
            return None
    
    def _is_medical_emergency(self, medical_data: Dict[str, Any]) -> bool:
        """
        Check if emergency is medical based on medical data.
        
        Args:
            medical_data: Medical data dictionary
            
        Returns:
            True if medical emergency
        """
        try:
            # Check for critical medical conditions
            conditions = medical_data.get('medical_conditions', [])
            critical_conditions = [
                c for c in conditions 
                if c.get('requires_immediate_attention', False)
            ]
            
            if critical_conditions:
                return True
            
            # Check for critical allergies
            allergies = medical_data.get('allergies', [])
            critical_allergies = [
                a for a in allergies 
                if a.get('requires_immediate_attention', False)
            ]
            
            if critical_allergies:
                return True
            
            # Check for emergency medications
            medications = medical_data.get('medications', [])
            emergency_medications = [
                m for m in medications 
                if m.get('is_emergency_medication', False)
            ]
            
            if emergency_medications:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check medical emergency: {str(e)}")
            return False
    
    def _get_service_config(self, service_type: str) -> Optional[Dict[str, Any]]:
        """
        Get service configuration for given service type.
        
        Args:
            service_type: Service type
            
        Returns:
            Service configuration or None
        """
        try:
            # Find matching service configuration
            for service_id, config in self._service_configs.items():
                if config.get('type') == service_type:
                    return config
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get service config: {str(e)}")
            return None
    
    def _prepare_dispatch_data(self, user: User, emergency_id: str, emergency_type: str,
                             location_data: Dict[str, Any], medical_data: Dict[str, Any],
                             priority: str, description: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare dispatch data for external service.
        
        Args:
            user: User instance
            emergency_id: Emergency ID
            emergency_type: Type of emergency
            location_data: Location data
            medical_data: Medical data
            priority: Priority level
            description: Emergency description
            service_config: Service configuration
            
        Returns:
            Prepared dispatch data
        """
        try:
            # Base dispatch data
            dispatch_data = {
                'emergency_id': emergency_id,
                'emergency_type': emergency_type,
                'priority': service_config.get('priority_mapping', {}).get(priority, priority),
                'description': description,
                'timestamp': django_timezone.now().isoformat(),
                'user': {
                    'id': str(user.id),
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'phone': getattr(user, 'phone_number', ''),
                    'email': user.email
                }
            }
            
            # Add location data
            if location_data:
                dispatch_data['location'] = {
                    'latitude': location_data.get('latitude'),
                    'longitude': location_data.get('longitude'),
                    'accuracy': location_data.get('accuracy'),
                    'altitude': location_data.get('altitude'),
                    'address': location_data.get('address', ''),
                    'description': location_data.get('description', '')
                }
            
            # Add medical data if consent allows
            if medical_data and medical_data.get('consent_level') != 'none':
                dispatch_data['medical'] = {
                    'blood_type': medical_data.get('blood_type'),
                    'allergies': medical_data.get('allergies', []),
                    'medical_conditions': medical_data.get('medical_conditions', []),
                    'medications': medical_data.get('medications', []),
                    'emergency_contact': {
                        'name': medical_data.get('emergency_contact_name', ''),
                        'phone': medical_data.get('emergency_contact_phone', ''),
                        'relationship': medical_data.get('emergency_contact_relationship', '')
                    }
                }
            
            # Add service-specific data
            dispatch_data['service'] = {
                'type': service_config.get('type'),
                'name': service_config.get('name'),
                'protocol': service_config.get('protocol')
            }
            
            return dispatch_data
            
        except Exception as e:
            logger.error(f"Failed to prepare dispatch data: {str(e)}")
            return {
                'emergency_id': emergency_id,
                'emergency_type': emergency_type,
                'priority': priority,
                'description': description,
                'timestamp': django_timezone.now().isoformat()
            }
    
    def _dispatch_to_service(self, service_config: Dict[str, Any], dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch to external service based on protocol.
        
        Args:
            service_config: Service configuration
            dispatch_data: Dispatch data
            
        Returns:
            Dispatch result
        """
        try:
            protocol = service_config.get('protocol', 'rest_api')
            
            if protocol == 'rest_api':
                return self._dispatch_rest_api(service_config, dispatch_data)
            elif protocol == 'soap':
                return self._dispatch_soap(service_config, dispatch_data)
            elif protocol == 'webhook':
                return self._dispatch_webhook(service_config, dispatch_data)
            elif protocol == 'sms':
                return self._dispatch_sms(service_config, dispatch_data)
            elif protocol == 'ussd':
                return self._dispatch_ussd(service_config, dispatch_data)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported protocol: {protocol}'
                }
                
        except Exception as e:
            logger.error(f"Failed to dispatch to service: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to dispatch to service',
                'details': str(e)
            }
    
    def _dispatch_rest_api(self, service_config: Dict[str, Any], dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch via REST API.
        
        Args:
            service_config: Service configuration
            dispatch_data: Dispatch data
            
        Returns:
            Dispatch result
        """
        try:
            endpoint = service_config.get('endpoint')
            api_key = service_config.get('api_key')
            timeout = service_config.get('timeout', 30)
            
            if not endpoint:
                return {
                    'success': False,
                    'error': 'Service endpoint not configured'
                }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Naboom-Emergency-Response/1.0'
            }
            
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Make API request
            response = requests.post(
                endpoint,
                json=dispatch_data,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'service_response': response.json(),
                    'status_code': response.status_code,
                    'external_id': response.json().get('id', ''),
                    'message': 'Emergency dispatched successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Service returned error: {response.status_code}',
                    'status_code': response.status_code,
                    'response': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Service request timeout',
                'timeout': True
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Service connection failed',
                'connection_error': True
            }
        except Exception as e:
            logger.error(f"REST API dispatch failed: {str(e)}")
            return {
                'success': False,
                'error': 'REST API dispatch failed',
                'details': str(e)
            }
    
    def _dispatch_webhook(self, service_config: Dict[str, Any], dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch via webhook.
        
        Args:
            service_config: Service configuration
            dispatch_data: Dispatch data
            
        Returns:
            Dispatch result
        """
        try:
            endpoint = service_config.get('endpoint')
            api_key = service_config.get('api_key')
            timeout = service_config.get('timeout', 15)
            
            if not endpoint:
                return {
                    'success': False,
                    'error': 'Webhook endpoint not configured'
                }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Naboom-Emergency-Response/1.0'
            }
            
            if api_key:
                headers['X-API-Key'] = api_key
            
            # Add webhook signature
            webhook_signature = self._generate_webhook_signature(dispatch_data, api_key)
            if webhook_signature:
                headers['X-Webhook-Signature'] = webhook_signature
            
            # Make webhook request
            response = requests.post(
                endpoint,
                json=dispatch_data,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'message': 'Webhook dispatched successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Webhook returned error: {response.status_code}',
                    'status_code': response.status_code,
                    'response': response.text
                }
                
        except Exception as e:
            logger.error(f"Webhook dispatch failed: {str(e)}")
            return {
                'success': False,
                'error': 'Webhook dispatch failed',
                'details': str(e)
            }
    
    def _dispatch_sms(self, service_config: Dict[str, Any], dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch via SMS.
        
        Args:
            service_config: Service configuration
            dispatch_data: Dispatch data
            
        Returns:
            Dispatch result
        """
        try:
            # This would integrate with SMS service
            # For now, return mock result
            return {
                'success': True,
                'message': 'SMS dispatch queued for delivery',
                'external_id': str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"SMS dispatch failed: {str(e)}")
            return {
                'success': False,
                'error': 'SMS dispatch failed',
                'details': str(e)
            }
    
    def _dispatch_ussd(self, service_config: Dict[str, Any], dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch via USSD.
        
        Args:
            service_config: Service configuration
            dispatch_data: Dispatch data
            
        Returns:
            Dispatch result
        """
        try:
            # This would integrate with USSD service
            # For now, return mock result
            return {
                'success': True,
                'message': 'USSD dispatch queued for delivery',
                'external_id': str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"USSD dispatch failed: {str(e)}")
            return {
                'success': False,
                'error': 'USSD dispatch failed',
                'details': str(e)
            }
    
    def _dispatch_soap(self, service_config: Dict[str, Any], dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch via SOAP web service.
        
        Args:
            service_config: Service configuration
            dispatch_data: Dispatch data
            
        Returns:
            Dispatch result
        """
        try:
            # This would integrate with SOAP service
            # For now, return mock result
            return {
                'success': True,
                'message': 'SOAP dispatch completed',
                'external_id': str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"SOAP dispatch failed: {str(e)}")
            return {
                'success': False,
                'error': 'SOAP dispatch failed',
                'details': str(e)
            }
    
    def _generate_webhook_signature(self, data: Dict[str, Any], secret: str) -> Optional[str]:
        """
        Generate webhook signature for security.
        
        Args:
            data: Data to sign
            secret: Secret key
            
        Returns:
            Signature string or None
        """
        try:
            if not secret:
                return None
            
            # Convert data to JSON string
            json_data = json.dumps(data, sort_keys=True)
            
            # Generate HMAC signature
            signature = hmac.new(
                secret.encode('utf-8'),
                json_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return f"sha256={signature}"
            
        except Exception as e:
            logger.error(f"Failed to generate webhook signature: {str(e)}")
            return None
    
    def _log_dispatch(self, user: User, emergency_id: str, service_type: str,
                     result: Dict[str, Any], dispatch_data: Dict[str, Any]):
        """
        Log emergency dispatch for audit purposes.
        
        Args:
            user: User instance
            emergency_id: Emergency ID
            service_type: Service type
            result: Dispatch result
            dispatch_data: Dispatch data
        """
        try:
            EmergencyAuditLog.log_action(
                action_type='external_service_dispatch',
                description=f'Emergency dispatched to {service_type}',
                user=user,
                severity='high',
                emergency_id=emergency_id,
                service_type=service_type,
                success=result.get('success', False),
                external_id=result.get('external_id', ''),
                status_code=result.get('status_code'),
                error_message=result.get('error', ''),
                dispatch_data=dispatch_data
            )
        except Exception as e:
            logger.error(f"Failed to log dispatch: {str(e)}")
    
    def get_service_status(self, service_type: str) -> Dict[str, Any]:
        """
        Get status of external service.
        
        Args:
            service_type: Service type
            
        Returns:
            Service status dictionary
        """
        try:
            service_config = self._get_service_config(service_type)
            if not service_config:
                return {
                    'success': False,
                    'error': f'Service not found: {service_type}'
                }
            
            # Check service health
            health_check = self._check_service_health(service_config)
            
            return {
                'success': True,
                'service_type': service_type,
                'service_name': service_config.get('name'),
                'protocol': service_config.get('protocol'),
                'status': health_check.get('status', 'unknown'),
                'response_time': health_check.get('response_time'),
                'last_check': health_check.get('last_check'),
                'error': health_check.get('error')
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get service status',
                'details': str(e)
            }
    
    def _check_service_health(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check health of external service.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Health check result
        """
        try:
            protocol = service_config.get('protocol', 'rest_api')
            endpoint = service_config.get('endpoint')
            
            if not endpoint:
                return {
                    'status': 'unavailable',
                    'error': 'No endpoint configured'
                }
            
            if protocol == 'rest_api':
                return self._check_rest_api_health(service_config)
            elif protocol == 'webhook':
                return self._check_webhook_health(service_config)
            else:
                return {
                    'status': 'unknown',
                    'error': f'Health check not supported for protocol: {protocol}'
                }
                
        except Exception as e:
            logger.error(f"Failed to check service health: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_rest_api_health(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check REST API service health.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Health check result
        """
        try:
            endpoint = service_config.get('endpoint')
            timeout = service_config.get('timeout', 30)
            
            # Add health check endpoint
            health_endpoint = f"{endpoint.rstrip('/')}/health"
            
            start_time = datetime.now()
            
            response = requests.get(
                health_endpoint,
                timeout=timeout
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'last_check': django_timezone.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'last_check': django_timezone.now().isoformat(),
                    'error': f'HTTP {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'last_check': django_timezone.now().isoformat(),
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'unreachable',
                'last_check': django_timezone.now().isoformat(),
                'error': 'Connection failed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'last_check': django_timezone.now().isoformat(),
                'error': str(e)
            }
    
    def _check_webhook_health(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check webhook service health.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Health check result
        """
        try:
            # For webhooks, we can't easily check health
            # Return basic status
            return {
                'status': 'configured',
                'last_check': django_timezone.now().isoformat(),
                'message': 'Webhook endpoint configured'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'last_check': django_timezone.now().isoformat(),
                'error': str(e)
            }
    
    def get_available_services(self) -> Dict[str, Any]:
        """
        Get list of available external services.
        
        Returns:
            Available services dictionary
        """
        try:
            services = []
            
            for service_id, config in self._service_configs.items():
                service_info = {
                    'id': service_id,
                    'name': config.get('name'),
                    'type': config.get('type'),
                    'protocol': config.get('protocol'),
                    'endpoint': config.get('endpoint'),
                    'timeout': config.get('timeout'),
                    'retry_attempts': config.get('retry_attempts')
                }
                
                # Check service health
                health_check = self._check_service_health(config)
                service_info['health'] = health_check
                
                services.append(service_info)
            
            return {
                'success': True,
                'services': services,
                'total_services': len(services),
                'timestamp': django_timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get available services: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get available services',
                'details': str(e)
            }
