from django.urls import path
from . import views
from .views import AboutView, ContactsView
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    # Flatpages
    path('about/', AboutView.as_view(), name='about'),
    path('contacts/', ContactsView.as_view(), name='contacts'),

    # Posts
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<int:pk>/subscribe/', views.subscribe_post, name='post_subscribe'),
    path('posts/<int:post_id>/respond/', views.ResponseCreateView.as_view(), name='response_create'),

    # Responses
    path('responses/', views.personal_cabinet, name='response_list'),
    path('responses/<int:pk>/', views.ResponseDetailView.as_view(), name='response_detail'),
    path('responses/<int:pk>/accept/', views.accept_response, name='accept_response'),
    # path('responses/<int:pk>/delete/', views.ResponseDeleteView.as_view(), name='response_delete'),
    path('posts/<int:post_id>/respond/', views.ResponseCreateView.as_view(), name='response_create'),

    # News
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('news/create/', views.NewsCreateView.as_view(), name='news_create'),
    path('news/<int:pk>/edit/', views.NewsUpdateView.as_view(), name='news_edit'),
    path('news/<int:pk>/delete/', views.NewsDeleteView.as_view(), name='news_delete'),
    path('news/subscribe/', views.subscribe_news, name='news_subscribe'),

    # Categories
    # path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/subscribe/', views.subscribe_category, name='category_subscribe'),

    # Personal cabinet
    path('cabinet/', views.personal_cabinet, name='personal_cabinet'),
]
