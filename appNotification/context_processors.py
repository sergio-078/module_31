from django.utils.translation import gettext_lazy as _
from .models import Category


def categories(request):
    """
    Контекст-процессор для добавления категорий во все шаблоны
    """
    return {
        'categories': Category.objects.all(),
        'category_choices': [
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
    }


def navigation_data(request):
    """
    Дополнительный контекст-процессор для навигационных данных
    """
    from .models import Post, News

    return {
        'recent_posts': Post.objects.order_by('-created_at')[:5],
        'recent_news': News.objects.order_by('-created_at')[:3],
        'posts_count': Post.objects.count(),
        'news_count': News.objects.count(),
    }
