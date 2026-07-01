"""URLs do app visualizer."""

from django.urls import path

from . import views

app_name = "visualizer"

urlpatterns = [
    path("upload/", views.upload_out, name="upload_out"),
    path("<int:out_id>/", views.visualize_out, name="visualize"),
    path("<int:out_id>/content/", views.out_content, name="out_content"),
    path("<int:out_id>/atoms/", views.out_atoms_json, name="out_atoms"),
]
