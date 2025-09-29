# services/push_service.py
from pywebpush import webpush, WebPushException
from django.conf import settings
import json
from typing import Dict, List, Optional, Any
from .base_service import BaseService

class PushNotificationService(BaseService):
    """
    Shared push notification service for panic and communityhub apps.
    Handles VAPID-based web push notifications across the entire project.
    """
    
    def __init__(self):
        super().__init__()
        self.vapid_private_key_file = settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY_FILE']
        self.vapid_claims = {
            "sub": f"mailto:{settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL']}"
        }

    def send_notification(self, subscription_info: Dict, message_body: Dict) -> bool:
        """
        Send a push notification to a single subscriber.
        
        Args:
            subscription_info: Push subscription data from frontend
            message_body: Notification payload
            
        Returns:
            bool: Success status
        """
        try:
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(message_body),
                vapid_private_key=self.vapid_private_key_file,
                vapid_claims=self.vapid_claims
            )
            self.log_info(f"Push notification sent successfully: {response.status_code}")
            return True
        except WebPushException as ex:
            self.log_error(f"WebPush failed: {repr(ex)}")
            return False

    def send_bulk_notifications(self, subscriptions: List[Dict], message_body: Dict) -> Dict[str, Any]:
        """
        Send push notifications to multiple subscribers.
        
        Args:
            subscriptions: List of subscription data
            message_body: Notification payload
            
        Returns:
            dict: Results with success/failure counts
        """
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for subscription in subscriptions:
            success = self.send_notification(subscription, message_body)
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(
                    f"Failed for subscription: {subscription.get('endpoint', 'unknown')}"
                )
        
        self.log_info(f"Bulk notification complete: {results['success']} sent, {results['failed']} failed")
        return results

    def create_panic_notification(self, location: str, severity: str, user_name: str) -> Dict[str, Any]:
        """
        Create a panic alert notification payload.
        Specific to panic app requirements.
        
        Args:
            location: Location of the panic alert
            severity: Alert severity level
            user_name: Name of user who triggered panic
            
        Returns:
            dict: Formatted panic notification payload
        """
        return {
            "title": f"🚨 PANIC ALERT - {severity.upper()}",
            "body": f"{user_name} triggered a panic alert at {location}",
            "icon": "/static/icons/panic-alert.png",
            "badge": "/static/icons/panic-badge.png",
            "tag": "panic-alert",
            "requireInteraction": True,
            "actions": [
                {
                    "action": "respond",
                    "title": "Respond"
                },
                {
                    "action": "view",
                    "title": "View Details"
                }
            ],
            "data": {
                "type": "panic",
                "severity": severity,
                "location": location,
                "timestamp": json.dumps({}, default=str),
                "url": "/panic/alerts/"
            },
            "vibrate": [200, 100, 200, 100, 200, 100, 200]
        }

    def create_community_notification(self, title: str, message: str, category: str, 
                                    action_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a community hub notification payload.
        Specific to communityhub app requirements.
        
        Args:
            title: Notification title
            message: Notification message
            category: Community category (news, events, safety, etc.)
            action_url: Optional URL for click action
            
        Returns:
            dict: Formatted community notification payload
        """
        category_icons = {
            'news': '/static/icons/news.png',
            'events': '/static/icons/events.png',
            'safety': '/static/icons/safety.png',
            'general': '/static/icons/community.png'
        }
        
        return {
            "title": f"📢 {title}",
            "body": message,
            "icon": category_icons.get(category, category_icons['general']),
            "badge": "/static/icons/community-badge.png",
            "tag": f"community-{category}",
            "requireInteraction": False,
            "actions": [
                {
                    "action": "view",
                    "title": "View"
                }
            ],
            "data": {
                "type": "community",
                "category": category,
                "url": action_url or "/communityhub/"
            }
        }

    def create_general_notification(self, title: str, body: str, icon: Optional[str] = None,
                                  url: Optional[str] = None, actions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Create a general notification payload for any app.
        
        Args:
            title: Notification title
            body: Notification message
            icon: Optional icon URL
            url: Optional click action URL
            actions: Optional action buttons
            
        Returns:
            dict: Formatted general notification payload
        """
        payload = {
            "title": title,
            "body": body,
            "icon": icon or "/static/icons/default-notification.png",
            "badge": "/static/icons/default-badge.png",
            "tag": "general-notification",
            "requireInteraction": False
        }
        
        if url:
            payload["data"] = {"url": url}
            
        if actions:
            payload["actions"] = actions
            
        return payload
