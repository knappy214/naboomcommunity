from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import UserProfile, UserGroup, UserRole, UserGroupMembership
from .forms import CustomUserCreationForm, UserProfileForm
from .utils import validate_phone_number, validate_postal_code, get_user_statistics


class UserProfileModelTest(TestCase):
    """Test cases for the UserProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = self.user.profile
    
    def test_profile_creation(self):
        """Test that profile is automatically created when user is created."""
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertEqual(self.user.profile.user, self.user)
    
    def test_profile_string_representation(self):
        """Test profile string representation."""
        self.assertEqual(str(self.profile), "testuser's Profile")
    
    def test_profile_fields(self):
        """Test that all profile fields are properly set."""
        self.profile.phone = '+27 12 345 6789'
        self.profile.date_of_birth = '1990-01-01'
        self.profile.gender = 'Male'
        self.profile.address = '123 Test Street'
        self.profile.city = 'Pretoria'
        self.profile.province = 'Gauteng'
        self.profile.postal_code = '0001'
        self.profile.save()
        
        self.assertEqual(self.profile.phone, '+27 12 345 6789')
        self.assertEqual(self.profile.date_of_birth.year, 1990)
        self.assertEqual(self.profile.gender, 'Male')
        self.assertEqual(self.profile.address, '123 Test Street')
        self.assertEqual(self.profile.city, 'Pretoria')
        self.assertEqual(self.profile.province, 'Gauteng')
        self.assertEqual(self.profile.postal_code, '0001')
    
    def test_medical_information(self):
        """Test medical information fields."""
        self.profile.allergies = 'Peanuts, Shellfish'
        self.profile.medical_conditions = 'Asthma'
        self.profile.current_medications = 'Inhaler'
        self.profile.save()
        
        self.assertEqual(self.profile.allergies, 'Peanuts, Shellfish')
        self.assertEqual(self.profile.medical_conditions, 'Asthma')
        self.assertEqual(self.profile.current_medications, 'Inhaler')
    
    def test_emergency_contact(self):
        """Test emergency contact fields."""
        self.profile.emergency_contact_name = 'John Doe'
        self.profile.emergency_contact_phone = '+27 82 123 4567'
        self.profile.emergency_contact_relationship = 'Spouse'
        self.profile.save()
        
        self.assertEqual(self.profile.emergency_contact_name, 'John Doe')
        self.assertEqual(self.profile.emergency_contact_phone, '+27 82 123 4567')
        self.assertEqual(self.profile.emergency_contact_relationship, 'Spouse')
    
    def test_user_preferences(self):
        """Test user preference fields."""
        self.profile.preferred_language = 'af'
        self.profile.timezone = 'Africa/Johannesburg'
        self.profile.email_notifications = False
        self.profile.sms_notifications = True
        self.profile.mfa_enabled = True
        self.profile.save()
        
        self.assertEqual(self.profile.preferred_language, 'af')
        self.assertEqual(self.profile.timezone, 'Africa/Johannesburg')
        self.assertFalse(self.profile.email_notifications)
        self.assertTrue(self.profile.sms_notifications)
        self.assertTrue(self.profile.mfa_enabled)
    
    def test_get_full_address(self):
        """Test the get_full_address method."""
        self.profile.address = '123 Test Street'
        self.profile.city = 'Pretoria'
        self.profile.province = 'Gauteng'
        self.profile.postal_code = '0001'
        self.profile.save()
        
        expected_address = '123 Test Street, Pretoria, Gauteng, 0001'
        self.assertEqual(self.profile.get_full_address(), expected_address)
        
        # Test with missing fields
        self.profile.address = ''
        self.profile.save()
        expected_address = 'Pretoria, Gauteng, 0001'
        self.assertEqual(self.profile.get_full_address(), expected_address)


class UserGroupTest(TestCase):
    """Test cases for the UserGroup model."""
    
    def setUp(self):
        """Set up test data."""
        self.group_data = {
            'name': 'Test Group',
            'description': 'A test group for testing purposes'
        }
    
    def test_create_group(self):
        """Test creating a user group."""
        group = UserGroup.objects.create(**self.group_data)
        self.assertEqual(group.name, 'Test Group')
        self.assertEqual(group.description, 'A test group for testing purposes')
        self.assertTrue(group.is_active)
        self.assertIsNotNone(group.id)
    
    def test_group_string_representation(self):
        """Test group string representation."""
        group = UserGroup.objects.create(**self.group_data)
        self.assertEqual(str(group), 'Test Group')
    
    def test_unique_group_name(self):
        """Test that group names must be unique."""
        UserGroup.objects.create(**self.group_data)
        with self.assertRaises(IntegrityError):
            UserGroup.objects.create(**self.group_data)


class UserRoleTest(TestCase):
    """Test cases for the UserRole model."""
    
    def setUp(self):
        """Set up test data."""
        self.role_data = {
            'name': 'Test Role',
            'description': 'A test role for testing purposes',
            'permissions': {'can_edit': True, 'can_delete': False}
        }
    
    def test_create_role(self):
        """Test creating a user role."""
        role = UserRole.objects.create(**self.role_data)
        self.assertEqual(role.name, 'Test Role')
        self.assertEqual(role.description, 'A test role for testing purposes')
        self.assertEqual(role.permissions, {'can_edit': True, 'can_delete': False})
        self.assertTrue(role.is_active)
    
    def test_role_string_representation(self):
        """Test role string representation."""
        role = UserRole.objects.create(**self.role_data)
        self.assertEqual(str(role), 'Test Role')
    
    def test_unique_role_name(self):
        """Test that role names must be unique."""
        UserRole.objects.create(**self.role_data)
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(**self.role_data)


class UserGroupMembershipTest(TestCase):
    """Test cases for the UserGroupMembership model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='A test group'
        )
        self.role = UserRole.objects.create(
            name='Test Role',
            description='A test role',
            permissions={}
        )
    
    def test_create_membership(self):
        """Test creating a group membership."""
        membership = UserGroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role=self.role
        )
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.group, self.group)
        self.assertEqual(membership.role, self.role)
        self.assertTrue(membership.is_active)
        self.assertIsNotNone(membership.joined_at)
    
    def test_unique_user_group_constraint(self):
        """Test that a user can only be in a group once."""
        UserGroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role=self.role
        )
        
        with self.assertRaises(IntegrityError):
            UserGroupMembership.objects.create(
                user=self.user,
                group=self.group,
                role=self.role
            )
    
    def test_membership_string_representation(self):
        """Test membership string representation."""
        membership = UserGroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role=self.role
        )
        expected = f"{self.user.username} - {self.group.name} ({self.role.name})"
        self.assertEqual(str(membership), expected)


class FormTest(TestCase):
    """Test cases for forms."""
    
    def test_custom_user_creation_form(self):
        """Test the custom user creation form."""
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
        self.assertTrue(form.is_valid())
    
    def test_user_profile_form(self):
        """Test the user profile form."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        form_data = {
            'phone': '+27 82 123 4567',
            'city': 'Johannesburg',
            'preferred_language': 'af'
        }
        form = UserProfileForm(data=form_data, instance=user.profile)
        self.assertTrue(form.is_valid())


class UtilityFunctionTest(TestCase):
    """Test cases for utility functions."""
    
    def test_validate_phone_number(self):
        """Test phone number validation."""
        # Valid phone numbers
        self.assertTrue(validate_phone_number('+27 12 345 6789'))
        self.assertTrue(validate_phone_number('012 345 6789'))
        self.assertTrue(validate_phone_number('+27 82 123 4567'))
        
        # Invalid phone numbers
        self.assertFalse(validate_phone_number('123'))
        self.assertFalse(validate_phone_number('abc'))
        self.assertFalse(validate_phone_number(''))
    
    def test_validate_postal_code(self):
        """Test postal code validation."""
        # Valid postal codes
        self.assertTrue(validate_postal_code('0001'))
        self.assertTrue(validate_postal_code('1234'))
        self.assertTrue(validate_postal_code(' 5678 '))
        
        # Invalid postal codes
        self.assertFalse(validate_postal_code('123'))
        self.assertFalse(validate_postal_code('12345'))
        self.assertFalse(validate_postal_code('abcd'))
    
    def test_get_user_statistics(self):
        """Test user statistics function."""
        # Create some test data
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass1'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass2'
        )
        
        # Update profiles
        user1.profile.city = 'Pretoria'
        user1.profile.preferred_language = 'en'
        user1.profile.save()
        
        user2.profile.city = 'Cape Town'
        user2.profile.preferred_language = 'af'
        user2.profile.save()
        
        stats = get_user_statistics()
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['active_users'], 2)
        self.assertEqual(stats['language_distribution']['en'], 1)
        self.assertEqual(stats['language_distribution']['af'], 1)
        self.assertEqual(stats['city_distribution']['Pretoria'], 1)
        self.assertEqual(stats['city_distribution']['Cape Town'], 1)


class AdminTest(TestCase):
    """Test cases for admin interface."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')
    
    def test_admin_access(self):
        """Test that admin users can access the admin interface."""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_admin(self):
        """Test user admin interface."""
        response = self.client.get('/admin/auth/user/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_profile_admin(self):
        """Test user profile admin interface."""
        response = self.client.get('/admin/home/userprofile/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_group_admin(self):
        """Test user group admin interface."""
        response = self.client.get('/admin/home/usergroup/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_role_admin(self):
        """Test user role admin interface."""
        response = self.client.get('/admin/home/userrole/')
        self.assertEqual(response.status_code, 200)
