"""Configuração do Celery para o projeto."""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heparin_converter.settings')

app = Celery('heparin_converter')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
