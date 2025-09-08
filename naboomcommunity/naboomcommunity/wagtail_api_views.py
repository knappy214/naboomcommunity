from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from wagtail.api.v2.serializers import BaseSerializer
from wagtail.api.v2.views import BaseAPIViewSet
from home.models import UserGroup, UserGroupMembership, UserProfile, UserRole


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
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
        }


class UserRoleSerializer(BaseSerializer):
    """Wagtail API v2 serializer for UserRole."""

    def to_representation(self, instance):
        """Convert UserRole instance to API representation."""
        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "permissions": instance.permissions,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
        }


class UserGroupMembershipSerializer(BaseSerializer):
    """Wagtail API v2 serializer for UserGroupMembership."""

    def to_representation(self, instance):
        """Convert UserGroupMembership instance to API representation."""
        return {
            "id": instance.id,
            "group": {
                "id": instance.group.id,
                "name": instance.group.name,
                "description": instance.group.description,
            },
            "role": {
                "id": instance.role.id,
                "name": instance.role.name,
                "description": instance.role.description,
                "permissions": instance.role.permissions,
            },
            "joined_at": instance.joined_at,
            "is_active": instance.is_active,
        }


class UserProfileAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserProfile model."""

    name = "user-profiles"
    model = UserProfile
    serializer_class = UserProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    # Add custom fields that can be requested via ?fields= parameter
    body_fields = BaseAPIViewSet.body_fields + ['stats', 'avatar_info']

    def authenticate_user(self, request) -> bool:
        """Authenticate request using JWT token."""
        authenticator = JWTAuthentication()
        try:
            user_auth = authenticator.authenticate(request)
            if user_auth is None:
                return False
            request.user, _ = user_auth
            return True
        except Exception:
            return False

    def listing_view(self, request):
        if not self.authenticate_user(request):
            return JsonResponse({'meta': {'total_count': 0}, 'items': []})
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        data = self.serializer_class().to_representation(profile)
        
        # Add custom fields if requested
        if 'stats' in request.GET.get('fields', '').split(','):
            data['stats'] = self._get_profile_stats(profile)
        if 'avatar_info' in request.GET.get('fields', '').split(','):
            data['avatar_info'] = self._get_avatar_info(profile)
            
        return JsonResponse({'meta': {'total_count': 1}, 'items': [data]})

    def detail_view(self, request, pk):
        if not self.authenticate_user(request):
            return JsonResponse({'detail': 'Authentication required'}, status=401)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        data = self.serializer_class().to_representation(profile)
        
        # Add custom fields if requested
        if 'stats' in request.GET.get('fields', '').split(','):
            data['stats'] = self._get_profile_stats(profile)
        if 'avatar_info' in request.GET.get('fields', '').split(','):
            data['avatar_info'] = self._get_avatar_info(profile)
            
        return JsonResponse(data)
    
    def _get_profile_stats(self, profile):
        """Get statistics about the user's profile."""
        user = profile.user
        group_memberships = (
            UserGroupMembership.objects.select_related("group", "role")
            .filter(user=user, is_active=True)
        )
        
        # Calculate profile completion percentage
        profile_fields = [
            'phone', 'date_of_birth', 'gender', 'address', 'city', 
            'province', 'postal_code', 'emergency_contact_name', 
            'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        
        completed_fields = sum(1 for field in profile_fields if getattr(profile, field))
        total_fields = len(profile_fields)
        completion_percentage = (completed_fields / total_fields) * 100
        
        return {
            'profile_completion_percentage': round(completion_percentage, 2),
            'completed_fields': completed_fields,
            'total_fields': total_fields,
            'group_memberships_count': group_memberships.count(),
            'active_groups': [membership.group.name for membership in group_memberships],
            'profile_created_at': profile.created_at,
            'profile_updated_at': profile.updated_at,
            'user_joined_at': user.date_joined,
            'last_login': user.last_login,
        }
    
    def _get_avatar_info(self, profile):
        """Get avatar information for the user."""
        if not profile.avatar:
            return {
                'has_avatar': False,
                'avatar': None
            }
        
        avatar = profile.avatar
        return {
            'has_avatar': True,
            'avatar': {
                'id': avatar.id,
                'title': avatar.title,
                'url': avatar.file.url,
                'width': avatar.width,
                'height': avatar.height,
                'file_size': avatar.file.size,
                'created_at': avatar.created_at,
                'urls': {
                    'original': profile.avatar_url,
                    'small': profile.get_avatar_small(),
                    'medium': profile.get_avatar_medium(),
                    'large': profile.get_avatar_large()
                }
            }
        }


class UserGroupAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserGroup model."""

    name = "user-groups"
    model = UserGroup
    serializer_class = UserGroupSerializer

    def listing_view(self, request):
        queryset = UserGroup.objects.all()
        items = [
            self.serializer_class().to_representation(group)
            for group in queryset
        ]
        return JsonResponse({"meta": {"total_count": len(items)}, "items": items})

    def detail_view(self, request, pk):
        try:
            group = UserGroup.objects.get(pk=pk)
        except UserGroup.DoesNotExist:
            return JsonResponse({"detail": "Not found"}, status=404)
        data = self.serializer_class().to_representation(group)
        return JsonResponse(data)


class UserRoleAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserRole model."""

    name = "user-roles"
    model = UserRole
    serializer_class = UserRoleSerializer

    def listing_view(self, request):
        queryset = UserRole.objects.all()
        items = [
            self.serializer_class().to_representation(role)
            for role in queryset
        ]
        return JsonResponse({"meta": {"total_count": len(items)}, "items": items})

    def detail_view(self, request, pk):
        try:
            role = UserRole.objects.get(pk=pk)
        except UserRole.DoesNotExist:
            return JsonResponse({"detail": "Not found"}, status=404)
        data = self.serializer_class().to_representation(role)
        return JsonResponse(data)


class UserGroupMembershipAPIViewSet(BaseAPIViewSet):
    """Wagtail API v2 ViewSet for UserGroupMembership model."""

    name = "user-group-memberships"
    model = UserGroupMembership
    serializer_class = UserGroupMembershipSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def authenticate_user(self, request) -> bool:
        """Authenticate request using JWT token."""
        authenticator = JWTAuthentication()
        try:
            user_auth = authenticator.authenticate(request)
            if user_auth is None:
                return False
            request.user, _ = user_auth
            return True
        except Exception:
            return False

    def listing_view(self, request):
        if not self.authenticate_user(request):
            return JsonResponse({"meta": {"total_count": 0}, "items": []})

        queryset = (
            UserGroupMembership.objects.select_related("group", "role")
            .filter(user=request.user)
        )
        items = [
            self.serializer_class().to_representation(membership)
            for membership in queryset
        ]
        return JsonResponse({"meta": {"total_count": len(items)}, "items": items})

    def detail_view(self, request, pk):
        if not self.authenticate_user(request):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        try:
            membership = (
                UserGroupMembership.objects.select_related("group", "role")
                .get(pk=pk, user=request.user)
            )
        except UserGroupMembership.DoesNotExist:
            return JsonResponse({"detail": "Not found"}, status=404)
        data = self.serializer_class().to_representation(membership)
        return JsonResponse(data)