from django.db import models
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    """Model for uploaded files in the converter app."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', db_column='user_id')
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    size = models.IntegerField()
    checksum = models.CharField(max_length=64)
    upload_date = models.DateTimeField()
    is_temp = models.BooleanField()

    class Meta:
        db_table = 'converter_uploadedfile'
        managed = False  # Table already exists, Django shouldn't manage it


class ConversionHistory(models.Model):
    """Model for tracking conversion history."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversions', db_column='user_id')
    uploaded_file = models.ForeignKey('UploadedFile', on_delete=models.SET_NULL, null=True, blank=True, db_column='uploaded_file_id')
    original_filename = models.CharField(max_length=255)
    system_name = models.CharField(max_length=255)
    fdf_content = models.TextField()
    parameters = models.JSONField()
    conversion_date = models.DateTimeField()
    completion_date = models.DateTimeField(null=True, blank=True)
    file_size = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField()
    download_count = models.IntegerField()

    class Meta:
        db_table = 'converter_conversionhistory'
        managed = False  # Table already exists, Django shouldn't manage it


class SavedConfiguration(models.Model):
    """Model for saved configurations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_configs', db_column='user_id')
    name = models.CharField(max_length=100)
    description = models.TextField()
    parameters = models.JSONField()
    is_default = models.BooleanField()
    created_at = models.DateTimeField()
    last_used = models.DateTimeField()
    use_count = models.IntegerField()

    class Meta:
        db_table = 'converter_savedconfiguration'
        managed = False  # Table already exists, Django shouldn't manage it
        unique_together = [['user', 'name']]
