# converter/urls.py

from django.urls import path, reverse_lazy
from .views import ConvertView, HomeView, SignupView, AboutView, ContactView, contact_submit_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('convert/', ConvertView.as_view(), name='convert'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('contact/submit/', contact_submit_view, name='contact_submit'),
    
    # --- URLs de Autenticação e Conta ---
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='converter/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- URLs para Recuperação de Senha (com reverse_lazy) ---
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='converter/password_reset_form.html',
        email_template_name='converter/password_reset_email.html',
        subject_template_name='converter/password_reset_subject.txt',
        # CORRIGIDO: Usando o nome da URL em vez da URL fixa.
        success_url=reverse_lazy('password_reset_done') 
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='converter/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='converter/password_reset_confirm.html',
        # CORRIGIDO: Usando o nome da URL.
        success_url=reverse_lazy('converter:password_reset_complete')
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='converter/password_reset_complete.html'
    ), name='password_reset_complete'),
]