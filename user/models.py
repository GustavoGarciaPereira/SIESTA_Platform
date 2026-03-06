from django.db import models
from django.contrib.auth.models import User


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
    institution = models.CharField(max_length=200)
    research_area = models.CharField(max_length=200)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    email_verified = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        """Metadados do modelo UserProfile."""
        db_table = 'user_userprofile'
        managed = False  # Tabela já existe, Django não deve gerenciá-la
