from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, UserGroup, UserRole, UserGroupMembership


class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users with extended profile fields.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    # Profile fields
    phone = forms.CharField(max_length=20, required=False, help_text="Contact phone number")
    date_of_birth = forms.DateField(required=False, help_text="User's date of birth")
    gender = forms.CharField(max_length=20, required=False, help_text="User's gender identity")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text="Full residential address")
    city = forms.CharField(max_length=100, required=False, help_text="City of residence")
    province = forms.CharField(max_length=100, required=False, help_text="Province/State of residence")
    postal_code = forms.CharField(max_length=20, required=False, help_text="Postal/ZIP code")
    preferred_language = forms.ChoiceField(
        choices=[('en', 'English'), ('af', 'Afrikaans')],
        initial='en',
        required=False,
        help_text="Preferred language for communications"
    )
    timezone = forms.CharField(max_length=50, initial='UTC', required=False, help_text="User's timezone")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields['email'].required = True
        # Add help text and styling
        for field_name, field in self.fields.items():
            if field.help_text:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.help_text
    
    def clean_email(self):
        """Ensure email is unique."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email
    
    def save(self, commit=True):
        """Save the user and create the profile."""
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.date_of_birth = self.cleaned_data.get('date_of_birth')
            profile.gender = self.cleaned_data.get('gender', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.city = self.cleaned_data.get('city', '')
            profile.province = self.cleaned_data.get('province', '')
            profile.postal_code = self.cleaned_data.get('postal_code', '')
            profile.preferred_language = self.cleaned_data.get('preferred_language', 'en')
            profile.timezone = self.cleaned_data.get('timezone', 'UTC')
            profile.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Form for editing existing users.
    """
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add styling to form fields
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    """
    Form for users to edit their own profile (excluding sensitive fields).
    """
    class Meta:
        model = UserProfile
        fields = (
            'phone', 'date_of_birth', 'gender', 'address', 'city', 'province', 'postal_code',
            'preferred_language', 'timezone', 'email_notifications', 'sms_notifications'
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes and help text
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field.help_text:
                field.widget.attrs['placeholder'] = field.help_text


class MedicalInfoForm(forms.ModelForm):
    """
    Form for users to update their medical information.
    """
    class Meta:
        model = UserProfile
        fields = (
            'allergies', 'medical_conditions', 'current_medications'
        )
        widgets = {
            'allergies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'current_medications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.help_text:
                field.widget.attrs['placeholder'] = field.help_text


class EmergencyContactForm(forms.ModelForm):
    """
    Form for users to update their emergency contact information.
    """
    class Meta:
        model = UserProfile
        fields = (
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field.help_text:
                field.widget.attrs['placeholder'] = field.help_text


class UserGroupForm(forms.ModelForm):
    """
    Form for creating and editing user groups.
    """
    class Meta:
        model = UserGroup
        fields = ('name', 'description', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.widget.attrs['class'] = 'form-control'


class UserRoleForm(forms.ModelForm):
    """
    Form for creating and editing user roles.
    """
    class Meta:
        model = UserRole
        fields = ('name', 'description', 'permissions', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'permissions': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.widget.attrs['class'] = 'form-control'
        
        # Add help text for permissions field
        self.fields['permissions'].help_text = (
            'Enter permissions as JSON. Example: {"can_edit": true, "can_delete": false, "can_view": true}'
        )
    
    def clean_permissions(self):
        """Validate that permissions field contains valid JSON."""
        permissions = self.cleaned_data.get('permissions')
        if permissions:
            try:
                import json
                json.loads(permissions)
            except json.JSONDecodeError:
                raise ValidationError('Permissions must be valid JSON format.')
        return permissions


class UserGroupMembershipForm(forms.ModelForm):
    """
    Form for managing user group memberships.
    """
    class Meta:
        model = UserGroupMembership
        fields = ('user', 'group', 'role', 'is_active', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_active', 'user', 'group', 'role']:
                field.widget.attrs['class'] = 'form-control'
        
        # Add select widgets for foreign keys
        self.fields['user'].widget.attrs['class'] = 'form-select'
        self.fields['group'].widget.attrs['class'] = 'form-select'
        self.fields['role'].widget.attrs['class'] = 'form-select'
    
    def clean(self):
        """Ensure user can only be in a group once."""
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        group = cleaned_data.get('group')
        
        if user and group:
            # Check if membership already exists (excluding current instance)
            existing = UserGroupMembership.objects.filter(
                user=user, group=group
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'User {user.username} is already a member of group {group.name}.'
                )
        
        return cleaned_data


class UserProfileAdminForm(forms.ModelForm):
    """Custom form for UserProfile admin that makes user field read-only."""
    
    # Override the user field completely
    user_display = forms.CharField(
        label="User",
        required=False,
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'readonly-field',
            'style': 'background-color: #f8f9fa; color: #6c757d; cursor: not-allowed; border: 1px solid #dee2e6; padding: 8px; width: 100%;'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'phone', 'date_of_birth', 'gender', 'address', 
            'city', 'province', 'postal_code', 'allergies', 
            'medical_conditions', 'current_medications',
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relationship', 'preferred_language',
            'timezone', 'email_notifications', 'sms_notifications', 'mfa_enabled'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make the user field read-only and hide it
        if 'user' in self.fields:
            self.fields['user'].widget = forms.HiddenInput()
            self.fields['user'].required = False
        
        # Set the user display field value for existing profiles
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'user') and self.instance.user:
                # Display username and email in a user-friendly format
                user_info = f"{self.instance.user.username}"
                if self.instance.user.email:
                    user_info += f" ({self.instance.user.email})"
                if self.instance.user.first_name or self.instance.user.last_name:
                    full_name = f"{self.instance.user.first_name or ''} {self.instance.user.last_name or ''}".strip()
                    if full_name:
                        user_info += f" - {full_name}"
                
                self.fields['user_display'].initial = user_info
                self.fields['user_display'].help_text = "This field cannot be changed. The user is automatically assigned when the profile is created."
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure the user field is preserved for existing profiles
        if self.instance and self.instance.pk:
            cleaned_data['user'] = self.instance.user
        return cleaned_data
