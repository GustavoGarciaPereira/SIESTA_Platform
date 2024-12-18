# converter/urls.py

from django.urls import path
from .views import ConvertView

urlpatterns = [
    path('', ConvertView.as_view(), name='convert'),
]
