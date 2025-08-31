import re
from typing import List, Dict, Any
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import UserProfile, UserGroup, UserRole, UserGroupMembership


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    Accepts various formats: +27 12 345 6789, 012 345 6789, etc.
    """
    if not phone:
        return True
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it starts with + (international) or is a local number
    if cleaned.startswith('+'):
        # International format: +27 12 345 6789
        if len(cleaned) >= 10 and len(cleaned) <= 15:
            return True
    else:
        # Local format: 012 345 6789
        if len(cleaned) >= 9 and len(cleaned) <= 10:
            return True
    
    return False


def validate_postal_code(postal_code: str) -> bool:
    """
    Validate South African postal code format.
    Format: 4 digits (e.g., 0001)
    """
    if not postal_code:
        return True
    
    # Remove spaces and check if it's exactly 4 digits
    cleaned = postal_code.replace(' ', '')
    return len(cleaned) == 4 and cleaned.isdigit()


def get_user_statistics() -> Dict[str, Any]:
    """
    Get comprehensive user statistics for the community.
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Get users with profiles
    users_with_profiles = UserProfile.objects.filter(user__is_active=True).count()
    users_with_medical_info = UserProfile.objects.filter(
        user__is_active=True
    ).exclude(
        allergies='',
        medical_conditions='',
        current_medications=''
    ).count()
    
    users_with_emergency_contact = UserProfile.objects.filter(
        user__is_active=True
    ).exclude(
        emergency_contact_name='',
        emergency_contact_phone=''
    ).count()
    
    # Language distribution
    language_stats = {}
    for profile in UserProfile.objects.filter(user__is_active=True):
        lang = profile.preferred_language
        language_stats[lang] = language_stats.get(lang, 0) + 1
    
    # City distribution
    city_stats = {}
    for profile in UserProfile.objects.filter(user__is_active=True).exclude(city=''):
        city = profile.city
        if city:
            city_stats[city] = city_stats.get(city, 0) + 1
    
    # Group membership stats
    group_stats = {}
    for group in UserGroup.objects.filter(is_active=True):
        member_count = group.members.filter(is_active=True).count()
        group_stats[group.name] = member_count
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'users_with_profiles': users_with_profiles,
        'users_with_medical_info': users_with_medical_info,
        'users_with_emergency_contact': users_with_emergency_contact,
        'language_distribution': language_stats,
        'city_distribution': city_stats,
        'group_membership': group_stats,
        'completion_rate': {
            'profiles': round((users_with_profiles / active_users * 100), 2) if active_users > 0 else 0,
            'medical_info': round((users_with_medical_info / active_users * 100), 2) if active_users > 0 else 0,
            'emergency_contact': round((users_with_emergency_contact / active_users * 100), 2) if active_users > 0 else 0,
        }
    }


def create_default_groups_and_roles():
    """
    Create default user groups and roles for the community.
    This should be called during initial setup.
    """
    # Create default roles
    roles = {
        'Leader': {
            'description': 'Group leader with full administrative privileges',
            'permissions': {
                'can_edit_group': True,
                'can_add_members': True,
                'can_remove_members': True,
                'can_assign_roles': True,
                'can_view_all_members': True
            }
        },
        'Moderator': {
            'description': 'Group moderator with limited administrative privileges',
            'permissions': {
                'can_edit_group': False,
                'can_add_members': True,
                'can_remove_members': False,
                'can_assign_roles': False,
                'can_view_all_members': True
            }
        },
        'Member': {
            'description': 'Regular group member with basic privileges',
            'permissions': {
                'can_edit_group': False,
                'can_add_members': False,
                'can_remove_members': False,
                'can_assign_roles': False,
                'can_view_all_members': False
            }
        }
    }
    
    created_roles = {}
    for role_name, role_data in roles.items():
        role, created = UserRole.objects.get_or_create(
            name=role_name,
            defaults={
                'description': role_data['description'],
                'permissions': role_data['permissions']
            }
        )
        created_roles[role_name] = role
    
    # Create default groups
    groups = {
        'Member': {
            'description': 'Default group for all registered community members',
            'default_role': 'Member'
        },
        'Elders': {
            'description': 'Senior community members and spiritual leaders',
            'default_role': 'Leader'
        },
        'Youth': {
            'description': 'Young community members',
            'default_role': 'Member'
        },
        'Choir': {
            'description': 'Music ministry and worship team',
            'default_role': 'Member'
        },
        'Tech Support': {
            'description': 'Technical assistance and digital literacy support',
            'default_role': 'Moderator'
        },
        'Prayer Team': {
            'description': 'Intercessory prayer and spiritual support',
            'default_role': 'Member'
        },
        'Outreach': {
            'description': 'Community outreach and evangelism',
            'default_role': 'Moderator'
        }
    }
    
    created_groups = {}
    for group_name, group_data in groups.items():
        group, created = UserGroup.objects.get_or_create(
            name=group_name,
            defaults={'description': group_data['description']}
        )
        created_groups[group_name] = group
    
    return {
        'roles': created_roles,
        'groups': created_groups
    }


def assign_user_to_default_group(user: User):
    """
    Automatically assign a new user to the default Member group with Member role.
    This should be called after a user profile is created.
    """
    try:
        # Get the Member group and Member role
        member_group = UserGroup.objects.get(name='Member', is_active=True)
        member_role = UserRole.objects.get(name='Member', is_active=True)
        
        # Check if user is already a member
        existing_membership = UserGroupMembership.objects.filter(
            user=user,
            group=member_group,
            is_active=True
        ).first()
        
        if not existing_membership:
            # Create the membership
            UserGroupMembership.objects.create(
                user=user,
                group=member_group,
                role=member_role,
                is_active=True,
                notes='Automatically assigned as default community member'
            )
            return True
        return False
    except (UserGroup.DoesNotExist, UserRole.DoesNotExist):
        # If default groups/roles don't exist, create them first
        create_default_groups_and_roles()
        # Try again
        return assign_user_to_default_group(user)


def assign_existing_users_to_member_group():
    """
    Assign all existing users to the Member group if they don't already have a membership.
    This is useful for migrating existing users to the new system.
    """
    try:
        # Get the Member group and Member role
        member_group = UserGroup.objects.get(name='Member', is_active=True)
        member_role = UserRole.objects.get(name='Member', is_active=True)
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        assigned_count = 0
        
        for user in users:
            # Check if user already has a membership in any group
            existing_membership = UserGroupMembership.objects.filter(
                user=user,
                is_active=True
            ).first()
            
            if not existing_membership:
                # Create the membership
                UserGroupMembership.objects.create(
                    user=user,
                    group=member_group,
                    role=member_role,
                    is_active=True,
                    notes='Automatically assigned existing user to Member group'
                )
                assigned_count += 1
        
        return assigned_count
    except (UserGroup.DoesNotExist, UserRole.DoesNotExist):
        # If default groups/roles don't exist, create them first
        create_default_groups_and_roles()
        # Try again
        return assign_existing_users_to_member_group()


def export_user_data(user: User, format: str = 'json') -> Dict[str, Any]:
    """
    Export user data in a structured format.
    Useful for data portability and GDPR compliance.
    """
    profile = getattr(user, 'profile', None)
    
    user_data = {
        'personal_info': {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        },
        'preferences': {},
        'medical_info': {},
        'emergency_contact': {},
        'memberships': [
            {
                'group': membership.group.name,
                'role': membership.role.name,
                'joined_at': membership.joined_at.isoformat(),
                'is_active': membership.is_active,
                'notes': membership.notes,
            }
            for membership in user.group_memberships.filter(is_active=True)
        ],
        'metadata': {
            'created_at': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
    }
    
    # Add profile data if it exists
    if profile:
        user_data['personal_info'].update({
            'phone': profile.phone,
            'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            'gender': profile.gender,
            'address': profile.address,
            'city': profile.city,
            'province': profile.province,
            'postal_code': profile.postal_code,
        })
        
        user_data['preferences'] = {
            'preferred_language': profile.preferred_language,
            'timezone': profile.timezone,
            'email_notifications': profile.email_notifications,
            'sms_notifications': profile.sms_notifications,
            'mfa_enabled': profile.mfa_enabled,
        }
        
        user_data['medical_info'] = {
            'allergies': profile.allergies,
            'medical_conditions': profile.medical_conditions,
            'current_medications': profile.current_medications,
        }
        
        user_data['emergency_contact'] = {
            'name': profile.emergency_contact_name,
            'phone': profile.emergency_contact_phone,
            'relationship': profile.emergency_contact_relationship,
        }
        
        user_data['metadata']['profile_created_at'] = profile.created_at.isoformat()
        user_data['metadata']['profile_updated_at'] = profile.updated_at.isoformat()
    
    return user_data


def anonymize_user_data(user: User) -> Dict[str, Any]:
    """
    Anonymize user data for privacy protection.
    Useful for data retention while maintaining privacy.
    """
    # Generate a unique anonymous identifier
    import hashlib
    anonymous_id = hashlib.sha256(f"{user.username}{user.email}".encode()).hexdigest()[:8]
    
    profile = getattr(user, 'profile', None)
    
    anonymous_data = {
        'anonymous_id': anonymous_id,
        'memberships': [
            {
                'group': membership.group.name,
                'role': membership.role.name,
                'joined_at': membership.joined_at.isoformat(),
            }
            for membership in user.group_memberships.filter(is_active=True)
        ],
        'metadata': {
            'created_at': user.date_joined.isoformat(),
        }
    }
    
    # Add profile preferences if they exist
    if profile:
        anonymous_data['preferences'] = {
            'preferred_language': profile.preferred_language,
            'timezone': profile.timezone,
        }
        anonymous_data['metadata']['profile_created_at'] = profile.created_at.isoformat()
    
    return anonymous_data

