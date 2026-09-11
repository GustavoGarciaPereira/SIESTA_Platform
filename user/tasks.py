"""Tarefas assíncronas do app user."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(name='user.send_contact_email')
def send_contact_email(name, email, subject, message):
    """Envia a mensagem do formulário de contato por e-mail."""
    send_mail(
        subject=f"[SIESTA Platform] {subject}",
        message=f"Nome: {name}\nE-mail: {email}\n\n{message}",
        from_email=settings.DEFAULT_FROM_EMAIL or 'no-reply@siesta-platform',
        recipient_list=[settings.CONTACT_EMAIL],
        fail_silently=False,
    )
