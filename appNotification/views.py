from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import Post, Response, News, Category, Subscription
from .forms import PostForm, ResponseForm, NewsForm
from appUser.models import UserActionLog, CustomUser


class AboutView(TemplateView):
    template_name = 'about.html'  # Использует ваш существующий шаблон

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('About Us')
        context['content'] = _('This is the about page content.')
        return context


class ContactsView(TemplateView):
    template_name = 'contacts.html'  # Использует ваш существующий шаблон

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Contacts')
        context['content'] = _('Contact information here.')
        return context


class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('author').order_by('-created_at')

        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Поиск
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['category_choices'] = Post.CATEGORY_CHOICES
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['responses'] = self.object.responses.filter(is_accepted=True).select_related('author')
        context['response_form'] = ResponseForm()

        if self.request.user.is_authenticated:
            context['is_subscribed'] = self.object.subscribers.filter(id=self.request.user.id).exists()

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post_create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # Логируем создание поста
        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Created post {self.object.id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        messages.success(self.request, _('Post created successfully!'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем описания категорий для подсказок
        return context

    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_edit.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff

    def form_valid(self, form):
        response = super().form_valid(form)

        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Updated post {self.object.id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        messages.success(self.request, _('Post updated successfully!'))
        return response

    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Deleted post {self.get_object().id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        messages.success(self.request, _('Post deleted successfully!'))
        return super().delete(request, *args, **kwargs)


class ResponseCreateView(LoginRequiredMixin, CreateView):
    model = Response
    form_class = ResponseForm
    template_name = 'response_create.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        response = super().form_valid(form)

        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Created response to post {post.id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        messages.success(self.request, _('Response created successfully!'))
        return response

    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.kwargs['post_id']})


class ResponseDetailView(LoginRequiredMixin, DetailView):
    model = Response
    template_name = 'response_detail.html'
    context_object_name = 'response'

    def get_queryset(self):
        # Показываем отклик только если:
        # 1. Это автор отклика
        # 2. Это автор объявления
        # 3. Отклик был принят (виден всем)
        return super().get_queryset().select_related('author', 'post__author').filter(
            Q(author=self.request.user) |
            Q(post__author=self.request.user) |
            Q(is_accepted=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        response = self.object
        context['can_edit'] = response.author == self.request.user
        context['can_accept'] = (response.post.author == self.request.user
                                 and not response.is_accepted)
        context['can_delete'] = (response.post.author == self.request.user
                                 or response.author == self.request.user)

        # Логируем просмотр
        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Viewed response {response.id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        return context

@login_required
def accept_response(request, pk):
    response = get_object_or_404(Response, pk=pk)

    if request.user == response.post.author:
        response.is_accepted = True
        response.save()

        UserActionLog.objects.create(
            user=request.user,
            action=f"Accepted response {response.id}",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, _('Response accepted!'))
    else:
        messages.error(request, _('You are not authorized to perform this action.'))

    return redirect('post_detail', pk=response.post.pk)


@login_required
def subscribe_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.subscribers.filter(id=request.user.id).exists():
        post.subscribers.remove(request.user)
        messages.success(request, _('You have unsubscribed from this post.'))
    else:
        post.subscribers.add(request.user)
        messages.success(request, _('You have subscribed to this post.'))

    UserActionLog.objects.create(
        user=request.user,
        action=f"Toggled subscription to post {post.id}",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return redirect('post_detail', pk=post.pk)


@login_required
def personal_cabinet(request):
    # Обработка POST запросов для подписки/отписки
    if request.method == 'POST':
        # Подписка/отписка на новости
        if 'news_subscribe' in request.POST:
            return handle_news_subscription(request)

        # Подписка/отписка на категории
        elif 'category_subscribe' in request.POST:
            return handle_category_subscription(request)

    # GET запрос - отображение личного кабинета
    return render_personal_cabinet(request)


def handle_news_subscription(request):
    """Обработка подписки/отписки на новости"""
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        category=None,
        defaults={'news': True}
    )

    if not created:
        subscription.delete()
        messages.success(request, _('Unsubscribed from news'))
        action = "Unsubscribed from news"
    else:
        messages.success(request, _('Subscribed to news'))
        action = "Subscribed to news"

    UserActionLog.objects.create(
        user=request.user,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return redirect('personal_cabinet')


def handle_category_subscription(request):
    """Обработка подписки/отписки на категории"""
    category_value = request.POST.get('category_value')
    if category_value:
        try:
            category = Category.objects.get(value=category_value)
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                category=category,
                defaults={'news': False}
            )

            if not created:
                subscription.delete()
                messages.success(request, _(f'Unsubscribed from {category.name}'))
                action = f"Unsubscribed from category {category.name}"
            else:
                messages.success(request, _(f'Subscribed to {category.name}'))
                action = f"Subscribed to category {category.name}"

            UserActionLog.objects.create(
                user=request.user,
                action=action,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        except Category.DoesNotExist:
            messages.error(request, _('Category not found'))

    return redirect('personal_cabinet')


def render_personal_cabinet(request):
    """Рендеринг личного кабинета"""
    # Получаем посты пользователя
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')

    # Получаем отклики пользователя
    user_responses = Response.objects.filter(author=request.user).order_by('-created_at')

    # Получаем отклики на посты пользователя
    responses_to_posts = Response.objects.filter(post__author=request.user).order_by('-created_at')

    # Фильтрация
    post_filter = request.GET.get('post_filter')
    if post_filter:
        responses_to_posts = responses_to_posts.filter(post_id=post_filter)

    status_filter = request.GET.get('status_filter')
    if status_filter == 'accepted':
        responses_to_posts = responses_to_posts.filter(is_accepted=True)
    elif status_filter == 'pending':
        responses_to_posts = responses_to_posts.filter(is_accepted=False)

    # Получаем все подписки пользователя
    subscriptions = Subscription.objects.filter(user=request.user).select_related('category')
    news_subscribed = Subscription.objects.filter(user=request.user, news=True).exists()

    # Получаем ВСЕ категории
    all_categories = Category.objects.all()

    # Помечаем, подписан ли пользователь на каждую категорию
    categories_with_status = []
    for category in all_categories:
        is_subscribed = Subscription.objects.filter(
            user=request.user,
            category=category
        ).exists()

        categories_with_status.append({
            'category': category,
            'is_subscribed': is_subscribed
        })

    context = {
        'user_posts': user_posts,
        'user_responses': user_responses,
        'responses_to_posts': responses_to_posts,
        'subscriptions': subscriptions,
        'news_subscribed': news_subscribed,
        'categories_with_status': categories_with_status,
        'post_filter': post_filter,
        'status_filter': status_filter,
    }

    UserActionLog.objects.create(
        user=request.user,
        action="Accessed personal cabinet",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return render(request, 'lk.html', context)


@login_required
def subscribe_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    # Проверяем, есть ли уже подписка
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        category=category,
        defaults={'news': False}
    )

    if not created:
        # Если подписка уже существует - удаляем ее (отписка)
        subscription.delete()
        messages.success(request, _(f'Unsubscribed from category: {category.name}'))
        action = f"Unsubscribed from category {category.name}"
    else:
        messages.success(request, _(f'Subscribed to category: {category.name}'))
        action = f"Subscribed to category {category.name}"

    # Логируем действие
    UserActionLog.objects.create(
        user=request.user,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    # ВАЖНО: возвращаем redirect
    return redirect('personal_cabinet')


@login_required
def subscribe_news(request):
    # Проверяем, есть ли уже подписка на новости
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        category=None,
        defaults={'news': True}
    )

    if not created:
        # Если подписка уже существует - удаляем ее (отписка)
        subscription.delete()
        messages.success(request, _('Unsubscribed from news'))
        action = "Unsubscribed from news"
    else:
        messages.success(request, _('Subscribed to news'))
        action = "Subscribed to news"

    # Логируем действие
    UserActionLog.objects.create(
        user=request.user,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return redirect('personal_cabinet')


# Аналогичные классы для News (NewsListView, NewsDetailView, NewsCreateView и т.д.)
class NewsListView(ListView):
    model = News
    template_name = 'news_list.html'
    context_object_name = 'news'
    paginate_by = 10
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_subscribed'] = Subscription.objects.filter(
                user=self.request.user,
                news=True
            ).exists()
        return context


class NewsDetailView(DetailView):
    model = News
    template_name = 'news_detail.html'
    context_object_name = 'news'

    def get_object(self, queryset=None):
        news = super().get_object(queryset)

        # Увеличиваем счетчик просмотров
        self.increment_views_count(news)

        return news

    def increment_views_count(self, news):
        """Логика подсчета просмотров с защитой от накрутки"""
        try:
            # Получаем или создаем ключ для сессии
            session_key = f'news_{news.id}_viewed'

            # Проверяем, не просматривал ли пользователь эту новость в текущей сессии
            if not self.request.session.get(session_key, False):
                # Увеличиваем счетчик
                news.increment_views()

                # Помечаем новость как просмотренную в этой сессии
                self.request.session[session_key] = True

                # Логируем просмотр
                if self.request.user.is_authenticated:
                    UserActionLog.objects.create(
                        user=self.request.user,
                        action=f"Viewed news {news.id}",
                        ip_address=self.request.META.get('REMOTE_ADDR')
                    )
                else:
                    UserActionLog.objects.create(
                        user=None,
                        action=f"Viewed news {news.id} (anonymous)",
                        ip_address=self.request.META.get('REMOTE_ADDR')
                    )

        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Error incrementing views count: {e}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Проверка подписки
        if self.request.user.is_authenticated:
            context['is_subscribed'] = Subscription.objects.filter(
                user=self.request.user,
                news=True
            ).exists()

        # Навигация между новостями
        context['previous_news'] = News.objects.filter(
            created_at__lt=self.object.created_at
        ).order_by('-created_at').first()

        context['next_news'] = News.objects.filter(
            created_at__gt=self.object.created_at
        ).order_by('created_at').first()

        # Популярные новости (дополнительно)
        context['popular_news'] = News.objects.order_by('-views_count')[:5]

        return context


class NewsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = 'news_create.html'

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        response = super().form_valid(form)
        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Created news {self.object.id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        messages.success(self.request, _('News created successfully!'))
        return response

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})

    def handle_no_permission(self):
        messages.error(self.request, _('You do not have permission to create news.'))
        return redirect('news_list')


class NewsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'news_edit.html'

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        response = super().form_valid(form)
        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Updated news {self.object.id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        messages.success(self.request, _('News updated successfully!'))
        return response

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class NewsDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = News
    template_name = 'news_delete.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        UserActionLog.objects.create(
            user=self.request.user,
            action=f"Deleted news {self.get_object().id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        messages.success(self.request, _('News deleted successfully!'))
        return super().delete(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем новости и объявления, отсортированные по дате создания
        latest_news = News.objects.all().order_by('-created_at')[:6]
        latest_posts = Post.objects.all().select_related('author').order_by('-created_at')[:6]

        # Комбинированный список для вкладки "All Content"
        combined_content = []
        for news in latest_news:
            combined_content.append({
                'type': 'news',
                'id': news.id,
                'title': news.title,
                'content': news.content,
                'created_at': news.created_at,
                'get_category_display': None
            })

        for post in latest_posts:
            combined_content.append({
                'type': 'post',
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at,
                'get_category_display': post.get_category_display()
            })

        # Сортируем комбинированный список по дате создания (новые сначала)
        combined_content.sort(key=lambda x: x['created_at'], reverse=True)

        # Статистика
        context.update({
            'latest_news': latest_news,
            'latest_posts': latest_posts,
            'combined_content': combined_content[:10],  # Ограничиваем количество
            'news_count': News.objects.count(),
            'posts_count': Post.objects.count(),
            'users_count': CustomUser.objects.count(),
        })

        return context
