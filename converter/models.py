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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='conversions', db_column='user_id')
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
        unique_together = [['user', 'name']]


class Pseudopotential(models.Model):
    """Pseudopotencial disponível para download, gerenciável pelo admin.

    Attributes:
        symbol (str): Símbolo químico do elemento (ex: C, H, O)
        functional (str): Funcional de troca-correlação do arquivo (ex: lda)
        file (FileField): Arquivo .psf armazenado em media/pseudos/
        description (str): Descrição opcional
        is_active (bool): Se o pseudopotencial pode ser usado nos downloads
        uploaded_at (datetime): Data/hora do cadastro
    """

    symbol = models.CharField(max_length=3)
    functional = models.CharField(max_length=10, default='lda')
    file = models.FileField(upload_to='pseudos/')
    description = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'converter_pseudopotential'
        unique_together = [['symbol', 'functional']]
        ordering = ['symbol', 'functional']

    def __str__(self):
        return f'{self.symbol}.{self.functional}'


class SimulationPreset(models.Model):
    """Preset global de parâmetros SIESTA, gerenciado pelo admin.

    Attributes:
        name (str): Nome exibido no seletor do conversor
        description (str): Descrição opcional
        parameters (JSONField): Valores dos campos do SIESTAParametersForm
        is_active (bool): Se o preset aparece no conversor
        sort_order (int): Ordem de exibição
        created_at/updated_at (datetime): Controle de auditoria
    """

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, default='')
    parameters = models.JSONField()
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'converter_simulationpreset'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name
