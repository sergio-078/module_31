# appUser/email_backends.py
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.utils.translation import gettext_lazy as _


class DebugEmailBackend(ConsoleEmailBackend):
    def send_messages(self, email_messages):
        results = super().send_messages(email_messages)

        # Выводим дополнительную информацию в консоль
        for message in email_messages:
            print("=" * 50)
            print("DEBUG EMAIL INFORMATION:")
            print(f"To: {message.to}")
            print(f"Subject: {message.subject}")
            print("Body:")
            print(message.body)
            print("=" * 50)

        return results