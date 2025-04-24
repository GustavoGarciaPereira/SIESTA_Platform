# converter/urls.py

from django.urls import path
from .views import ConvertView

from .views import ConvertView, HomeView, SignupView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', HomeView.as_view(), name='home'), # Página home
    path('convert/', ConvertView.as_view(), name='convert'),  # Página inicial
    path('login/', auth_views.LoginView.as_view(template_name='converter/login.html'), name='login'),

    # URLs para recuperação de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='converter/password_reset_form.html',
        email_template_name='converter/password_reset_email.html',
        subject_template_name='converter/password_reset_subject.txt',
        success_url='/password_reset/done/'
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='converter/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='converter/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='converter/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),  # View de criação de conta
    # path('login/', LoginView.as_view(), name='login'),  # View de login
    # path('signup/', SignupView.as_view(), name='signup'),  # View de criação de conta
]