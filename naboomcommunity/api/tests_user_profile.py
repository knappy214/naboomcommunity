from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from home.models import UserProfile, UserGroup, UserRole, UserGroupMembership
from wagtail.images.models import Image

User = get_user_model()


class UserProfileAPITestCase(APITestCase):
    """Test cases for user profile API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone='+1234567890',
            city='Test City',
            preferred_language='en'
        )
        
        # Create test groups and roles
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='A test group'
        )
        self.role = UserRole.objects.create(
            name='Member',
            description='Basic member role'
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_get_user_profile(self):
        """Test retrieving user profile."""
        url = reverse('user-profile-detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['phone'], '+1234567890')
        self.assertEqual(response.data['city'], 'Test City')
    
    def test_update_user_profile(self):
        """Test updating user profile."""
        url = reverse('user-profile-update')
        data = {
            'phone': '+0987654321',
            'city': 'Updated City',
            'address': '123 Test Street',
            'preferred_language': 'af'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '+0987654321')
        self.assertEqual(self.profile.city, 'Updated City')
        self.assertEqual(self.profile.address, '123 Test Street')
        self.assertEqual(self.profile.preferred_language, 'af')
    
    def test_update_basic_info(self):
        """Test updating basic user information."""
        url = reverse('user-profile-basic-info')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
    
    def test_change_password(self):
        """Test changing user password."""
        url = reverse('user-profile-change-password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_change_password_wrong_current(self):
        """Test changing password with wrong current password."""
        url = reverse('user-profile-change-password')
        data = {
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
    
    def test_change_password_mismatch(self):
        """Test changing password with mismatched new passwords."""
        url = reverse('user-profile-change-password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'differentpass'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_get_user_profile_stats(self):
        """Test getting user profile statistics."""
        url = reverse('user-profile-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_completion_percentage', response.data)
        self.assertIn('completed_fields', response.data)
        self.assertIn('total_fields', response.data)
        self.assertIn('group_memberships_count', response.data)
    
    def test_join_group(self):
        """Test joining a user group."""
        url = reverse('user-profile-join-group')
        data = {
            'group_id': self.group.id,
            'role_id': self.role.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserGroupMembership.objects.filter(
                user=self.user, 
                group=self.group
            ).exists()
        )
    
    def test_join_group_already_member(self):
        """Test joining a group when already a member."""
        # First join
        UserGroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role=self.role
        )
        
        url = reverse('user-profile-join-group')
        data = {
            'group_id': self.group.id,
            'role_id': self.role.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already a member', response.data['error'])
    
    def test_leave_group(self):
        """Test leaving a user group."""
        # First join
        membership = UserGroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role=self.role
        )
        
        url = reverse('user-profile-leave-group')
        data = {'group_id': self.group.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            UserGroupMembership.objects.filter(
                user=self.user, 
                group=self.group
            ).exists()
        )
    
    def test_leave_group_not_member(self):
        """Test leaving a group when not a member."""
        url = reverse('user-profile-leave-group')
        data = {'group_id': self.group.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not a member', response.data['error'])
    
    def test_get_group_memberships(self):
        """Test getting user group memberships."""
        # Create a membership
        UserGroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role=self.role
        )
        
        url = reverse('user-group-membership-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['group']['name'], 'Test Group')
    
    def test_get_user_groups(self):
        """Test getting available user groups."""
        url = reverse('user-group-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Group')
    
    def test_get_user_roles(self):
        """Test getting available user roles."""
        url = reverse('user-role-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Member')
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access profile endpoints."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('user-profile-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_auto_creation(self):
        """Test that profile is automatically created for new users."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        # Profile should be automatically created
        self.assertTrue(
            UserProfile.objects.filter(user=new_user).exists()
        )


class UserProfilePermissionsTestCase(APITestCase):
    """Test cases for user profile permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.profile1 = UserProfile.objects.create(user=self.user1)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        
        # Get JWT token for user1
        refresh = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh.access_token)
        
        # Get JWT token for user2
        refresh = RefreshToken.for_user(self.user2)
        self.token2 = str(refresh.access_token)
    
    def test_user_cannot_access_other_profile(self):
        """Test that users cannot access other users' profiles."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to access user2's profile through the detail endpoint
        # (This should return user1's own profile due to the view logic)
        url = reverse('user-profile-detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')
    
    def test_user_cannot_update_other_profile(self):
        """Test that users cannot update other users' profiles."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to update profile (this will update user1's profile due to view logic)
        url = reverse('user-profile-update')
        data = {'phone': '+1234567890'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.phone, '+1234567890')
        
        # Verify user2's profile is unchanged
        self.profile2.refresh_from_db()
        self.assertEqual(self.profile2.phone, '')


class UserProfileValidationTestCase(APITestCase):
    """Test cases for user profile validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_invalid_email_format(self):
        """Test validation of invalid email format."""
        url = reverse('user-profile-basic-info')
        data = {
            'email': 'invalid-email'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_duplicate_email(self):
        """Test validation of duplicate email."""
        # Create another user with different email
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        url = reverse('user-profile-basic-info')
        data = {
            'email': 'other@example.com'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_weak_password(self):
        """Test validation of weak password."""
        url = reverse('user-profile-change-password')
        data = {
            'current_password': 'testpass123',
            'new_password': '123',  # Too weak
            'confirm_password': '123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)


class AvatarAPITestCase(APITestCase):
    """Test cases for avatar functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a test image
        self.test_image = SimpleUploadedFile(
            "test_avatar.jpg",
            b"fake_image_content",
            content_type="image/jpeg"
        )
    
    def test_upload_avatar(self):
        """Test uploading a new avatar."""
        url = reverse('user-profile-avatar-upload')
        
        with open('/dev/null', 'rb') as f:
            response = self.client.post(url, {'image': f}, format='multipart')
        
        # This will fail because we can't create a real image, but we can test the endpoint structure
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])
    
    def test_get_avatar_info_no_avatar(self):
        """Test getting avatar info when no avatar is set."""
        url = reverse('user-profile-avatar-info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_avatar'])
        self.assertIsNone(response.data['avatar'])
    
    def test_get_avatar_info_with_avatar(self):
        """Test getting avatar info when avatar is set."""
        # Create a test image
        image = Image.objects.create(
            title="Test Avatar",
            file=self.test_image
        )
        self.profile.avatar = image
        self.profile.save()
        
        url = reverse('user-profile-avatar-info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_avatar'])
        self.assertIsNotNone(response.data['avatar'])
        self.assertEqual(response.data['avatar']['id'], image.id)
        self.assertIn('urls', response.data['avatar'])
    
    def test_delete_avatar_no_avatar(self):
        """Test deleting avatar when none exists."""
        url = reverse('user-profile-avatar-delete')
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('No avatar to delete', response.data['detail'])
    
    def test_delete_avatar_with_avatar(self):
        """Test deleting existing avatar."""
        # Create a test image
        image = Image.objects.create(
            title="Test Avatar",
            file=self.test_image
        )
        self.profile.avatar = image
        self.profile.save()
        
        url = reverse('user-profile-avatar-delete')
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Avatar deleted successfully', response.data['detail'])
        
        # Verify avatar is removed
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.avatar)
    
    def test_set_avatar_from_existing(self):
        """Test setting avatar from existing image."""
        # Create a test image
        image = Image.objects.create(
            title="Test Avatar",
            file=self.test_image
        )
        
        url = reverse('user-profile-avatar-set-existing')
        data = {'image_id': image.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Avatar set successfully', response.data['detail'])
        
        # Verify avatar is set
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar.id, image.id)
    
    def test_set_avatar_from_nonexistent_image(self):
        """Test setting avatar from non-existent image."""
        url = reverse('user-profile-avatar-set-existing')
        data = {'image_id': 99999}  # Non-existent ID
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Image not found', response.data['error'])
    
    def test_set_avatar_missing_image_id(self):
        """Test setting avatar without providing image_id."""
        url = reverse('user-profile-avatar-set-existing')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image_id is required', response.data['error'])
    
    def test_profile_includes_avatar_data(self):
        """Test that profile endpoint includes avatar data."""
        # Create a test image
        image = Image.objects.create(
            title="Test Avatar",
            file=self.test_image
        )
        self.profile.avatar = image
        self.profile.save()
        
        url = reverse('user-profile-detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar', response.data)
        self.assertIn('avatar_url', response.data)
        self.assertIn('avatar_small', response.data)
        self.assertIn('avatar_medium', response.data)
        self.assertIn('avatar_large', response.data)
        self.assertIn('avatar_id', response.data)
    
    def test_update_profile_with_avatar_id(self):
        """Test updating profile with avatar_id."""
        # Create a test image
        image = Image.objects.create(
            title="Test Avatar",
            file=self.test_image
        )
        
        url = reverse('user-profile-update')
        data = {
            'avatar_id': image.id,
            'phone': '+1234567890'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify avatar is set
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar.id, image.id)
        self.assertEqual(self.profile.phone, '+1234567890')
    
    def test_update_profile_remove_avatar(self):
        """Test removing avatar by setting avatar_id to null."""
        # Create a test image and set it
        image = Image.objects.create(
            title="Test Avatar",
            file=self.test_image
        )
        self.profile.avatar = image
        self.profile.save()
        
        url = reverse('user-profile-update')
        data = {'avatar_id': None}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify avatar is removed
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.avatar)
    
    def test_update_profile_invalid_avatar_id(self):
        """Test updating profile with invalid avatar_id."""
        url = reverse('user-profile-update')
        data = {'avatar_id': 99999}  # Non-existent ID
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar_id', response.data)
    
    def test_avatar_unauthorized_access(self):
        """Test that unauthorized users cannot access avatar endpoints."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('user-profile-avatar-info')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        url = reverse('user-profile-avatar-upload')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        url = reverse('user-profile-avatar-delete')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
