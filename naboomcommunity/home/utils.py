import re
from typing import List, Dict, Any
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
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
    This function should be called during initial setup.
    """
    # Create default roles
    roles = {
        'Member': {
            'description': _('Basic member permissions and access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True
            }
        },
        'Elder': {
            'description': _('Elder-level permissions and leadership access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_members': True,
                'can_edit_content': True
            }
        },
        'Deacon': {
            'description': _('Deacon-level permissions and service access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_services': True,
                'can_edit_content': True
            }
        },
        'Youth Leader': {
            'description': _('Youth leader permissions and ministry access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_youth': True,
                'can_edit_content': True
            }
        },
        'Worship Leader': {
            'description': _('Worship team permissions and music access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_worship': True,
                'can_edit_content': True
            }
        },
        'Sunday School Teacher': {
            'description': _('Sunday school teacher permissions and education access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_education': True,
                'can_edit_content': True
            }
        },
        'Community Outreach': {
            'description': _('Community outreach permissions and service access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_outreach': True,
                'can_edit_content': True
            }
        },
        'Technical Support': {
            'description': _('Technical support permissions and system access'),
            'permissions': {
                'can_view_community': True,
                'can_edit_profile': True,
                'can_view_members': True,
                'can_manage_system': True,
                'can_edit_content': True
            }
        }
    }
    
    # Create default groups
    groups = {
        'Member': {
            'description': _('Default group for all registered community members'),
            'default_role': 'Member'
        },
        'Elders': {
            'description': _('Church elders and spiritual leaders'),
            'default_role': 'Elder'
        },
        'Deacons': {
            'description': _('Church deacons and service leaders'),
            'default_role': 'Deacon'
        },
        'Youth Leaders': {
            'description': _('Youth ministry leaders and coordinators'),
            'default_role': 'Youth Leader'
        },
        'Worship Team': {
            'description': _('Music and worship ministry team'),
            'default_role': 'Worship Leader'
        },
        'Sunday School Teachers': {
            'description': _('Sunday school and children\'s ministry teachers'),
            'default_role': 'Sunday School Teacher'
        },
        'Community Outreach': {
            'description': _('Community service and outreach coordinators'),
            'default_role': 'Community Outreach'
        },
        'Technical Support': {
            'description': _('Technical and IT support team'),
            'default_role': 'Technical Support'
        }
    }
    
    created_roles = {}
    created_groups = {}
    
    # Create roles first
    for role_name, role_data in roles.items():
        role, created = UserRole.objects.get_or_create(
            name=role_name,
            defaults={
                'description': role_data['description'],
                'permissions': role_data['permissions'],
                'is_active': True
            }
        )
        created_roles[role_name] = role
        if created:
            print(f"Created role: {role_name}")
    
    # Create groups
    for group_name, group_data in groups.items():
        group, created = UserGroup.objects.get_or_create(
            name=group_name,
            defaults={
                'description': group_data['description'],
                'is_active': True
            }
        )
        created_groups[group_name] = group
        if created:
            print(f"Created group: {group_name}")
    
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
        # Get or create the Member group
        member_group, created = UserGroup.objects.get_or_create(
            name='Member',
            defaults={
                'description': _('Default group for all registered community members'),
                'is_active': True
            }
        )
        
        # Get or create the Member role
        member_role, created = UserRole.objects.get_or_create(
            name='Member',
            defaults={
                'description': _('Basic member permissions and access'),
                'permissions': {
                    'can_view_community': True,
                    'can_edit_profile': True,
                    'can_view_members': True
                },
                'is_active': True
            }
        )
        
        # Create the membership
        membership, created = UserGroupMembership.objects.get_or_create(
            user=user,
            group=member_group,
            defaults={
                'role': member_role,
                'is_active': True,
                'notes': _('Automatically assigned during registration')
            }
        )
        
        if created:
            print(f"Assigned user {user.username} to Member group with Member role")
        else:
            print(f"User {user.username} already has membership in Member group")
        
        return membership
        
    except Exception as e:
        print(f"Error assigning user {user.username} to default group: {e}")
        return None


def assign_existing_users_to_member_group():
    """
    Assign all existing users to the Member group if they don't already have a membership.
    This is useful for migrating existing users to the new system.
    """
    try:
        # Get or create the Member group and role
        member_group, created = UserGroup.objects.get_or_create(
            name='Member',
            defaults={
                'description': _('Default group for all registered community members'),
                'is_active': True
            }
        )
        
        member_role, created = UserRole.objects.get_or_create(
            name='Member',
            defaults={
                'description': _('Basic member permissions and access'),
                'permissions': {
                    'can_view_community': True,
                    'can_edit_profile': True,
                    'can_view_members': True
                },
                'is_active': True
            }
        )
        
        # Get all users who don't have a membership in the Member group
        users_without_membership = User.objects.filter(
            ~models.Q(group_memberships__group=member_group)
        )
        
        assigned_count = 0
        for user in users_without_membership:
            membership, created = UserGroupMembership.objects.get_or_create(
                user=user,
                group=member_group,
                defaults={
                    'role': member_role,
                    'is_active': True,
                    'notes': _('Automatically assigned during migration')
                }
            )
            if created:
                assigned_count += 1
        
        print(f"Assigned {assigned_count} existing users to Member group")
        return assigned_count
        
    except Exception as e:
        print(f"Error assigning existing users to Member group: {e}")
        return 0


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

