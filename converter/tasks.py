"""Tarefas assíncronas do app converter."""

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import UploadedFile


@shared_task(name='converter.cleanup_temp_files')
def cleanup_temp_files(days=30):
    """Remove arquivos temporários (is_temp) mais antigos que `days` dias.

    Returns:
        int: quantidade de registros removidos
    """
    cutoff = timezone.now() - timedelta(days=days)
    queryset = UploadedFile.objects.filter(is_temp=True, upload_date__lt=cutoff)

    removed = 0
    for uploaded in queryset:
        if uploaded.file:
            uploaded.file.delete(save=False)
        uploaded.delete()
        removed += 1
    return removed
