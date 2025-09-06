#!/usr/bin/env python3
"""
Example script demonstrating how to use the User Profile API endpoints.

This script shows how to interact with the user profile API using the requests library.
Make sure to install requests: pip install requests
"""

import requests
import json
from typing import Dict, Any


class UserProfileAPIClient:
    """Client for interacting with the User Profile API."""
    
    def __init__(self, base_url: str, token: str = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API (e.g., 'https://your-domain.com/api')
            token: JWT authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate and get JWT token.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Authentication response with token
        """
        response = self.session.post(
            f'{self.base_url}/auth/jwt/create',
            json={
                'username': username,
                'password': password
            }
        )
        response.raise_for_status()
        
        auth_data = response.json()
        self.token = auth_data['access']
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })
        
        return auth_data
    
    def get_profile(self) -> Dict[str, Any]:
        """Get current user's profile."""
        response = self.session.get(f'{self.base_url}/user-profile/')
        response.raise_for_status()
        return response.json()
    
    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            data: Profile data to update
        """
        response = self.session.patch(
            f'{self.base_url}/user-profile/update/',
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def update_basic_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update basic user information.
        
        Args:
            data: Basic info data (first_name, last_name, email)
        """
        response = self.session.patch(
            f'{self.base_url}/user-profile/basic-info/',
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password.
        
        Args:
            current_password: Current password
            new_password: New password
        """
        response = self.session.post(
            f'{self.base_url}/user-profile/change-password/',
            json={
                'current_password': current_password,
                'new_password': new_password,
                'confirm_password': new_password
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """Get profile statistics."""
        response = self.session.get(f'{self.base_url}/user-profile/stats/')
        response.raise_for_status()
        return response.json()
    
    def get_groups(self) -> list:
        """Get available user groups."""
        response = self.session.get(f'{self.base_url}/user-groups/')
        response.raise_for_status()
        return response.json()
    
    def get_roles(self) -> list:
        """Get available user roles."""
        response = self.session.get(f'{self.base_url}/user-roles/')
        response.raise_for_status()
        return response.json()
    
    def join_group(self, group_id: int, role_id: int = None) -> Dict[str, Any]:
        """
        Join a user group.
        
        Args:
            group_id: ID of the group to join
            role_id: ID of the role (optional, will use default if not provided)
        """
        data = {'group_id': group_id}
        if role_id:
            data['role_id'] = role_id
            
        response = self.session.post(
            f'{self.base_url}/user-profile/join-group/',
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def leave_group(self, group_id: int) -> Dict[str, Any]:
        """
        Leave a user group.
        
        Args:
            group_id: ID of the group to leave
        """
        response = self.session.post(
            f'{self.base_url}/user-profile/leave-group/',
            json={'group_id': group_id}
        )
        response.raise_for_status()
        return response.json()
    
    def get_group_memberships(self) -> list:
        """Get user's group memberships."""
        response = self.session.get(f'{self.base_url}/user-profile/group-memberships/')
        response.raise_for_status()
        return response.json()
    
    def upload_avatar(self, image_file) -> dict:
        """
        Upload a new avatar.
        
        Args:
            image_file: File object or path to image file
        """
        files = {'image': image_file}
        response = self.session.post(
            f'{self.base_url}/user-profile/avatar/upload/',
            files=files
        )
        response.raise_for_status()
        return response.json()
    
    def delete_avatar(self) -> dict:
        """Delete current avatar."""
        response = self.session.delete(f'{self.base_url}/user-profile/avatar/delete/')
        response.raise_for_status()
        return response.json()
    
    def get_avatar_info(self) -> dict:
        """Get avatar information."""
        response = self.session.get(f'{self.base_url}/user-profile/avatar/info/')
        response.raise_for_status()
        return response.json()
    
    def set_avatar_from_existing(self, image_id: int) -> dict:
        """
        Set avatar from existing image.
        
        Args:
            image_id: ID of existing image
        """
        response = self.session.post(
            f'{self.base_url}/user-profile/avatar/set-existing/',
            json={'image_id': image_id}
        )
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the User Profile API client."""
    
    # Configuration
    BASE_URL = 'http://localhost:8001/api'  # Adjust to your server URL
    USERNAME = 'admin'  # Adjust to your username
    PASSWORD = 'admin123'  # Adjust to your password
    
    # Initialize client
    client = UserProfileAPIClient(BASE_URL)
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        auth_data = client.authenticate(USERNAME, PASSWORD)
        print(f"✅ Authentication successful! Token: {auth_data['access'][:20]}...")
        
        # Get current profile
        print("\n👤 Getting user profile...")
        profile = client.get_profile()
        print(f"✅ Profile retrieved for: {profile['username']} ({profile['email']})")
        print(f"   Name: {profile['first_name']} {profile['last_name']}")
        print(f"   Phone: {profile.get('phone', 'Not set')}")
        print(f"   City: {profile.get('city', 'Not set')}")
        
        # Get profile statistics
        print("\n📊 Getting profile statistics...")
        stats = client.get_profile_stats()
        print(f"✅ Profile completion: {stats['profile_completion_percentage']}%")
        print(f"   Completed fields: {stats['completed_fields']}/{stats['total_fields']}")
        print(f"   Group memberships: {stats['group_memberships_count']}")
        
        # Update profile
        print("\n✏️  Updating profile...")
        update_data = {
            'phone': '+1234567890',
            'city': 'Example City',
            'address': '123 Example Street',
            'preferred_language': 'en'
        }
        updated_profile = client.update_profile(update_data)
        print("✅ Profile updated successfully!")
        
        # Get available groups
        print("\n👥 Getting available groups...")
        groups = client.get_groups()
        print(f"✅ Found {len(groups)} groups:")
        for group in groups:
            print(f"   - {group['name']}: {group['description']}")
        
        # Get available roles
        print("\n🎭 Getting available roles...")
        roles = client.get_roles()
        print(f"✅ Found {len(roles)} roles:")
        for role in roles:
            print(f"   - {role['name']}: {role['description']}")
        
        # Join a group (if groups exist)
        if groups:
            group_id = groups[0]['id']
            role_id = roles[0]['id'] if roles else None
            
            print(f"\n🤝 Joining group '{groups[0]['name']}'...")
            membership = client.join_group(group_id, role_id)
            print(f"✅ Successfully joined group! Membership ID: {membership['id']}")
        
        # Get group memberships
        print("\n📋 Getting group memberships...")
        memberships = client.get_group_memberships()
        print(f"✅ Current memberships: {len(memberships)}")
        for membership in memberships:
            print(f"   - {membership['group']['name']} ({membership['role']['name']})")
        
        # Avatar management
        print("\n🖼️  Avatar management...")
        
        # Get current avatar info
        avatar_info = client.get_avatar_info()
        if avatar_info['has_avatar']:
            print(f"✅ Current avatar: {avatar_info['avatar']['title']}")
            print(f"   URLs: {avatar_info['avatar']['urls']}")
        else:
            print("ℹ️  No avatar currently set")
        
        # Note: Actual avatar upload would require a real image file
        print("ℹ️  Avatar upload requires a real image file (skipping in example)")
        
        print("\n🎉 Example completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == '__main__':
    main()
