"""Serializers da API REST."""

from rest_framework import serializers

from converter.models import ConversionHistory, SavedConfiguration
from visualizer.models import OutFile


class ConversionHistorySerializer(serializers.ModelSerializer):
    """Histórico de conversões (somente leitura)."""

    class Meta:
        model = ConversionHistory
        fields = [
            'id', 'original_filename', 'system_name', 'parameters',
            'conversion_date', 'completion_date', 'file_size', 'status',
            'download_count',
        ]
        read_only_fields = fields


class SavedConfigurationSerializer(serializers.ModelSerializer):
    """Configurações salvas do usuário."""

    class Meta:
        model = SavedConfiguration
        fields = ['id', 'name', 'description', 'parameters', 'created_at', 'last_used', 'use_count']
        read_only_fields = ['created_at', 'last_used', 'use_count']


class OutFileSerializer(serializers.ModelSerializer):
    """Arquivos .out do usuário."""

    class Meta:
        model = OutFile
        fields = ['id', 'file', 'system_name', 'atom_count', 'uploaded_at']
        read_only_fields = ['atom_count', 'uploaded_at']
