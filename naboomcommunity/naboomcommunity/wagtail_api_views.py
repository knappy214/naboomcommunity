from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from wagtail.api.v2.views import BaseAPIViewSet
from wagtail.api.v2.serializers import BaseSerializer
from home.models import UserProfile, UserGroup, UserRole, UserGroupMembership

User = get_user_model()


class UserProfileSerializer(BaseSerializer):
    """Wagtail API v2 serializer for UserProfile."""
    
    def to_representation(self, instance):
        """Convert UserProfile instance to API representation."""
        return {
            'id': instance.id,
            'user_id': instance.user.id,
            'username': instance.user.username,
            'email': instance.user.email,
            'first_name': instance.user.first_name,
            'last_name': instance.user.last_name,
            'phone': instance.phone,
            'date_of_birth': instance.date_of_birth,
            'gender': instance.gender,
            'address': instance.address,
            'city': instance.city,
            'province': instance.province,
            'postal_code': instance.postal_code,
            'allergies': instance.allergies,
            'medical_conditions': instance.medical_conditions,
            'current_medications': instance.current_medications,
            'emergency_contact_name': instance.emergency_contact_name,
            'emergency_contact_phone': instance.emergency_contact_phone,
            'emergency_contact_relationship': instance.emergency_contact_relationship,
            'preferred_language': instance.preferred_language,
            'timezone': instance.timezone,
            'email_notifications': instance.email_notifications,
            'sms_notifications': instance.sms_notifications,
            'mfa_enabled': instance.mfa_enabled,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class UserGroupSerializer(BaseSerializer):
    """Wagtail API v2 serializer for UserGroup."""
    
    def to_representation(self, instance):
        """Convert UserGroup instance to API representation."""
        return {
            'id': instance.id,
            'name': instance.name,
            'description': instance.description,
            'is_active': instance.is_active,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class UserRoleSerializer(BaseSerializer):
    """Wagtail API v2 serializer for UserRole."""
    
    def to_representation(self, instance):
        """Convert UserRole instance to API representation."""
        return {
            'id': instance.id,
            'name': instance.name,
            'description': instance.description,
            'permissions': instance.permissions,
            'is_active': instance.is_active,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class UserGroupMembershipSerializer(BaseSerializer):
    """Wagtail API v2 serializer for UserGroupMembership."""
    
    def to_representation(self, instance):
        """Convert UserGroupMembership instance to API representation."""
        return {
            'id': instance.id,
            'group': UserGroupSerializer(instance.group).to_representation(instance.group),
            'role': UserRoleSerializer(instance.role).to_representation(instance.role),
            'joined_at': instance.joined_at,
            'is_active': instance.is_active,
            'notes': instance.notes,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class UserProfileAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserProfile model."""
    
    name = "user-profiles"
    model = UserProfile
    serializer_class = UserProfileSerializer
    
    def authenticate_user(self, request):
        """Authenticate user using JWT token."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            print("DEBUG: No Bearer token found")
            return False
        
        token = auth_header.split(' ')[1]
        try:
            # Manually decode the JWT token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            request.user = user
            print(f"DEBUG: Authenticated user {user.username} (ID: {user.id})")
            return True
        except (InvalidToken, TokenError) as e:
            print(f"DEBUG: JWT token invalid: {e}")
        except User.DoesNotExist:
            print(f"DEBUG: User with ID {user_id} not found")
        except Exception as e:
            print(f"DEBUG: Unexpected error in JWT authentication: {e}")
        return False
    
    def get_queryset(self):
        """Get queryset based on authentication and permissions."""
        if self.request.user.is_authenticated:
            # Return only the current user's profile
            return UserProfile.objects.filter(user=self.request.user)
        return UserProfile.objects.none()
    
    def list(self, request, *args, **kwargs):
        """List user profiles (only current user's profile)."""
        print(f"DEBUG: Starting list method, user authenticated: {request.user.is_authenticated}")
        print(f"DEBUG: User: {request.user}")
        print(f"DEBUG: Authorization header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        
        # Try to authenticate with JWT token
        if not self.authenticate_user(request):
            print("DEBUG: JWT authentication failed, returning empty response")
            return JsonResponse({
                'meta': {'total_count': 0},
                'items': []
            })
        
        print(f"DEBUG: After authentication, user: {request.user.username} (ID: {request.user.id})")
        
        # Get or create the current user's profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        print(f"DEBUG: Profile {'created' if created else 'found'}: {profile.id}")
        
        queryset = UserProfile.objects.filter(id=profile.id)
        print(f"DEBUG: Queryset count: {queryset.count()}")
        
        serializer = self.get_serializer(queryset, many=True)
        print(f"DEBUG: Serialized data: {serializer.data}")
        
        return JsonResponse({
            'meta': {
                'total_count': queryset.count()
            },
            'items': serializer.data
        })
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        """Retrieve a specific user profile."""
        # Try to authenticate with JWT token
        if not self.authenticate_user(request):
            return JsonResponse(
                {"detail": "Authentication required"}, 
                status=401
            )
        
        # Get or create the current user's profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return JsonResponse(serializer.data)


class UserGroupAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserGroup model."""
    
    name = "user-groups"
    model = UserGroup
    serializer_class = UserGroupSerializer
    
    def get_queryset(self):
        """Get active user groups."""
        return UserGroup.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """List user groups."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({
            'meta': {
                'total_count': queryset.count()
            },
            'items': serializer.data
        })


class UserRoleAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserRole model."""
    
    name = "user-roles"
    model = UserRole
    serializer_class = UserRoleSerializer
    
    def get_queryset(self):
        """Get active user roles."""
        return UserRole.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """List user roles."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({
            'meta': {
                'total_count': queryset.count()
            },
            'items': serializer.data
        })


class UserGroupMembershipAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserGroupMembership model."""
    
    name = "user-group-memberships"
    model = UserGroupMembership
    serializer_class = UserGroupMembershipSerializer
    
    def get_queryset(self):
        """Get group memberships for the current user."""
        if self.request.user.is_authenticated:
            return UserGroupMembership.objects.filter(user=self.request.user)
        return UserGroupMembership.objects.none()
    
    def list(self, request, *args, **kwargs):
        """List user group memberships."""
        if not request.user.is_authenticated:
            return JsonResponse({
                'meta': {'total_count': 0},
                'items': []
            })
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({
            'meta': {
                'total_count': queryset.count()
            },
            'items': serializer.data
        })
