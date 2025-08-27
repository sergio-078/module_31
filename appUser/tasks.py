from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import EmailVerification, CustomUser


@shared_task
def clean_expired_verifications():
    """Очистка просроченных верификаций и пользователей"""
    expired_time = timezone.now() - timedelta(hours=24)
    expired_verifications = EmailVerification.objects.filter(
        created_at__lt=expired_time
    )

    count = 0
    for verification in expired_verifications:
        user = verification.user
        verification.delete()
        user.delete()
        count += 1

    return f'Cleaned {count} expired registrations'
