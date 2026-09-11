from django.contrib import admin
from .models import (
    ConversionHistory,
    Pseudopotential,
    SavedConfiguration,
    SimulationPreset,
    UploadedFile,
)


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


@admin.register(Pseudopotential)
class PseudopotentialAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'functional', 'file', 'is_active', 'uploaded_at')
    list_filter = ('is_active', 'functional', 'uploaded_at')
    search_fields = ('symbol', 'description', 'file')
    readonly_fields = ('uploaded_at',)
    date_hierarchy = 'uploaded_at'


@admin.register(SimulationPreset)
class SimulationPresetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'sort_order', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active', 'sort_order')