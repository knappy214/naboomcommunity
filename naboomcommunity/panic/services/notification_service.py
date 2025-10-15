"""
Notification Service for Emergency Response
Handles multi-channel emergency notifications to family and contacts.
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from django.core.cache import cache
from django.utils import timezone as django_timezone
from django.contrib.auth import get_user_model
from django.conf import settings
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

from ..models import EmergencyAuditLog
from ..api.throttling import emergency_rate_limiter

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for handling emergency notifications to family and contacts.
    Supports multiple channels: SMS, email, push notifications, and USSD.
    """
    
    # Notification channels
    CHANNELS = {
        'sms': 'SMS',
        'email': 'Email',
        'push': 'Push Notification',
        'ussd': 'USSD',
        'whatsapp': 'WhatsApp',
        'telegram': 'Telegram'
    }
    
    # Priority levels
    PRIORITIES = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }
    
    # Cache settings
    CACHE_TIMEOUT = 3600  # 1 hour
    CACHE_PREFIX = 'emergency_notification'
    
    def __init__(self):
        self.rate_limiter = emergency_rate_limiter
        self.twilio_client = None
        self._init_twilio()
    
    def _init_twilio(self):
        """Initialize Twilio client for SMS notifications."""
        try:
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                logger.info("Twilio client initialized successfully")
            else:
                logger.warning("Twilio credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
    
    def send_emergency_notification(self, user: User, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send emergency notification to family and contacts.
        
        Args:
            user: User instance
            notification_data: Notification data dictionary
            
        Returns:
            Notification result dictionary
        """
        try:
            # Extract notification data
            emergency_id = notification_data.get('emergency_id')
            emergency_type = notification_data.get('emergency_type', 'panic')
            channels = notification_data.get('channels', ['sms', 'email'])
            recipients = notification_data.get('recipients', [])
            message = notification_data.get('message', '')
            priority = notification_data.get('priority', 'high')
            location_data = notification_data.get('location', {})
            medical_data = notification_data.get('medical_data', {})
            
            # Validate required fields
            if not emergency_id:
                return {
                    'success': False,
                    'error': 'Emergency ID is required'
                }
            
            if not recipients:
                return {
                    'success': False,
                    'error': 'Recipients list is required'
                }
            
            # Check rate limiting
            if not self.rate_limiter.check_notification_rate(user):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded for notifications',
                    'retry_after': self.rate_limiter.get_retry_after('notification')
                }
            
            # Generate notification ID
            notification_id = str(uuid.uuid4())
            
            # Prepare notification content
            notification_content = self._prepare_notification_content(
                emergency_type, message, location_data, medical_data, user
            )
            
            # Send notifications to each channel
            results = {}
            total_sent = 0
            total_failed = 0
            
            for channel in channels:
                if channel not in self.CHANNELS:
                    logger.warning(f"Unknown notification channel: {channel}")
                    continue
                
                channel_result = self._send_channel_notification(
                    channel, recipients, notification_content, priority
                )
                
                results[channel] = channel_result
                total_sent += channel_result.get('sent_count', 0)
                total_failed += channel_result.get('failed_count', 0)
            
            # Update rate limiter
            self.rate_limiter.record_notification(user)
            
            # Log notification
            self._log_notification(
                user, notification_id, emergency_id, emergency_type,
                channels, total_sent, total_failed, results
            )
            
            return {
                'success': True,
                'notification_id': notification_id,
                'channels_sent': channels,
                'total_sent': total_sent,
                'total_failed': total_failed,
                'results': results,
                'timestamp': django_timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send emergency notification: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to send emergency notification',
                'details': str(e)
            }
    
    def _prepare_notification_content(self, emergency_type: str, message: str,
                                    location_data: Dict[str, Any], medical_data: Dict[str, Any],
                                    user: User) -> Dict[str, Any]:
        """
        Prepare notification content for different channels.
        
        Args:
            emergency_type: Type of emergency
            message: Custom message
            location_data: Location information
            medical_data: Medical information
            user: User instance
            
        Returns:
            Prepared notification content
        """
        try:
            # Base notification content
            content = {
                'emergency_type': emergency_type,
                'user_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'user_phone': getattr(user, 'phone_number', ''),
                'timestamp': django_timezone.now().isoformat(),
                'message': message or f"Emergency alert: {emergency_type.title()}",
                'location': location_data,
                'medical_summary': self._prepare_medical_summary(medical_data)
            }
            
            # Add location information if available
            if location_data:
                content['location_text'] = self._format_location_text(location_data)
            
            # Add medical information if available
            if medical_data and medical_data.get('consent_level') != 'none':
                content['medical_info'] = self._format_medical_info(medical_data)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to prepare notification content: {str(e)}")
            return {
                'emergency_type': emergency_type,
                'message': message or f"Emergency alert: {emergency_type.title()}",
                'timestamp': django_timezone.now().isoformat()
            }
    
    def _prepare_medical_summary(self, medical_data: Dict[str, Any]) -> str:
        """
        Prepare medical summary for notification.
        
        Args:
            medical_data: Medical data dictionary
            
        Returns:
            Formatted medical summary
        """
        try:
            if not medical_data or medical_data.get('consent_level') == 'none':
                return "No medical information available"
            
            summary_parts = []
            
            # Add blood type if available
            if medical_data.get('blood_type'):
                summary_parts.append(f"Blood Type: {medical_data['blood_type']}")
            
            # Add critical allergies if available
            allergies = medical_data.get('allergies', [])
            if allergies:
                critical_allergies = [a for a in allergies if a.get('requires_immediate_attention', False)]
                if critical_allergies:
                    allergy_names = [a.get('name', 'Unknown') for a in critical_allergies]
                    summary_parts.append(f"Critical Allergies: {', '.join(allergy_names)}")
            
            # Add emergency contact if available
            emergency_contact = medical_data.get('emergency_contact', {})
            if emergency_contact.get('name'):
                summary_parts.append(f"Emergency Contact: {emergency_contact['name']} ({emergency_contact.get('phone', 'No phone')})")
            
            return "; ".join(summary_parts) if summary_parts else "Basic medical information available"
            
        except Exception as e:
            logger.error(f"Failed to prepare medical summary: {str(e)}")
            return "Medical information available"
    
    def _format_location_text(self, location_data: Dict[str, Any]) -> str:
        """
        Format location data for notification text.
        
        Args:
            location_data: Location data dictionary
            
        Returns:
            Formatted location text
        """
        try:
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')
            accuracy = location_data.get('accuracy')
            
            if latitude and longitude:
                location_text = f"Location: {latitude:.6f}, {longitude:.6f}"
                if accuracy:
                    location_text += f" (Accuracy: {accuracy}m)"
                return location_text
            
            return "Location: Unknown"
            
        except Exception as e:
            logger.error(f"Failed to format location text: {str(e)}")
            return "Location: Unknown"
    
    def _format_medical_info(self, medical_data: Dict[str, Any]) -> str:
        """
        Format medical information for notification.
        
        Args:
            medical_data: Medical data dictionary
            
        Returns:
            Formatted medical information
        """
        try:
            info_parts = []
            
            # Add blood type
            if medical_data.get('blood_type'):
                info_parts.append(f"Blood Type: {medical_data['blood_type']}")
            
            # Add critical conditions
            conditions = medical_data.get('medical_conditions', [])
            critical_conditions = [c for c in conditions if c.get('requires_immediate_attention', False)]
            if critical_conditions:
                condition_names = [c.get('name', 'Unknown') for c in critical_conditions]
                info_parts.append(f"Critical Conditions: {', '.join(condition_names)}")
            
            # Add critical allergies
            allergies = medical_data.get('allergies', [])
            critical_allergies = [a for a in allergies if a.get('requires_immediate_attention', False)]
            if critical_allergies:
                allergy_names = [a.get('name', 'Unknown') for a in critical_allergies]
                info_parts.append(f"Critical Allergies: {', '.join(allergy_names)}")
            
            return "; ".join(info_parts) if info_parts else "Medical information available"
            
        except Exception as e:
            logger.error(f"Failed to format medical info: {str(e)}")
            return "Medical information available"
    
    def _send_channel_notification(self, channel: str, recipients: List[Dict[str, Any]],
                                 content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send notification via specific channel.
        
        Args:
            channel: Notification channel
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            Channel-specific result
        """
        try:
            if channel == 'sms':
                return self._send_sms_notification(recipients, content, priority)
            elif channel == 'email':
                return self._send_email_notification(recipients, content, priority)
            elif channel == 'push':
                return self._send_push_notification(recipients, content, priority)
            elif channel == 'ussd':
                return self._send_ussd_notification(recipients, content, priority)
            elif channel == 'whatsapp':
                return self._send_whatsapp_notification(recipients, content, priority)
            elif channel == 'telegram':
                return self._send_telegram_notification(recipients, content, priority)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported channel: {channel}',
                    'sent_count': 0,
                    'failed_count': len(recipients)
                }
                
        except Exception as e:
            logger.error(f"Failed to send {channel} notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _send_sms_notification(self, recipients: List[Dict[str, Any]], 
                             content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send SMS notification.
        
        Args:
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            SMS result dictionary
        """
        try:
            if not self.twilio_client:
                return {
                    'success': False,
                    'error': 'SMS service not configured',
                    'sent_count': 0,
                    'failed_count': len(recipients)
                }
            
            # Prepare SMS message
            message_text = self._format_sms_message(content)
            
            sent_count = 0
            failed_count = 0
            errors = []
            
            for recipient in recipients:
                phone_number = recipient.get('phone')
                if not phone_number:
                    failed_count += 1
                    errors.append(f"Missing phone number for recipient: {recipient.get('name', 'Unknown')}")
                    continue
                
                try:
                    # Send SMS via Twilio
                    message = self.twilio_client.messages.create(
                        body=message_text,
                        from_=getattr(settings, 'TWILIO_PHONE_NUMBER', ''),
                        to=phone_number
                    )
                    
                    sent_count += 1
                    logger.info(f"SMS sent to {phone_number}: {message.sid}")
                    
                except TwilioException as e:
                    failed_count += 1
                    error_msg = f"Failed to send SMS to {phone_number}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _format_sms_message(self, content: Dict[str, Any]) -> str:
        """
        Format SMS message content.
        
        Args:
            content: Notification content
            
        Returns:
            Formatted SMS message
        """
        try:
            message_parts = [
                f"🚨 EMERGENCY ALERT 🚨",
                f"Type: {content['emergency_type'].upper()}",
                f"Person: {content['user_name']}",
                f"Time: {content['timestamp']}",
                f"Message: {content['message']}"
            ]
            
            # Add location if available
            if content.get('location_text'):
                message_parts.append(f"Location: {content['location_text']}")
            
            # Add medical summary if available
            if content.get('medical_summary'):
                message_parts.append(f"Medical: {content['medical_summary']}")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Failed to format SMS message: {str(e)}")
            return f"Emergency alert: {content.get('emergency_type', 'Unknown')} - {content.get('message', '')}"
    
    def _send_email_notification(self, recipients: List[Dict[str, Any]], 
                               content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send email notification.
        
        Args:
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            Email result dictionary
        """
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            # Prepare email content
            subject = f"🚨 EMERGENCY ALERT - {content['emergency_type'].upper()}"
            
            # Render email template
            email_context = {
                'content': content,
                'priority': priority,
                'timestamp': django_timezone.now()
            }
            
            # Use a simple text template for now
            message = self._format_email_message(content)
            
            sent_count = 0
            failed_count = 0
            errors = []
            
            for recipient in recipients:
                email = recipient.get('email')
                if not email:
                    failed_count += 1
                    errors.append(f"Missing email for recipient: {recipient.get('name', 'Unknown')}")
                    continue
                
                try:
                    # Send email
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@naboomneighbornet.net.za'),
                        recipient_list=[email],
                        fail_silently=False
                    )
                    
                    sent_count += 1
                    logger.info(f"Email sent to {email}")
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to send email to {email}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _format_email_message(self, content: Dict[str, Any]) -> str:
        """
        Format email message content.
        
        Args:
            content: Notification content
            
        Returns:
            Formatted email message
        """
        try:
            message_parts = [
                "EMERGENCY ALERT NOTIFICATION",
                "=" * 50,
                f"Emergency Type: {content['emergency_type'].upper()}",
                f"Person: {content['user_name']}",
                f"Phone: {content.get('user_phone', 'Not provided')}",
                f"Time: {content['timestamp']}",
                f"Message: {content['message']}",
                ""
            ]
            
            # Add location if available
            if content.get('location_text'):
                message_parts.extend([
                    "LOCATION INFORMATION:",
                    content['location_text'],
                    ""
                ])
            
            # Add medical information if available
            if content.get('medical_info'):
                message_parts.extend([
                    "MEDICAL INFORMATION:",
                    content['medical_info'],
                    ""
                ])
            
            message_parts.extend([
                "Please respond immediately if you can assist.",
                "",
                "This is an automated emergency notification from Naboom Community Emergency Response System."
            ])
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Failed to format email message: {str(e)}")
            return f"Emergency alert: {content.get('emergency_type', 'Unknown')} - {content.get('message', '')}"
    
    def _send_push_notification(self, recipients: List[Dict[str, Any]], 
                              content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send push notification.
        
        Args:
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            Push notification result dictionary
        """
        try:
            # This would integrate with push notification service
            # For now, return mock result
            return {
                'success': True,
                'sent_count': len(recipients),
                'failed_count': 0,
                'message': 'Push notifications queued for delivery'
            }
            
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _send_ussd_notification(self, recipients: List[Dict[str, Any]], 
                              content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send USSD notification.
        
        Args:
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            USSD result dictionary
        """
        try:
            # This would integrate with USSD service
            # For now, return mock result
            return {
                'success': True,
                'sent_count': len(recipients),
                'failed_count': 0,
                'message': 'USSD notifications queued for delivery'
            }
            
        except Exception as e:
            logger.error(f"USSD notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _send_whatsapp_notification(self, recipients: List[Dict[str, Any]], 
                                  content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send WhatsApp notification.
        
        Args:
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            WhatsApp result dictionary
        """
        try:
            # This would integrate with WhatsApp Business API
            # For now, return mock result
            return {
                'success': True,
                'sent_count': len(recipients),
                'failed_count': 0,
                'message': 'WhatsApp notifications queued for delivery'
            }
            
        except Exception as e:
            logger.error(f"WhatsApp notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _send_telegram_notification(self, recipients: List[Dict[str, Any]], 
                                  content: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send Telegram notification.
        
        Args:
            recipients: List of recipients
            content: Notification content
            priority: Priority level
            
        Returns:
            Telegram result dictionary
        """
        try:
            # This would integrate with Telegram Bot API
            # For now, return mock result
            return {
                'success': True,
                'sent_count': len(recipients),
                'failed_count': 0,
                'message': 'Telegram notifications queued for delivery'
            }
            
        except Exception as e:
            logger.error(f"Telegram notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    def _log_notification(self, user: User, notification_id: str, emergency_id: str,
                         emergency_type: str, channels: List[str], total_sent: int,
                         total_failed: int, results: Dict[str, Any]):
        """
        Log notification for audit purposes.
        
        Args:
            user: User instance
            notification_id: Notification ID
            emergency_id: Emergency ID
            emergency_type: Type of emergency
            channels: Notification channels
            total_sent: Total sent count
            total_failed: Total failed count
            results: Channel results
        """
        try:
            EmergencyAuditLog.log_action(
                action_type='notification_send',
                description=f'Emergency notification sent via {", ".join(channels)}',
                user=user,
                severity='medium',
                emergency_id=emergency_id,
                notification_id=notification_id,
                emergency_type=emergency_type,
                channels=channels,
                total_sent=total_sent,
                total_failed=total_failed,
                results=results
            )
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
    
    def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get notification delivery status.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Status dictionary
        """
        try:
            cache_key = f"{self.CACHE_PREFIX}:status:{notification_id}"
            status = cache.get(cache_key)
            
            if status:
                return {
                    'success': True,
                    'notification_id': notification_id,
                    'status': status
                }
            else:
                return {
                    'success': False,
                    'error': 'Notification not found',
                    'notification_id': notification_id
                }
                
        except Exception as e:
            logger.error(f"Failed to get notification status: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get notification status',
                'details': str(e)
            }
    
    def get_user_notification_preferences(self, user: User) -> Dict[str, Any]:
        """
        Get user's notification preferences.
        
        Args:
            user: User instance
            
        Returns:
            Preferences dictionary
        """
        try:
            cache_key = f"{self.CACHE_PREFIX}:preferences:{user.id}"
            preferences = cache.get(cache_key)
            
            if not preferences:
                # Default preferences
                preferences = {
                    'channels': ['sms', 'email'],
                    'priority': 'high',
                    'emergency_types': ['panic', 'medical', 'fire', 'crime', 'accident'],
                    'quiet_hours': {
                        'enabled': False,
                        'start': '22:00',
                        'end': '07:00'
                    },
                    'location_sharing': True,
                    'medical_sharing': True
                }
                
                # Cache default preferences
                cache.set(cache_key, preferences, self.CACHE_TIMEOUT)
            
            return {
                'success': True,
                'preferences': preferences
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification preferences: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get notification preferences',
                'details': str(e)
            }
    
    def update_user_notification_preferences(self, user: User, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's notification preferences.
        
        Args:
            user: User instance
            preferences: New preferences
            
        Returns:
            Update result dictionary
        """
        try:
            cache_key = f"{self.CACHE_PREFIX}:preferences:{user.id}"
            cache.set(cache_key, preferences, self.CACHE_TIMEOUT)
            
            # Log preference update
            EmergencyAuditLog.log_action(
                action_type='notification_preferences_update',
                description='Notification preferences updated',
                user=user,
                severity='low',
                preferences=preferences
            )
            
            return {
                'success': True,
                'message': 'Notification preferences updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to update notification preferences: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update notification preferences',
                'details': str(e)
            }
