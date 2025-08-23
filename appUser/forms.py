from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email'),
            'autocomplete': 'email'
        }),
        validators=[validate_email]
    )
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create password'),
            'autocomplete': 'new-password'
        }),
        help_text=_("Your password must contain at least 8 characters.")
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Repeat password'),
            'autocomplete': 'new-password'
        }),
        help_text=_("Enter the same password as before, for verification.")
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords don't match"))

        return password2


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_("First name"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First name')
        })
    )
    last_name = forms.CharField(
        label=_("Last name"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last name')
        })
    )
    avatar = forms.ImageField(
        label=_("Avatar"),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )
    language = forms.ChoiceField(
        label=_("Language"),
        choices=[('ru', 'Русский'), ('en', 'English')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    timezone = forms.ChoiceField(
        label=_("Timezone"),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'avatar', 'language', 'timezone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['timezone'].choices = self.get_timezone_choices()

    def get_timezone_choices(self):
        import pytz
        timezones = []
        for tz in pytz.all_timezones:
            timezones.append((tz, tz))
        return timezones

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:  # 2MB limit
                raise ValidationError(_("Avatar file size should not exceed 2MB."))
            if not avatar.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError(_("Only JPG/JPEG/PNG files are allowed."))
        return avatar
