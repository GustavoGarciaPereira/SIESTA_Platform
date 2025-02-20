# converter/urls.py

from django.urls import path
from .views import ConvertView

from .views import ConvertView, HomeView, SignupView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', HomeView.as_view(), name='home'), # Página home
    path('convert/', ConvertView.as_view(), name='convert'),  # Página inicial
    path('login/', auth_views.LoginView.as_view(template_name='converter/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),  # View de criação de conta
    # path('login/', LoginView.as_view(), name='login'),  # View de login
    # path('signup/', SignupView.as_view(), name='signup'),  # View de criação de conta
]