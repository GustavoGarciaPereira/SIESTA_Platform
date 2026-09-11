"""Views da API REST (DRF) — dados isolados por usuário."""

from django.utils import timezone
from rest_framework import viewsets

from converter.models import ConversionHistory, SavedConfiguration
from visualizer.models import OutFile
from visualizer.views import _count_atoms, _extract_system_label

from .serializers import (
    ConversionHistorySerializer,
    OutFileSerializer,
    SavedConfigurationSerializer,
)


class ConversionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista e detalha as conversões do usuário autenticado."""

    serializer_class = ConversionHistorySerializer

    def get_queryset(self):
        return ConversionHistory.objects.filter(user=self.request.user).order_by('-conversion_date')


class SavedConfigurationViewSet(viewsets.ModelViewSet):
    """CRUD das configurações salvas do usuário autenticado."""

    serializer_class = SavedConfigurationSerializer

    def get_queryset(self):
        return SavedConfiguration.objects.filter(user=self.request.user).order_by('-last_used')

    def perform_create(self, serializer):
        now = timezone.now()
        serializer.save(
            user=self.request.user,
            is_default=False,
            created_at=now,
            last_used=now,
            use_count=0,
        )


class OutFileViewSet(viewsets.ModelViewSet):
    """Lista, envia e remove arquivos .out do usuário autenticado."""

    serializer_class = OutFileSerializer

    def get_queryset(self):
        return OutFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        out_file = serializer.save(user=self.request.user)
        try:
            with out_file.file.open('rb') as f:
                content = f.read().decode('utf-8', errors='replace')
            out_file.system_name = out_file.system_name or _extract_system_label(content)
            out_file.atom_count = _count_atoms(content)
            out_file.save(update_fields=['system_name', 'atom_count'])
        except Exception:
            pass
