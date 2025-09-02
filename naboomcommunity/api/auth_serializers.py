from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            User.USERNAME_FIELD,
            "email",
            "password",
        ) if hasattr(User, "email") else ("username", "email", "password")
        extra_kwargs = {"email": {"required": True}}

    def validate_password(self, value):
        try:
            validate_password(value)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add email field to the serializer
        self.fields['email'] = serializers.EmailField(required=False)
        # Make username field optional since we'll set it in validate
        self.fields['username'].required = False
    
    def validate(self, attrs):
        email = attrs.get("email")
        if email:
            # Find user by email and set the username field for authentication
            try:
                user = User.objects.get(email__iexact=email)
                attrs["username"] = user.username
            except User.DoesNotExist:
                # If user not found, set a dummy username to prevent KeyError
                attrs["username"] = "nonexistent_user"
        # Ensure username field is always present
        if "username" not in attrs:
            attrs["username"] = attrs.get("email", "")
        return super().validate(attrs)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
