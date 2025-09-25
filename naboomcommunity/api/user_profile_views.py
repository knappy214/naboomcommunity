from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from home.models import UserProfile, UserGroup, UserRole, UserGroupMembership
from .user_profile_serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserBasicInfoUpdateSerializer,
    UserPasswordChangeSerializer,
    UserGroupSerializer,
    UserRoleSerializer,
    UserGroupMembershipSerializer,
    AvatarUploadSerializer
)
from .permissions import IsProfileOwner, CanManageGroupMemberships, IsAdminOrReadOnly

User = get_user_model()


class UserProfileDetailView(generics.RetrieveAPIView):
    """
    Retrieve the current user's profile.
    GET /api/user-profile/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_object(self):
        """Get the current user's profile."""
        profile, _ = UserProfile.objects.select_related("user", "avatar").get_or_create(user=self.request.user)
        return profile


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    Update the current user's profile.
    PUT/PATCH /api/user-profile/update/
    """
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_object(self):
        """Get the current user's profile."""
        profile, _ = UserProfile.objects.select_related("user", "avatar").get_or_create(user=self.request.user)
        return profile


class UserBasicInfoUpdateView(generics.UpdateAPIView):
    """
    Update the current user's basic information (name, email).
    PUT/PATCH /api/user-profile/basic-info/
    """
    serializer_class = UserBasicInfoUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get the current user."""
        return self.request.user


class UserPasswordChangeView(APIView):
    """
    Change the current user's password.
    POST /api/user-profile/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Change user password."""
        serializer = UserPasswordChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"detail": "Password changed successfully"}, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserGroupListView(generics.ListAPIView):
    """
    List all available user groups.
    GET /api/user-groups/
    """
    serializer_class = UserGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    queryset = UserGroup.objects.all()


class UserRoleListView(generics.ListAPIView):
    """
    List all available user roles.
    GET /api/user-roles/
    """
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    queryset = UserRole.objects.all()


class UserGroupMembershipListView(generics.ListCreateAPIView):
    """
    List and create user group memberships for the current user.
    GET/POST /api/user-profile/group-memberships/
    """
    serializer_class = UserGroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageGroupMemberships]

    def get_queryset(self):
        """Get group memberships for the current user."""
        return (
            UserGroupMembership.objects.select_related("group", "role")
            .filter(user=self.request.user)
        )
    
    def perform_create(self, serializer):
        """Create a new group membership for the current user."""
        serializer.save(user=self.request.user)


class UserGroupMembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific group membership.
    GET/PUT/PATCH/DELETE /api/user-profile/group-memberships/{id}/
    """
    serializer_class = UserGroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageGroupMemberships]
    
    def get_queryset(self):
        """Get group memberships for the current user only."""
        return (
            UserGroupMembership.objects.select_related("group", "role")
            .filter(user=self.request.user)
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_stats(request):
    """
    Get statistics about the current user's profile.
    GET /api/user-profile/stats/
    """
    user = request.user
    profile, _ = UserProfile.objects.select_related("user", "avatar").get_or_create(user=user)

    # Get group memberships
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
    
    stats = {
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
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_group(request):
    """
    Join a user group.
    POST /api/user-profile/join-group/
    """
    group_id = request.data.get('group_id')
    role_id = request.data.get('role_id')
    
    if not group_id:
        return Response(
            {"error": "group_id is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        group = UserGroup.objects.get(id=group_id)
    except UserGroup.DoesNotExist:
        return Response(
            {"error": "Group not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is already a member
    if UserGroupMembership.objects.filter(user=request.user, group=group).exists():
        return Response(
            {"error": "You are already a member of this group"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get role (default to first available role if not specified)
    if role_id:
        try:
            role = UserRole.objects.get(id=role_id)
        except UserRole.DoesNotExist:
            return Response(
                {"error": "Role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Get the first available role for this group
        role = UserRole.objects.first()
        if not role:
            return Response(
                {"error": "No roles available"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Create membership
    membership = UserGroupMembership.objects.create(
        user=request.user,
        group=group,
        role=role
    )
    
    serializer = UserGroupMembershipSerializer(membership)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_group(request):
    """
    Leave a user group.
    POST /api/user-profile/leave-group/
    """
    group_id = request.data.get('group_id')
    
    if not group_id:
        return Response(
            {"error": "group_id is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        membership = UserGroupMembership.objects.get(
            user=request.user, 
            group_id=group_id
        )
    except UserGroupMembership.DoesNotExist:
        return Response(
            {"error": "You are not a member of this group"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    membership.delete()
    return Response(
        {"detail": "Successfully left the group"}, 
        status=status.HTTP_200_OK
    )


class AvatarUploadView(APIView):
    """
    Upload a new avatar for the current user.
    POST /api/user-profile/avatar/upload/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Upload a new avatar."""
        serializer = AvatarUploadSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            image = serializer.save()
            
            # Return the updated profile with avatar info
            profile = request.user.profile
            profile_serializer = UserProfileSerializer(profile)
            
            return Response({
                'detail': 'Avatar uploaded successfully',
                'avatar': {
                    'id': image.id,
                    'url': image.file.url,
                    'title': image.title
                },
                'profile': profile_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvatarDeleteView(APIView):
    """
    Delete the current user's avatar.
    DELETE /api/user-profile/avatar/delete/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        """Delete the current user's avatar."""
        profile = request.user.profile
        
        if not profile.avatar:
            return Response(
                {"detail": "No avatar to delete"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store avatar info before deletion
        avatar_info = {
            'id': profile.avatar.id,
            'title': profile.avatar.title
        }
        
        # Delete the avatar
        profile.avatar = None
        profile.save()
        
        return Response({
            'detail': 'Avatar deleted successfully',
            'deleted_avatar': avatar_info
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def avatar_info(request):
    """
    Get current user's avatar information.
    GET /api/user-profile/avatar/info/
    """
    profile = request.user.profile
    
    if not profile.avatar:
        return Response({
            'has_avatar': False,
            'avatar': None
        })
    
    avatar = profile.avatar
    return Response({
        'has_avatar': True,
        'avatar': {
            'id': avatar.id,
            'title': avatar.title,
            'url': profile.avatar_url,  # Use the proper serving URL
            'width': avatar.width,
            'height': avatar.height,
            'file_size': avatar.file.size,
            'created_at': avatar.created_at,
            'urls': {
                'original': profile.get_avatar_original(),
                'small': profile.get_avatar_small(),
                'medium': profile.get_avatar_medium(),
                'large': profile.get_avatar_large()
            }
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_avatar_from_existing(request):
    """
    Set avatar from an existing image in the system.
    POST /api/user-profile/avatar/set-existing/
    """
    image_id = request.data.get('image_id')
    
    if not image_id:
        return Response(
            {"error": "image_id is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from wagtail.images.models import Image
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        return Response(
            {"error": "Image not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Set the avatar
    profile = request.user.profile
    profile.avatar = image
    profile.save()
    
    # Return updated profile
    profile_serializer = UserProfileSerializer(profile)
    
    return Response({
        'detail': 'Avatar set successfully',
        'avatar': {
            'id': image.id,
            'url': image.file.url,
            'title': image.title
        },
        'profile': profile_serializer.data
    }, status=status.HTTP_200_OK)
