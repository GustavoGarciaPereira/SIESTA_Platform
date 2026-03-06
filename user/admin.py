from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'research_area', 'email_verified', 'created_at', 'email_verified','created_at'
,'updated_at')
    list_filter = ('email_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'institution', 'research_area')
    date_hierarchy = 'created_at'