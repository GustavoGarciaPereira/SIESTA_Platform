# converter/forms.py

from django import forms

class UploadFileForm(forms.Form):
    xyz_file = forms.FileField(label='Selecione o arquivo Heparin.xyz', 
                               help_text='Apenas arquivos com extensão .xyz são permitidos.')

    def clean_xyz_file(self):
        file = self.cleaned_data.get('xyz_file', False)
        if file:
            if not file.name.endswith('.xyz'):
                raise forms.ValidationError("Apenas arquivos .xyz são permitidos.")
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("O arquivo é muito grande. O tamanho máximo é de 5MB.")
        return file




from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class UserCreationForm(BaseUserCreationForm):
    # Adiciona campo de email
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu.email@exemplo.com'})
    )

    # Adiciona classes Bootstrap aos widgets
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nome de usuário'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirme a senha'})

    def clean_username(self):
        """Reject usernames that differ only in case."""
        username = self.cleaned_data.get("username")
        if (
            username
            and self._meta.model.objects.filter(username__iexact=username).exists()
        ):
            self._update_errors(
                ValidationError(
                    {
                        "username": self.instance.unique_error_message(
                            self._meta.model, ["username"]
                        )
                    }
                )
            )
        else:
            return username

    # Verificar email único
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and self._meta.model.objects.filter(email=email).exists():
            raise ValidationError(_("Este email já está em uso."))
        return email

    # Atualiza o Meta para incluir o campo email
    class Meta(BaseUserCreationForm.Meta):
        fields = ["username", "email", "password1", "password2"]