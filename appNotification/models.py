from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinLengthValidator
from ckeditor.fields import RichTextField
import datetime

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    # slug = models.SlugField(max_length=50, unique=True)
    value = models.CharField(max_length=20, unique=True, default='None')  # соответствует значениям из CATEGORY_CHOICES
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('tanks', _('Tanks')),
        ('heals', _('Heals')),
        ('dd', _('DD')),
        ('traders', _('Traders')),
        ('guildmasters', _('Guildmasters')),
        ('questgivers', _('Questgivers')),
        ('blacksmiths', _('Blacksmiths')),
        ('tanners', _('Tanners')),
        ('potionmakers', _('Potionmakers')),
        ('spellmasters', _('Spellmasters')),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255, validators=[MinLengthValidator(5)])
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscribers = models.ManyToManyField(User, related_name='subscribed_posts', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return f"{self.title} by {self.author.email}"

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})


class Response(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='responses')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField(validators=[MinLengthValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Response')
        verbose_name_plural = _('Responses')

    def __str__(self):
        return f"Response to {self.post.title} by {self.author.email}"


class News(models.Model):
    title = models.CharField(max_length=255, validators=[MinLengthValidator(5)])
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscribers = models.ManyToManyField(User, related_name='subscribed_news', blank=True)
    views_count = models.PositiveIntegerField(default=0, verbose_name=_('Views count'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('News')
        verbose_name_plural = _('News')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news_detail', kwargs={'pk': self.pk})

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    news = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'category']
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

    def __str__(self):
        if self.category:
            return f"{self.user.email} subscribed to {self.category.name}"
        elif self.news:
            return f"{self.user.email} subscribed to news"
        return f"{self.user.email} subscription"

    @classmethod
    def get_user_subscriptions(cls, user):
        """Получить все подписки пользователя"""
        return cls.objects.filter(user=user).select_related('category')

    @classmethod
    def is_user_subscribed_to_news(cls, user):
        """Проверить подписку на новости"""
        return cls.objects.filter(user=user, news=True).exists()

    @classmethod
    def is_user_subscribed_to_category(cls, user, category):
        """Проверить подписку на категорию"""
        return cls.objects.filter(user=user, category=category).exists()
