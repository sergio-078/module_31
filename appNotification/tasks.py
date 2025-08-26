from celery import shared_task
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Post, News, Subscription
from appUser.models import UserActionLog
import datetime


@shared_task
def send_weekly_newsletter():
    # Calculate the date range for the past week
    end_date = timezone.now()
    start_date = end_date - datetime.timedelta(days=7)

    # Get all news from the past week
    weekly_news = News.objects.filter(created_at__range=(start_date, end_date))

    if weekly_news.exists():
        # Get all users subscribed to news
        subscriptions = Subscription.objects.filter(news=True).select_related('user')

        for subscription in subscriptions:
            # Prepare email content
            subject = _('Weekly news digest from our portal')
            message = render_to_string('appNotification/emails/weekly_news.txt', {
                'news': weekly_news,
                'user': subscription.user,
                'start_date': start_date,
                'end_date': end_date,
            })

            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [subscription.user.email],
                fail_silently=False,
            )

            # Log the action
            UserActionLog.objects.create(
                user=subscription.user,
                action="Received weekly news digest",
            )


@shared_task
def send_weekly_posts_digest():
    # Calculate the date range for the past week
    end_date = timezone.now()
    start_date = end_date - datetime.timedelta(days=7)

    # Get all categories with subscriptions
    categories = Subscription.objects.exclude(category=None).values_list('category', flat=True).distinct()

    for category_id in categories:
        # Get posts from this category in the past week
        weekly_posts = Post.objects.filter(
            category=category_id,
            created_at__range=(start_date, end_date)
        )

        if weekly_posts.exists():
            # Get all users subscribed to this category
            subscriptions = Subscription.objects.filter(category_id=category_id).select_related('user')

            for subscription in subscriptions:
                # Prepare email content
                subject = _('Weekly posts digest in your subscribed category')
                message = render_to_string('appNotification/emails/weekly_posts.txt', {
                    'posts': weekly_posts,
                    'user': subscription.user,
                    'category': subscription.category,
                    'start_date': start_date,
                    'end_date': end_date,
                })

                # Send email
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [subscription.user.email],
                    fail_silently=False,
                )

                # Log the action
                UserActionLog.objects.create(
                    user=subscription.user,
                    action=f"Received weekly posts digest for category {subscription.category.name}",
                )


def send_weekly_category_digest():
    # Рассылка по категориям объявлений
    categories = Category.objects.all()

    for category in categories:
        # Получаем посты за последнюю неделю в этой категории
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        weekly_posts = Post.objects.filter(
            category=category.name,  # Или category=category, в зависимости от модели
            created_at__range=(start_date, end_date)
        )

        if weekly_posts.exists():
            # Получаем подписчиков этой категории
            subscriptions = Subscription.objects.filter(category=category)

            for subscription in subscriptions:
                # Отправляем email каждому подписчику
                subject = _(f'Weekly digest for {category.name}')
                message = render_to_string('appNotification/emails/weekly_category_digest.txt', {
                    'posts': weekly_posts,
                    'user': subscription.user,
                    'category': category,
                    'start_date': start_date,
                    'end_date': end_date,
                })

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [subscription.user.email],
                    fail_silently=False,
                )
