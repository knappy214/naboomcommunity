# Extended User Profile Model Implementation

## Overview

This document describes the implementation of a comprehensive user profile system for the Naboom Community Django application. The system extends Django's built-in User model with a related UserProfile model, avoiding circular dependencies while providing all the required functionality.

## Features

### 🔐 **Extended User Profile**
- **Personal Information**: Phone, date of birth, gender, address, city, province, postal code
- **Medical Information**: Allergies, medical conditions, current medications
- **Emergency Contacts**: Name, phone, relationship
- **Preferences**: Language (English/Afrikaans), timezone, notification settings, MFA

### 👥 **Community Management**
- **User Groups**: Organize members into categories (Elders, Youth, Choir, Tech Support, etc.)
- **User Roles**: Define permissions within groups (Leader, Moderator, Member)
- **Group Memberships**: Track user participation with timestamps and notes

### 🛡️ **Security & Privacy**
- **Multi-Factor Authentication**: Built-in MFA support
- **Data Export**: GDPR-compliant data portability
- **Data Anonymization**: Privacy protection for analytics
- **Automatic Profile Creation**: Profiles are automatically created when users are created

## Models

### UserProfile
A related model that extends Django's built-in User model with comprehensive profile fields.

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Profile fields
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Medical information
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
```

### UserGroup
Organizes community members into functional categories.

```python
class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### UserRole
Defines permissions and responsibilities within groups.

```python
class UserRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
```

### UserGroupMembership
Manages the many-to-many relationship between users, groups, and roles.

```python
class UserGroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
```

## Installation & Setup

### 1. **Run Migrations**
```bash
python manage.py migrate
```

### 2. **Setup Community Structure**
```bash
python manage.py setup_community
```

This command creates:
- Default user groups (Elders, Youth, Choir, Tech Support, Prayer Team, Outreach)
- Default user roles (Leader, Moderator, Member)

### 3. **Create Superuser**
```bash
python manage.py createsuperuser
```

## Usage

### Creating Users with Profiles

```python
from django.contrib.auth.models import User
from home.models import UserProfile

# Create a user (profile is automatically created)
user = User.objects.create_user(
    username='john_doe',
    email='john@example.com',
    password='secure_password',
    first_name='John',
    last_name='Doe'
)

# Access the profile
profile = user.profile
profile.phone = '+27 82 123 4567'
profile.city = 'Pretoria'
profile.preferred_language = 'en'
profile.save()
```

### Using the Custom User Creation Form

```python
from home.forms import CustomUserCreationForm

form_data = {
    'username': 'newuser',
    'email': 'newuser@example.com',
    'password1': 'newpass123',
    'password2': 'newpass123',
    'first_name': 'New',
    'last_name': 'User',
    'phone': '+27 12 345 6789',
    'city': 'Cape Town',
    'preferred_language': 'en'
}

form = CustomUserCreationForm(data=form_data)
if form.is_valid():
    user = form.save()  # This creates both User and UserProfile
```

### Managing Groups and Roles

```python
from home.models import UserGroup, UserRole, UserGroupMembership

# Create a group
youth_group = UserGroup.objects.create(
    name='Youth Ministry',
    description='Young adults and teenagers'
)

# Create a role
youth_leader = UserRole.objects.create(
    name='Youth Leader',
    description='Leads youth activities and mentoring',
    permissions={
        'can_organize_events': True,
        'can_mentor': True,
        'can_manage_finances': False
    }
)

# Add user to group with role
membership = UserGroupMembership.objects.create(
    user=user,
    group=youth_group,
    role=youth_leader
)
```

### Accessing Profile Data

```python
# Get user's profile
user = User.objects.get(username='john_doe')
profile = user.profile

# Access profile fields
print(f"Phone: {profile.phone}")
print(f"City: {profile.city}")
print(f"Language: {profile.preferred_language}")

# Get full address
full_address = profile.get_full_address()
print(f"Address: {full_address}")
```

### Utility Functions

```python
from home.utils import (
    validate_phone_number,
    validate_postal_code,
    get_user_statistics,
    export_user_data,
    anonymize_user_data
)

# Validate phone numbers
is_valid = validate_phone_number('+27 12 345 6789')  # True
is_valid = validate_phone_number('123')  # False

# Validate postal codes
is_valid = validate_postal_code('0001')  # True
is_valid = validate_postal_code('12345')  # False

# Get community statistics
stats = get_user_statistics()
print(f"Total users: {stats['total_users']}")
print(f"Active users: {stats['active_users']}")

# Export user data (GDPR compliance)
user_data = export_user_data(user)

# Anonymize user data for analytics
anonymous_data = anonymize_user_data(user)
```

## Forms

The application includes comprehensive forms for user management:

- **CustomUserCreationForm**: User registration with extended profile fields
- **UserProfileForm**: User self-service profile editing
- **MedicalInfoForm**: Medical information management
- **EmergencyContactForm**: Emergency contact management
- **UserGroupForm**: Group creation and editing
- **UserRoleForm**: Role creation and editing
- **UserGroupMembershipForm**: Membership management

## Admin Interface

The Django admin interface is fully configured with:

- **UserAdmin**: Extended user admin with inline UserProfile
- **UserProfileAdmin**: Dedicated profile management
- **UserGroupAdmin**: Group management with member counts
- **UserRoleAdmin**: Role management with permission validation
- **UserGroupMembershipAdmin**: Membership management with autocomplete

## Automatic Profile Creation

UserProfile objects are automatically created when User objects are created using Django signals:

```python
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)
```

This ensures that every user has a profile without manual intervention.

## Testing

Run the comprehensive test suite:

```bash
python manage.py test home
```

Tests cover:
- Model creation and validation
- Profile automatic creation
- Form validation
- Utility functions
- Admin interface access
- Data integrity constraints

## Security Considerations

### 🔒 **Data Protection**
- Medical information is stored securely with proper access controls
- Emergency contact data is protected and only accessible to authorized users
- Personal data can be exported and anonymized for compliance

### 🛡️ **Authentication**
- Uses Django's built-in authentication system
- Built-in MFA support for enhanced security
- Password validation follows Django best practices

### 📊 **Privacy**
- GDPR-compliant data export functionality
- Data anonymization for analytics while preserving privacy
- Configurable notification preferences

## Customization

### Adding New Profile Fields
To add new profile fields, modify the `UserProfile` model and create a new migration:

```python
# Add to UserProfile model
new_field = models.CharField(max_length=100, blank=True)

# Create and run migration
python manage.py makemigrations home
python manage.py migrate
```

### Custom Groups and Roles
Modify the `create_default_groups_and_roles()` function in `utils.py` to add your community-specific groups and roles.

### Validation Rules
Customize validation functions in `utils.py` for phone numbers, postal codes, and other field-specific validation.

## Troubleshooting

### Common Issues

1. **Profile Not Found**: Ensure the UserProfile model is properly imported and the signal is working
2. **Admin Access**: Verify superuser creation and permissions
3. **Database Constraints**: Check for unique constraint violations in group/role names

### Debug Commands

```bash
# Check model structure
python manage.py shell
>>> from home.models import UserProfile
>>> UserProfile._meta.get_fields()

# Verify settings
python manage.py check

# Test database connection
python manage.py dbshell
```

## Contributing

When contributing to this user profile system:

1. **Follow Django conventions** for model design
2. **Add comprehensive tests** for new functionality
3. **Update documentation** for new features
4. **Maintain backward compatibility** when possible
5. **Follow security best practices** for sensitive data

## License

This implementation is part of the Naboom Community project and follows Django's BSD license.

---

**Note**: This user profile system extends Django's built-in User model, avoiding circular dependencies while providing comprehensive community management features. The approach is more compatible with existing Django applications and Wagtail CMS installations.
