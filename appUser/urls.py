from django.contrib.auth import views as auth_views
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    # Auth
    path('login/', LoginView.as_view(
        template_name='login.html',
        extra_context={'title': _('Login')}
    ), name='login'),

    path('logout/', LogoutView.as_view(
        template_name='logout.html',
        extra_context={'title': _('Logout')}
    ), name='logout'),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify/<str:code>/', views.verify_email, name='verify_email'),
    # Восстановление пароля
    # path('password_reset/',
    #      auth_views.PasswordResetView.as_view(
    #          template_name='password_reset.html',
    #          email_template_name='password_reset_email.html',
    #          subject_template_name='password_reset_subject.txt',
    #          success_url='/user/password_reset/done/'
    #      ),
    #      name='password_reset'),

    path('password_reset/', views.custom_password_reset, name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url='/user/reset/done/'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Profile
    path('profile/', views.profile, name='profile'),
    # path('profile/update/', views.profile_update, name='profile_update'),

    # Timezone/Language
    path('set-timezone/', views.set_timezone, name='set_timezone'),
    path('set-language/', views.set_language, name='set_language'),
]
