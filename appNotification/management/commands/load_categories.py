from django.core.management.base import BaseCommand
from appNotification.models import Category, Post


class Command(BaseCommand):
    help = 'Load categories from Post.CATEGORY_CHOICES'

    def handle(self, *args, **options):
        for value, name in Post.CATEGORY_CHOICES:
            Category.objects.get_or_create(
                value=value,
                defaults={'name': name, 'description': f'Category for {name}'}
            )
        self.stdout.write(self.style.SUCCESS('Categories loaded successfully'))
