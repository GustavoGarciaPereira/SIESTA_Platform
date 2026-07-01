"""Formulários do app visualizer."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import OutFile


class OutFileForm(forms.ModelForm):
    """Formulário para upload de arquivo .out do SIESTA."""

    class Meta:
        model = OutFile
        fields = ["file", "system_name"]
        widgets = {
            "file": forms.FileInput(
                attrs={"class": "form-control", "accept": ".out,.txt"}
            ),
            "system_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Ex: Molecula_H2O"),
                }
            ),
        }
        labels = {
            "file": _("Arquivo .out do SIESTA"),
            "system_name": _("Nome do sistema (opcional)"),
        }
        help_texts = {
            "file": _(
                "Selecione um arquivo de saída (.out) do SIESTA. "
                "Deve conter as seções 'Atomic coordinates (Ang)' "
                "e 'Mulliken populations'."
            ),
        }

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
            if ext not in ("out", "txt"):
                raise forms.ValidationError(
                    _("Apenas arquivos .out ou .txt são permitidos.")
                )
            if f.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    _("Arquivo muito grande. Limite: 10 MB.")
                )
        return f
