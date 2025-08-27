from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appUser.models import EmailVerification, CustomUser


class Command(BaseCommand):
    help = 'Clean expired email verifications and associated users'

    def handle(self, *args, **options):
        # Находим просроченные верификации
        expired_time = timezone.now() - timedelta(hours=24)
        expired_verifications = EmailVerification.objects.filter(
            created_at__lt=expired_time
        )

        count = 0
        for verification in expired_verifications:
            # Удаляем пользователя и верификацию
            user = verification.user
            email = user.email
            verification.delete()
            user.delete()
            count += 1

            self.stdout.write(f'Removed expired registration for: {email}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned {count} expired registrations')
        )