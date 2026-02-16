from django.contrib import admin
from .models import ConversionHistory, UploadedFile, SavedConfiguration


@admin.register(ConversionHistory)
class ConversionHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'system_name', 'status', 'conversion_date', 'download_count')
    list_filter = ('status', 'conversion_date')
    search_fields = ('system_name', 'original_filename', 'user__username')
    readonly_fields = ('conversion_date', 'completion_date')
    date_hierarchy = 'conversion_date'


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'original_name', 'file_type', 'size', 'upload_date', 'is_temp')
    list_filter = ('file_type', 'is_temp', 'upload_date')
    search_fields = ('original_name', 'user__username')
    readonly_fields = ('upload_date', 'size', 'checksum')
    date_hierarchy = 'upload_date'


@admin.register(SavedConfiguration)
class SavedConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'is_default', 'created_at', 'last_used', 'use_count')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'last_used', 'use_count')
    date_hierarchy = 'created_at'