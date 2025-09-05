from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsProfileOwner(permissions.BasePermission):
    """
    Custom permission to only allow users to access their own profile.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Only allow users to access their own profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsGroupMember(permissions.BasePermission):
    """
    Custom permission to only allow group members to access group-specific data.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the group
        if hasattr(obj, 'group'):
            from home.models import UserGroupMembership
            return UserGroupMembership.objects.filter(
                user=request.user, 
                group=obj.group, 
                is_active=True
            ).exists()
        return False


class CanManageGroupMemberships(permissions.BasePermission):
    """
    Custom permission to allow users to manage their own group memberships.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Users can only manage their own group memberships
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit, but allow read access to all authenticated users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff
