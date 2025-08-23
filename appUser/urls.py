from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    # Auth
    path('login/', LoginView.as_view(
        template_name='appUser/login.html',
        extra_context={'title': _('Login')}
    ), name='login'),

    path('logout/', LogoutView.as_view(
        template_name='appUser/logout.html',
        extra_context={'title': _('Logout')}
    ), name='logout'),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify/<str:code>/', views.verify_email, name='verify_email'),

    # Profile
    path('profile/', views.profile, name='profile'),
    # path('profile/update/', views.profile_update, name='profile_update'),

    # Timezone/Language
    path('set-timezone/', views.set_timezone, name='set_timezone'),
    path('set-language/', views.set_language, name='set_language'),
]
