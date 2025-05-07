from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import User

class UserRegistrationForm(UserCreationForm):
    """Form for registering a new user with custom fields"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email already exists.'))
        return email

class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_id = self.instance.id
        
        # Check if email exists but exclude current user
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            raise forms.ValidationError(_('A user with that email already exists.'))
        return email

class CustomUserChangeForm(UserChangeForm):
    """Admin form for changing user information"""
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'is_active', 'is_staff')
