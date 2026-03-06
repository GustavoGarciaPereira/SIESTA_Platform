from django.db import models
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    """Model para arquivos enviados no aplicativo de conversão.
    
    Attributes:
        user (ForeignKey): Usuário que enviou o arquivo
        file (FileField): Arquivo enviado
        original_name (str): Nome original do arquivo
        file_type (str): Tipo do arquivo (ex: 'xyz')
        size (int): Tamanho do arquivo em bytes
        checksum (str): Checksum SHA-256 do conteúdo do arquivo
        upload_date (datetime): Data e hora do upload
        is_temp (bool): Indica se é um arquivo temporário
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', db_column='user_id')
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    size = models.IntegerField()
    checksum = models.CharField(max_length=64)
    upload_date = models.DateTimeField()
    is_temp = models.BooleanField()

    class Meta:
        """Metadados do modelo UploadedFile."""
        db_table = 'converter_uploadedfile'
        managed = False  # Tabela já existe, Django não deve gerenciá-la


class ConversionHistory(models.Model):
    """Model para histórico de conversões.
    
    Attributes:
        user (ForeignKey): Usuário que realizou a conversão
        uploaded_file (ForeignKey): Arquivo enviado relacionado (opcional)
        original_filename (str): Nome original do arquivo XYZ
        system_name (str): Nome do sistema para o arquivo FDF
        fdf_content (str): Conteúdo do arquivo FDF gerado
        parameters (JSONField): Parâmetros de simulação SIESTA usados
        conversion_date (datetime): Data e hora do início da conversão
        completion_date (datetime): Data e hora da conclusão da conversão
        file_size (int): Tamanho do arquivo em bytes
        status (str): Status da conversão (pending, processing, completed, failed)
        error_message (str): Mensagem de erro em caso de falha
        download_count (int): Contador de downloads do arquivo FDF
    """
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
        """Metadados do modelo ConversionHistory."""
        db_table = 'converter_conversionhistory'
        managed = False  # Tabela já existe, Django não deve gerenciá-la


class SavedConfiguration(models.Model):
    """Model para configurações salvas de parâmetros SIESTA.
    
    Attributes:
        user (ForeignKey): Usuário que salvou a configuração
        name (str): Nome da configuração
        description (str): Descrição da configuração
        parameters (JSONField): Parâmetros de simulação SIESTA salvos
        is_default (bool): Indica se é a configuração padrão do usuário
        created_at (datetime): Data e hora de criação
        last_used (datetime): Data e hora do último uso
        use_count (int): Contador de usos da configuração
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_configs', db_column='user_id')
    name = models.CharField(max_length=100)
    description = models.TextField()
    parameters = models.JSONField()
    is_default = models.BooleanField()
    created_at = models.DateTimeField()
    last_used = models.DateTimeField()
    use_count = models.IntegerField()

    class Meta:
        """Metadados do modelo SavedConfiguration."""
        db_table = 'converter_savedconfiguration'
        managed = False  # Tabela já existe, Django não deve gerenciá-la
        unique_together = [['user', 'name']]
