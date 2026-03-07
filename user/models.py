from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Informações estendidas do perfil do usuário.
    
    Attributes:
        user (OneToOneField): Usuário associado ao perfil
        institution (str): Instituição do usuário
        research_area (str): Área de pesquisa do usuário
        profile_picture (ImageField): Foto de perfil (opcional)
        email_verified (bool): Indica se o e-mail foi verificado
        created_at (datetime): Data e hora de criação do perfil
        updated_at (datetime): Data e hora da última atualização
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', db_column='user_id')
    institution = models.CharField(max_length=200, blank=True, default='')
    research_area = models.CharField(max_length=200, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadados do modelo UserProfile."""
        db_table = 'user_userprofile'
