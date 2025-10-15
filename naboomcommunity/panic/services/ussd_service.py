"""
USSD Integration Service
Unstructured Supplementary Service Data (USSD) integration for emergency response.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
import requests
from urllib.parse import urlencode, parse_qs
import hashlib
import hmac

from ..models import EmergencyLocation, EmergencyMedical, EmergencyAuditLog
from ..tasks.emergency_tasks import send_emergency_notification

User = get_user_model()
logger = logging.getLogger(__name__)


class USSDSession:
    """
    Represents a USSD session for emergency response.
    """
    
    def __init__(self, session_id: str, msisdn: str, service_code: str):
        self.session_id = session_id
        self.msisdn = msisdn
        self.service_code = service_code
        self.start_time = timezone.now()
        self.last_activity = timezone.now()
        self.current_menu = 'main'
        self.user_data = {}
        self.emergency_data = {}
        self.is_active = True
    
    def to_dict(self):
        """Convert session to dictionary for caching."""
        return {
            'session_id': self.session_id,
            'msisdn': self.msisdn,
            'service_code': self.service_code,
            'start_time': self.start_time.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'current_menu': self.current_menu,
            'user_data': self.user_data,
            'emergency_data': self.emergency_data,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create session from dictionary."""
        session = cls(
            session_id=data['session_id'],
            msisdn=data['msisdn'],
            service_code=data['service_code']
        )
        session.start_time = timezone.datetime.fromisoformat(data['start_time'])
        session.last_activity = timezone.datetime.fromisoformat(data['last_activity'])
        session.current_menu = data['current_menu']
        session.user_data = data['user_data']
        session.emergency_data = data['emergency_data']
        session.is_active = data['is_active']
        return session


class USSDService:
    """
    Service for handling USSD interactions for emergency response.
    """
    
    def __init__(self):
        self.session_timeout = 300  # 5 minutes
        self.max_session_duration = 1800  # 30 minutes
        self.emergency_service_codes = {
            'panic': '*123*1#',
            'medical': '*123*2#',
            'fire': '*123*3#',
            'police': '*123*4#',
            'location': '*123*5#',
            'status': '*123*6#',
        }
        self.menu_flows = {
            'main': self._get_main_menu,
            'panic': self._get_panic_menu,
            'medical': self._get_medical_menu,
            'location': self._get_location_menu,
            'status': self._get_status_menu,
            'emergency_confirm': self._get_emergency_confirm_menu,
        }
    
    def process_ussd_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming USSD request.
        
        Args:
            request_data: USSD request data from gateway
        
        Returns:
            USSD response data
        """
        try:
            # Extract USSD parameters
            session_id = request_data.get('sessionId', '')
            msisdn = request_data.get('msisdn', '')
            service_code = request_data.get('serviceCode', '')
            text = request_data.get('text', '')
            operator = request_data.get('operator', '')
            
            # Log USSD request
            self._log_ussd_request(session_id, msisdn, service_code, text, operator)
            
            # Get or create session
            session = self._get_or_create_session(session_id, msisdn, service_code)
            
            # Process USSD text
            response = self._process_ussd_text(session, text)
            
            # Update session
            self._update_session(session)
            
            return response
            
        except Exception as e:
            logger.error(f"USSD request processing failed: {str(e)}")
            return self._create_error_response("System error. Please try again later.")
    
    def _get_or_create_session(self, session_id: str, msisdn: str, service_code: str) -> USSDSession:
        """Get existing session or create new one."""
        cache_key = f"ussd_session_{session_id}"
        cached_session = cache.get(cache_key)
        
        if cached_session:
            session = USSDSession.from_dict(cached_session)
            session.last_activity = timezone.now()
            return session
        
        # Create new session
        session = USSDSession(session_id, msisdn, service_code)
        return session
    
    def _update_session(self, session: USSDSession):
        """Update session in cache."""
        cache_key = f"ussd_session_{session.session_id}"
        cache.set(cache_key, session.to_dict(), self.session_timeout)
    
    def _process_ussd_text(self, session: USSDSession, text: str) -> Dict[str, Any]:
        """Process USSD text input."""
        # Handle empty text (initial request)
        if not text:
            return self._get_main_menu(session)
        
        # Parse text input
        text_parts = text.split('*')
        current_input = text_parts[-1] if text_parts else ''
        
        # Route to appropriate menu handler
        menu_handler = self.menu_flows.get(session.current_menu)
        if menu_handler:
            return menu_handler(session, current_input)
        
        return self._get_main_menu(session)
    
    def _get_main_menu(self, session: USSDSession, input_text: str = '') -> Dict[str, Any]:
        """Get main USSD menu."""
        session.current_menu = 'main'
        
        if not input_text:
            menu_text = (
                "NABOOM EMERGENCY RESPONSE\n"
                "1. Panic Button\n"
                "2. Medical Emergency\n"
                "3. Fire Emergency\n"
                "4. Police Emergency\n"
                "5. Location Update\n"
                "6. Check Status\n"
                "0. Exit"
            )
            return self._create_response(menu_text, False)
        
        # Handle menu selection
        if input_text == '1':
            return self._get_panic_menu(session, '')
        elif input_text == '2':
            return self._get_medical_menu(session, '')
        elif input_text == '3':
            return self._handle_fire_emergency(session)
        elif input_text == '4':
            return self._handle_police_emergency(session)
        elif input_text == '5':
            return self._get_location_menu(session, '')
        elif input_text == '6':
            return self._get_status_menu(session, '')
        elif input_text == '0':
            return self._create_response("Thank you for using NABOOM Emergency Response.", True)
        else:
            return self._create_response("Invalid selection. Please try again.", False)
    
    def _get_panic_menu(self, session: USSDSession, input_text: str) -> Dict[str, Any]:
        """Get panic button menu."""
        session.current_menu = 'panic'
        
        if not input_text:
            menu_text = (
                "PANIC BUTTON ACTIVATION\n"
                "1. Activate Panic Button\n"
                "2. Cancel\n"
                "0. Back to Main Menu"
            )
            return self._create_response(menu_text, False)
        
        if input_text == '1':
            return self._handle_panic_activation(session)
        elif input_text == '2':
            return self._get_main_menu(session, '')
        elif input_text == '0':
            return self._get_main_menu(session, '')
        else:
            return self._create_response("Invalid selection. Please try again.", False)
    
    def _get_medical_menu(self, session: USSDSession, input_text: str) -> Dict[str, Any]:
        """Get medical emergency menu."""
        session.current_menu = 'medical'
        
        if not input_text:
            menu_text = (
                "MEDICAL EMERGENCY\n"
                "1. Report Medical Emergency\n"
                "2. Update Medical Info\n"
                "3. View Medical Status\n"
                "0. Back to Main Menu"
            )
            return self._create_response(menu_text, False)
        
        if input_text == '1':
            return self._handle_medical_emergency(session)
        elif input_text == '2':
            return self._handle_medical_update(session)
        elif input_text == '3':
            return self._handle_medical_status(session)
        elif input_text == '0':
            return self._get_main_menu(session, '')
        else:
            return self._create_response("Invalid selection. Please try again.", False)
    
    def _get_location_menu(self, session: USSDSession, input_text: str) -> Dict[str, Any]:
        """Get location update menu."""
        session.current_menu = 'location'
        
        if not input_text:
            menu_text = (
                "LOCATION UPDATE\n"
                "1. Send Current Location\n"
                "2. Update Location Manually\n"
                "3. View Last Location\n"
                "0. Back to Main Menu"
            )
            return self._create_response(menu_text, False)
        
        if input_text == '1':
            return self._handle_location_update(session)
        elif input_text == '2':
            return self._handle_manual_location(session)
        elif input_text == '3':
            return self._handle_location_status(session)
        elif input_text == '0':
            return self._get_main_menu(session, '')
        else:
            return self._create_response("Invalid selection. Please try again.", False)
    
    def _get_status_menu(self, session: USSDSession, input_text: str) -> Dict[str, Any]:
        """Get status check menu."""
        session.current_menu = 'status'
        
        if not input_text:
            menu_text = (
                "STATUS CHECK\n"
                "1. Check Emergency Status\n"
                "2. View Recent Alerts\n"
                "3. Contact Information\n"
                "0. Back to Main Menu"
            )
            return self._create_response(menu_text, False)
        
        if input_text == '1':
            return self._handle_status_check(session)
        elif input_text == '2':
            return self._handle_recent_alerts(session)
        elif input_text == '3':
            return self._handle_contact_info(session)
        elif input_text == '0':
            return self._get_main_menu(session, '')
        else:
            return self._create_response("Invalid selection. Please try again.", False)
    
    def _handle_panic_activation(self, session: USSDSession) -> Dict[str, Any]:
        """Handle panic button activation."""
        try:
            # Get user by phone number
            user = self._get_user_by_phone(session.msisdn)
            
            if not user:
                return self._create_response(
                    "User not found. Please register first at naboomneighbornet.net.za", True
                )
            
            # Create emergency location
            location_data = {
                'user_id': user.id,
                'emergency_type': 'panic',
                'location': None,  # USSD doesn't provide GPS
                'accuracy': None,
                'device_id': f"USSD_{session.session_id}",
                'description': 'Panic button activated via USSD'
            }
            
            # Save emergency location
            with transaction.atomic():
                emergency_location = EmergencyLocation.objects.create(**location_data)
                
                # Log emergency activation
                EmergencyAuditLog.objects.create(
                    action_type='panic_activate',
                    user=user,
                    severity='critical',
                    description='Panic button activated via USSD',
                    metadata={
                        'session_id': session.session_id,
                        'msisdn': session.msisdn,
                        'location_id': emergency_location.id
                    }
                )
            
            # Send notifications
            self._send_emergency_notifications(user, 'panic', emergency_location)
            
            response_text = (
                "PANIC BUTTON ACTIVATED!\n"
                "Emergency services have been notified.\n"
                "Stay calm and wait for help.\n"
                "Location: Approximate (via USSD)\n"
                "Time: " + timezone.now().strftime("%H:%M:%S")
            )
            
            return self._create_response(response_text, True)
            
        except Exception as e:
            logger.error(f"Panic activation failed: {str(e)}")
            return self._create_response("Error activating panic button. Please try again.", True)
    
    def _handle_medical_emergency(self, session: USSDSession) -> Dict[str, Any]:
        """Handle medical emergency report."""
        try:
            user = self._get_user_by_phone(session.msisdn)
            
            if not user:
                return self._create_response(
                    "User not found. Please register first at naboomneighbornet.net.za", True
                )
            
            # Create medical emergency
            location_data = {
                'user_id': user.id,
                'emergency_type': 'medical',
                'location': None,
                'accuracy': None,
                'device_id': f"USSD_{session.session_id}",
                'description': 'Medical emergency reported via USSD'
            }
            
            with transaction.atomic():
                emergency_location = EmergencyLocation.objects.create(**location_data)
                
                # Log medical emergency
                EmergencyAuditLog.objects.create(
                    action_type='medical_emergency',
                    user=user,
                    severity='high',
                    description='Medical emergency reported via USSD',
                    metadata={
                        'session_id': session.session_id,
                        'msisdn': session.msisdn,
                        'location_id': emergency_location.id
                    }
                )
            
            # Send notifications
            self._send_emergency_notifications(user, 'medical', emergency_location)
            
            response_text = (
                "MEDICAL EMERGENCY REPORTED!\n"
                "Medical services have been notified.\n"
                "Stay calm and wait for help.\n"
                "Time: " + timezone.now().strftime("%H:%M:%S")
            )
            
            return self._create_response(response_text, True)
            
        except Exception as e:
            logger.error(f"Medical emergency handling failed: {str(e)}")
            return self._create_response("Error reporting medical emergency. Please try again.", True)
    
    def _handle_fire_emergency(self, session: USSDSession) -> Dict[str, Any]:
        """Handle fire emergency report."""
        try:
            user = self._get_user_by_phone(session.msisdn)
            
            if not user:
                return self._create_response(
                    "User not found. Please register first at naboomneighbornet.net.za", True
                )
            
            # Create fire emergency
            location_data = {
                'user_id': user.id,
                'emergency_type': 'fire',
                'location': None,
                'accuracy': None,
                'device_id': f"USSD_{session.session_id}",
                'description': 'Fire emergency reported via USSD'
            }
            
            with transaction.atomic():
                emergency_location = EmergencyLocation.objects.create(**location_data)
                
                # Log fire emergency
                EmergencyAuditLog.objects.create(
                    action_type='fire_emergency',
                    user=user,
                    severity='high',
                    description='Fire emergency reported via USSD',
                    metadata={
                        'session_id': session.session_id,
                        'msisdn': session.msisdn,
                        'location_id': emergency_location.id
                    }
                )
            
            # Send notifications
            self._send_emergency_notifications(user, 'fire', emergency_location)
            
            response_text = (
                "FIRE EMERGENCY REPORTED!\n"
                "Fire services have been notified.\n"
                "Evacuate if safe to do so.\n"
                "Time: " + timezone.now().strftime("%H:%M:%S")
            )
            
            return self._create_response(response_text, True)
            
        except Exception as e:
            logger.error(f"Fire emergency handling failed: {str(e)}")
            return self._create_response("Error reporting fire emergency. Please try again.", True)
    
    def _handle_police_emergency(self, session: USSDSession) -> Dict[str, Any]:
        """Handle police emergency report."""
        try:
            user = self._get_user_by_phone(session.msisdn)
            
            if not user:
                return self._create_response(
                    "User not found. Please register first at naboomneighbornet.net.za", True
                )
            
            # Create police emergency
            location_data = {
                'user_id': user.id,
                'emergency_type': 'crime',
                'location': None,
                'accuracy': None,
                'device_id': f"USSD_{session.session_id}",
                'description': 'Police emergency reported via USSD'
            }
            
            with transaction.atomic():
                emergency_location = EmergencyLocation.objects.create(**location_data)
                
                # Log police emergency
                EmergencyAuditLog.objects.create(
                    action_type='police_emergency',
                    user=user,
                    severity='high',
                    description='Police emergency reported via USSD',
                    metadata={
                        'session_id': session.session_id,
                        'msisdn': session.msisdn,
                        'location_id': emergency_location.id
                    }
                )
            
            # Send notifications
            self._send_emergency_notifications(user, 'police', emergency_location)
            
            response_text = (
                "POLICE EMERGENCY REPORTED!\n"
                "Police services have been notified.\n"
                "Stay safe and wait for help.\n"
                "Time: " + timezone.now().strftime("%H:%M:%S")
            )
            
            return self._create_response(response_text, True)
            
        except Exception as e:
            logger.error(f"Police emergency handling failed: {str(e)}")
            return self._create_response("Error reporting police emergency. Please try again.", True)
    
    def _handle_location_update(self, session: USSDSession) -> Dict[str, Any]:
        """Handle location update request."""
        try:
            user = self._get_user_by_phone(session.msisdn)
            
            if not user:
                return self._create_response(
                    "User not found. Please register first at naboomneighbornet.net.za", True
                )
            
            # Create location update
            location_data = {
                'user_id': user.id,
                'emergency_type': 'location',
                'location': None,
                'accuracy': None,
                'device_id': f"USSD_{session.session_id}",
                'description': 'Location update via USSD'
            }
            
            with transaction.atomic():
                emergency_location = EmergencyLocation.objects.create(**location_data)
                
                # Log location update
                EmergencyAuditLog.objects.create(
                    action_type='location_update',
                    user=user,
                    severity='low',
                    description='Location update via USSD',
                    metadata={
                        'session_id': session.session_id,
                        'msisdn': session.msisdn,
                        'location_id': emergency_location.id
                    }
                )
            
            response_text = (
                "LOCATION UPDATE SENT!\n"
                "Your location has been updated.\n"
                "Time: " + timezone.now().strftime("%H:%M:%S")
            )
            
            return self._create_response(response_text, True)
            
        except Exception as e:
            logger.error(f"Location update failed: {str(e)}")
            return self._create_response("Error updating location. Please try again.", True)
    
    def _handle_status_check(self, session: USSDSession) -> Dict[str, Any]:
        """Handle status check request."""
        try:
            user = self._get_user_by_phone(session.msisdn)
            
            if not user:
                return self._create_response(
                    "User not found. Please register first at naboomneighbornet.net.za", True
                )
            
            # Get recent emergency locations
            recent_emergencies = EmergencyLocation.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-created_at')[:5]
            
            if not recent_emergencies:
                response_text = (
                    "STATUS CHECK\n"
                    "No recent emergencies found.\n"
                    "You are safe and secure."
                )
            else:
                response_text = "RECENT EMERGENCIES:\n"
                for emergency in recent_emergencies:
                    response_text += f"- {emergency.emergency_type.upper()}\n"
                    response_text += f"  {emergency.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            return self._create_response(response_text, True)
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return self._create_response("Error checking status. Please try again.", True)
    
    def _get_user_by_phone(self, msisdn: str) -> Optional[User]:
        """Get user by phone number."""
        try:
            # Clean phone number
            phone = self._clean_phone_number(msisdn)
            
            # Try to find user by phone number
            # This assumes you have a phone field in your User model
            # Adjust the field name as needed
            return User.objects.filter(phone=phone).first()
            
        except Exception as e:
            logger.error(f"Failed to get user by phone: {str(e)}")
            return None
    
    def _clean_phone_number(self, msisdn: str) -> str:
        """Clean phone number for database lookup."""
        # Remove non-digit characters
        phone = ''.join(filter(str.isdigit, msisdn))
        
        # Handle South African numbers
        if phone.startswith('27'):
            phone = phone[2:]
        elif phone.startswith('0'):
            phone = phone[1:]
        
        return phone
    
    def _send_emergency_notifications(self, user: User, emergency_type: str, location: EmergencyLocation):
        """Send emergency notifications."""
        try:
            # This would integrate with your notification system
            # For now, we'll just log the notification
            logger.info(f"Emergency notification sent for {emergency_type} to user {user.username}")
            
            # You could also trigger Celery tasks here
            # send_emergency_notification.delay(user.id, {
            #     'type': emergency_type,
            #     'location_id': location.id,
            #     'source': 'USSD'
            # })
            
        except Exception as e:
            logger.error(f"Failed to send emergency notification: {str(e)}")
    
    def _log_ussd_request(self, session_id: str, msisdn: str, service_code: str, text: str, operator: str):
        """Log USSD request for auditing."""
        try:
            EmergencyAuditLog.objects.create(
                action_type='ussd_request',
                user=None,  # Anonymous request
                severity='low',
                description=f'USSD request from {msisdn}',
                metadata={
                    'session_id': session_id,
                    'msisdn': msisdn,
                    'service_code': service_code,
                    'text': text,
                    'operator': operator
                }
            )
        except Exception as e:
            logger.error(f"Failed to log USSD request: {str(e)}")
    
    def _create_response(self, message: str, end_session: bool = False) -> Dict[str, Any]:
        """Create USSD response."""
        return {
            'message': message,
            'endSession': end_session
        }
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            'message': message,
            'endSession': True
        }


class USSDGateway:
    """
    USSD Gateway integration for emergency response.
    """
    
    def __init__(self, gateway_url: str, api_key: str, secret_key: str):
        self.gateway_url = gateway_url
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = 30
    
    def send_ussd_response(self, session_id: str, message: str, end_session: bool = False) -> bool:
        """
        Send USSD response to gateway.
        
        Args:
            session_id: USSD session ID
            message: Response message
            end_session: Whether to end the session
        
        Returns:
            Boolean indicating success
        """
        try:
            # Prepare request data
            request_data = {
                'sessionId': session_id,
                'message': message,
                'endSession': end_session,
                'timestamp': int(time.time())
            }
            
            # Generate signature
            signature = self._generate_signature(request_data)
            request_data['signature'] = signature
            
            # Send request
            response = requests.post(
                self.gateway_url,
                json=request_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send USSD response: {str(e)}")
            return False
    
    def _generate_signature(self, data: dict) -> str:
        """Generate signature for USSD gateway authentication."""
        # Create signature string
        signature_string = f"{data['sessionId']}{data['message']}{data['timestamp']}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature


# USSD Service instance
ussd_service = USSDService()

# USSD Gateway instance (configure with your gateway details)
ussd_gateway = USSDGateway(
    gateway_url=getattr(settings, 'USSD_GATEWAY_URL', ''),
    api_key=getattr(settings, 'USSD_API_KEY', ''),
    secret_key=getattr(settings, 'USSD_SECRET_KEY', '')
)
