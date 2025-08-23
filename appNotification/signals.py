from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from .models import Response, Post, News, Subscription
from appUser.models import UserActionLog
import datetime


@receiver(post_save, sender=Response)
def notify_post_author_on_response(sender, instance, created, **kwargs):
    if created:
        subject = _('New response to your post')
        message = render_to_string('appNotification/emails/response_created.txt', {
            'post': instance.post,
            'response': instance,
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.post.author.email],
            fail_silently=False,
        )

        # Log the action
        UserActionLog.objects.create(
            user=instance.author,
            action=f"Created response to post {instance.post.id}",
        )


@receiver(post_save, sender=Response)
def notify_response_author_on_accept(sender, instance, **kwargs):
    if instance.is_accepted and instance.tracker.has_changed('is_accepted'):
        subject = _('Your response was accepted')
        message = render_to_string('appNotification/emails/response_accepted.txt', {
            'post': instance.post,
            'response': instance,
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.author.email],
            fail_silently=False,
        )

        # Log the action
        UserActionLog.objects.create(
            user=instance.post.author,
            action=f"Accepted response {instance.id} to post {instance.post.id}",
        )


@receiver(m2m_changed, sender=Post.subscribers.through)
def notify_on_post_subscription(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_pk in pk_set:
            user = instance.__class__.subscribers.through.objects.get(pk=user_pk).customuser
            subject = _('Subscription confirmation')
            message = render_to_string('appNotification/emails/post_subscription.txt', {
                'post': instance,
                'user': user,
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # Log the action
            UserActionLog.objects.create(
                user=user,
                action=f"Subscribed to post {instance.id}",
            )


@receiver(m2m_changed, sender=News.subscribers.through)
def notify_on_news_subscription(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_pk in pk_set:
            user = instance.__class__.subscribers.through.objects.get(pk=user_pk).customuser
            subject = _('News subscription confirmation')
            message = render_to_string('appNotification/emails/news_subscription.txt', {
                'news': instance,
                'user': user,
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # Log the action
            UserActionLog.objects.create(
                user=user,
                action=f"Subscribed to news {instance.id}",
            )


@receiver(post_save, sender=Subscription)
def notify_on_category_subscription(sender, instance, created, **kwargs):
    if created and instance.category:
        subject = _('Category subscription confirmation')
        message = render_to_string('appNotification/emails/category_subscription.txt', {
            'category': instance.category,
            'user': instance.user,
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=False,
        )

        # Log the action
        UserActionLog.objects.create(
            user=instance.user,
            action=f"Subscribed to category {instance.category.name}",
        )
