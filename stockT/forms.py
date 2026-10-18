"""Forms for the stockT application."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import ContactInfo, StockUsage, UserComment

User = get_user_model()


class RegisterForm(UserCreationForm):
    """One-time workspace setup form: the first registrant becomes Superadmin."""

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'clock_number', 'department', 'phone_number',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. jsmith', 'autofocus': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@company.com'}),
            'clock_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digits only'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.setdefault('class', 'form-control')
        self.fields['password2'].widget.attrs.setdefault('class', 'form-control')

    def clean_clock_number(self):
        return _validate_clock_number(self.cleaned_data.get('clock_number'))


def _validate_clock_number(clock_number):
    clock_number = (clock_number or '').strip()
    if not clock_number:
        raise forms.ValidationError('A clock number is required.')
    if not clock_number.isdigit():
        raise forms.ValidationError('Clock number must contain digits only.')
    if User.objects.filter(clock_number=clock_number).exists():
        raise forms.ValidationError('This clock number is already registered.')
    return clock_number


class AddUserForm(UserCreationForm):
    """Form used by the Superadmin/admin to add a person to the workspace."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'clock_number', 'department', 'phone_number', 'role',
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.setdefault('class', 'form-control')
        self.fields['password2'].widget.attrs.setdefault('class', 'form-control')

    def clean_clock_number(self):
        return _validate_clock_number(self.cleaned_data.get('clock_number'))


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

    def clean_clock_number(self):
        clock_number = (self.cleaned_data.get('clock_number') or '').strip()
        if clock_number and not clock_number.isdigit():
            raise forms.ValidationError('Clock number must contain digits only.')
        if clock_number and User.objects.filter(clock_number=clock_number).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This clock number is already registered.')
        return clock_number


class LimitedEditUserForm(EditUserForm):
    """
    Manager-limited edit form.

    Excludes role/is_staff so a manager can never escalate their own (or
    anyone's) privileges by posting privileged fields.
    """

    class Meta(EditUserForm.Meta):
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'clock_number', 'department', 'phone_number', 'is_active',
        )
