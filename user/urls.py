
from django.urls import path, reverse_lazy

from django.contrib.auth import views as auth_views

from .views import (
    AboutView,
    ContactView,
    CustomLoginView,
    HomeView,
    SignupView,
    contact_submit_view,
    profile_view,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # Página home
    path('login/', CustomLoginView.as_view(), name='login'),

    # URLs para recuperação de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='converter/password_reset_form.html',
        email_template_name='converter/password_reset_email.html',
        subject_template_name='converter/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='converter/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='converter/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='converter/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('contact/submit/', contact_submit_view, name='contact_submit'),
    path('profile/', profile_view, name='profile'),
]
