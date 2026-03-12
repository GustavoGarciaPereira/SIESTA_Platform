# converter/urls.py

from django.urls import path
from .views import ConvertView, history_view, download_fdf, download_pseudos, delete_history, save_configuration, my_configurations, load_configuration, delete_configuration

urlpatterns = [
    path('convert/', ConvertView.as_view(), name='convert'),
    path('history/', history_view, name='converter_history'),
    path('history/<int:conv_id>/download/', download_fdf, name='download_fdf'),
    path('history/<int:conv_id>/delete/', delete_history, name='delete_history'),
    path('download/fdf/<int:conv_id>/', download_fdf, name='download_fdf_legacy'),
    path('download/pseudos/<int:conv_id>/', download_pseudos, name='download_pseudos'),
    path('config/save/', save_configuration, name='save_configuration'),
    path('config/my/', my_configurations, name='my_configurations'),
    path('config/load/<int:config_id>/', load_configuration, name='load_configuration'),
    path('config/delete/<int:config_id>/', delete_configuration, name='delete_configuration'),
]
