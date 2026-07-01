"""Admin do app visualizer."""

from django.contrib import admin

from .models import OutFile


@admin.register(OutFile)
class OutFileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "system_name", "atom_count", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("system_name", "user__username")
    readonly_fields = ("uploaded_at", "atom_count")
    date_hierarchy = "uploaded_at"
