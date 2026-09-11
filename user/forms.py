from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import UserProfile



class UserCreationForm(BaseUserCreationForm):
    # Adiciona campo de email
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('seu.email@exemplo.com')})
    )

    # Adiciona classes Bootstrap aos widgets
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Nome de usuário')})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Senha')})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Confirme a senha')})

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

    # Verificar email único (comparação sem diferenciar maiúsculas/minúsculas)
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and self._meta.model.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("Este email já está em uso."))
        return email

    # Atualiza o Meta para incluir o campo email
    class Meta(BaseUserCreationForm.Meta):
        fields = ["username", "email", "password1", "password2"]


class ContactForm(forms.Form):
    """Formulário da página de contato."""

    name = forms.CharField(
        label=_("Nome"),
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Seu nome')}),
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('seu.email@exemplo.com')}),
    )
    subject = forms.CharField(
        label=_("Assunto"),
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Assunto da mensagem')}),
    )
    message = forms.CharField(
        label=_("Mensagem"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': _('Escreva sua mensagem'),
        }),
    )


class UserProfileForm(forms.ModelForm):
    """Formulário para edição do perfil do usuário."""
    class Meta:
        model = UserProfile
        fields = ['institution', 'research_area', 'profile_picture']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sua instituição'}),
            'research_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sua área de pesquisa'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'institution': _('Instituição'),
            'research_area': _('Área de Pesquisa'),
            'profile_picture': _('Foto de Perfil'),
        }
        help_texts = {
            'profile_picture': _('Envie uma imagem para seu perfil (opcional)'),
        }
        
