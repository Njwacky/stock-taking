"""Forms for the stockT application."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import ContactInfo, StockUsage, UserComment

User = get_user_model()


class RegisterForm(UserCreationForm):
    """Registration form including clock number validation."""

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'clock_number', 'department', 'phone_number',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'}),
            'clock_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digits only, e.g. 12345'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure password fields get the same styling as other inputs
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'At least 8 characters'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})
        # Help texts for UX
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = 'Must be at least 8 characters and not entirely numeric.'
        # Make first_name/last_name optional visually but keep model blank
        for fname in ('first_name', 'last_name', 'email', 'department', 'phone_number'):
            self.fields[fname].required = False

    def clean_clock_number(self):
        clock_number = (self.cleaned_data.get('clock_number') or '').strip()
        if not clock_number:
            raise forms.ValidationError('A clock number is required.')
        if not clock_number.isdigit():
            raise forms.ValidationError('Clock number must contain digits only.')
        if User.objects.filter(clock_number=clock_number).exists():
            raise forms.ValidationError('This clock number is already registered.')
        return clock_number


class UserCommentForm(forms.ModelForm):
    """Form for submitting user feedback."""

    class Meta:
        model = UserComment
        fields = ('category', 'subject', 'message')
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class ContactInfoForm(forms.ModelForm):
    """Form for managing footer contact information."""

    class Meta:
        model = ContactInfo
        fields = ('contact_type', 'label', 'value', 'is_active', 'order')
        widgets = {
            'contact_type': forms.Select(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class StockUsageForm(forms.ModelForm):
    """Form for logging stock usage."""

    class Meta:
        model = StockUsage
        fields = ('kit_type', 'quantity_used', 'purpose', 'feedback')
        widgets = {
            'kit_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity_used': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProfileForm(forms.ModelForm):
    """Form for updating editable profile information."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'department', 'phone_number')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EditUserForm(forms.ModelForm):
    """Admin/manager form for editing user accounts."""

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'clock_number', 'department', 'phone_number', 'role',
            'is_active', 'is_staff',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'clock_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
