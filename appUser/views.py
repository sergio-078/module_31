from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import secrets
import pytz

from .models import CustomUser, EmailVerification, UserActionLog
from .forms import RegistrationForm, ProfileForm


class RegisterView(View):
    template_name = 'appUser/register.html'

    def get(self, request):
        form = RegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Создаем и отправляем код верификации
            verification = EmailVerification.create_verification(user)
            verification.send_verification_email()

            messages.success(request, _('Registration successful! Please check your email for verification.'))
            UserActionLog.objects.create(
                user=user,
                action="Registered new account",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('login')
        return render(request, self.template_name, {'form': form})


def verify_email(request, code):
    try:
        verification = EmailVerification.objects.get(code=code)
        if verification.is_valid():
            user = verification.user
            user.is_active = True
            user.save()
            verification.delete()
            messages.success(request, _('Email verified successfully! You can now log in.'))
            UserActionLog.objects.create(
                user=user,
                action="Verified email",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('login')
        else:
            messages.error(request, _('Verification link has expired.'))
            return redirect('register')
    except EmailVerification.DoesNotExist:
        messages.error(request, _('Invalid verification link.'))
        return redirect('register')


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated successfully!'))
            UserActionLog.objects.create(
                user=user,
                action="Updated profile",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('profile')
    else:
        form = ProfileForm(instance=user)

    return render(request, 'appUser/profile.html', {
        'form': form,
        'timezones': pytz.all_timezones
    })


@login_required
def set_timezone(request):
    if request.method == 'POST':
        timezone = request.POST.get('timezone')
        if timezone in pytz.all_timezones:
            request.session['django_timezone'] = timezone
            request.user.timezone = timezone
            request.user.save()
            messages.success(request, _('Timezone updated successfully!'))
            UserActionLog.objects.create(
                user=request.user,
                action=f"Changed timezone to {timezone}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
        else:
            messages.error(request, _('Invalid timezone.'))
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def set_language(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        if language in [lang[0] for lang in settings.LANGUAGES]:
            request.session['django_language'] = language
            request.user.language = language
            request.user.save()
            messages.success(request, _('Language changed successfully!'))
            UserActionLog.objects.create(
                user=request.user,
                action=f"Changed language to {language}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
        else:
            messages.error(request, _('Invalid language.'))
    return redirect(request.META.get('HTTP_REFERER', 'home'))
