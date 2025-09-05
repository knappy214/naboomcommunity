from django.contrib.auth import get_user_model
from rest_framework import serializers
from home.models import UserProfile, UserGroup, UserRole, UserGroupMembership
from wagtail.images.api.v2.serializers import ImageSerializer

User = get_user_model()


class UserGroupSerializer(serializers.ModelSerializer):
    """Serializer for UserGroup model."""
    
    class Meta:
        model = UserGroup
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model."""
    
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description', 'permissions', 'is_active', 'created_at', 'updated_at']


class UserGroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for UserGroupMembership model."""
    group = UserGroupSerializer(read_only=True)
    role = UserRoleSerializer(read_only=True)
    group_id = serializers.IntegerField(write_only=True, required=False)
    role_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = UserGroupMembership
        fields = [
            'id', 'group', 'role', 'group_id', 'role_id', 
            'joined_at', 'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model with comprehensive profile data."""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    
    # Avatar fields
    avatar = ImageSerializer(read_only=True)
    avatar_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    avatar_url = serializers.CharField(read_only=True)
    avatar_small = serializers.CharField(source='get_avatar_small', read_only=True)
    avatar_medium = serializers.CharField(source='get_avatar_medium', read_only=True)
    avatar_large = serializers.CharField(source='get_avatar_large', read_only=True)
    
    # Group memberships
    group_memberships = UserGroupMembershipSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            # User basic info
            'user_id', 'username', 'email', 'first_name', 'last_name', 
            'is_active', 'date_joined', 'last_login',
            
            # Personal Information
            'avatar', 'avatar_id', 'avatar_url', 'avatar_small', 'avatar_medium', 'avatar_large',
            'phone', 'date_of_birth', 'gender', 'address', 'city', 
            'province', 'postal_code',
            
            # Medical Information
            'allergies', 'medical_conditions', 'current_medications',
            
            # Emergency Contact
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relationship',
            
            # Preferences
            'preferred_language', 'timezone', 'email_notifications', 
            'sms_notifications', 'mfa_enabled',
            
            # Metadata
            'created_at', 'updated_at',
            
            # Group memberships
            'group_memberships'
        ]
        read_only_fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 
                           'is_active', 'date_joined', 'last_login', 'created_at', 'updated_at']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating UserProfile model (excludes sensitive fields)."""
    avatar_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = UserProfile
        fields = [
            # Personal Information
            'avatar_id', 'phone', 'date_of_birth', 'gender', 'address', 'city', 
            'province', 'postal_code',
            
            # Medical Information
            'allergies', 'medical_conditions', 'current_medications',
            
            # Emergency Contact
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relationship',
            
            # Preferences
            'preferred_language', 'timezone', 'email_notifications', 
            'sms_notifications', 'mfa_enabled'
        ]
    
    def update(self, instance, validated_data):
        """Update profile with avatar handling."""
        avatar_id = validated_data.pop('avatar_id', None)
        
        # Handle avatar update
        if avatar_id is not None:
            if avatar_id:
                try:
                    from wagtail.images.models import Image
                    avatar = Image.objects.get(id=avatar_id)
                    instance.avatar = avatar
                except Image.DoesNotExist:
                    raise serializers.ValidationError({'avatar_id': 'Invalid avatar ID'})
            else:
                instance.avatar = None
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class UserBasicInfoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating basic user information."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def validate_email(self, value):
        """Ensure email is unique if changed."""
        if self.instance and self.instance.email != value:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserPasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate password change data."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        from django.contrib.auth.password_validation import validate_password
        from django.core import exceptions
        
        try:
            validate_password(value)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class AvatarUploadSerializer(serializers.Serializer):
    """Serializer for avatar upload."""
    image = serializers.ImageField(required=True)
    
    def validate_image(self, value):
        """Validate uploaded image."""
        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Maximum size is 5MB.")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        return value
    
    def create(self, validated_data):
        """Create a new image and assign it as avatar."""
        from wagtail.images.models import Image
        
        # Create new image
        image = Image.objects.create(
            title=f"Avatar for {self.context['request'].user.username}",
            file=validated_data['image']
        )
        
        # Assign to user profile
        profile = self.context['request'].user.profile
        profile.avatar = image
        profile.save()
        
        return image
