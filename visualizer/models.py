from django.conf import settings
from django.db import models


class OutFile(models.Model):
    """Arquivo de saída (.out) de simulação SIESTA.

    Armazena o arquivo enviado pelo usuário para visualização 3D
    do campo elétrico e geometria atômica.

    Attributes:
        user: Usuário que enviou o arquivo
        file: Arquivo .out armazenado
        system_name: Nome opcional do sistema (extraído do .out)
        atom_count: Número de átomos detectados (preenchido na view)
        uploaded_at: Data/hora do upload
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="out_files",
        db_column="user_id",
    )
    file = models.FileField(upload_to="out_files/")
    system_name = models.CharField(max_length=255, blank=True, default="")
    atom_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visualizer_outfile"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.system_name or 'Unknown'} ({self.atom_count} atoms)"
