"""Rotas da API REST v1."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ConversionHistoryViewSet,
    OutFileViewSet,
    SavedConfigurationViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register('conversions', ConversionHistoryViewSet, basename='conversions')
router.register('configurations', SavedConfigurationViewSet, basename='configurations')
router.register('out-files', OutFileViewSet, basename='out-files')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
