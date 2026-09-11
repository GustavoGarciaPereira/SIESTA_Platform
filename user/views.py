# Built-in Python imports
import logging

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, TemplateView

# Local imports
from .forms import ContactForm, UserCreationForm, UserProfileForm
from .models import UserProfile

logger = logging.getLogger(__name__)

# Tempo de sessão para "Lembrar meus dados" (14 dias)
REMEMBER_ME_AGE = 60 * 60 * 24 * 14


class CustomLoginView(LoginView):
    """View de login com suporte à opção 'Lembrar meus dados'."""

    template_name = 'converter/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('remember'):
            self.request.session.set_expiry(REMEMBER_ME_AGE)
        else:
            self.request.session.set_expiry(0)
        return response


@require_POST
def contact_submit_view(request):
    """Valida e envia a mensagem do formulário de contato por e-mail."""
    form = ContactForm(request.POST)
    if not form.is_valid():
        errors = ' '.join(
            str(error)
            for field_errors in form.errors.values()
            for error in field_errors
        )
        messages.error(
            request,
            _('Não foi possível enviar sua mensagem: %(errors)s') % {'errors': errors},
        )
        return redirect('contact')

    data = form.cleaned_data
    try:
        send_mail(
            subject=f"[SIESTA Platform] {data['subject']}",
            message=(
                f"Nome: {data['name']}\n"
                f"E-mail: {data['email']}\n\n"
                f"{data['message']}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL or 'no-reply@siesta-platform',
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Falha ao enviar mensagem de contato de %s", data.get('email'))
        messages.error(
            request,
            _('Não foi possível enviar sua mensagem. Tente novamente mais tarde.'),
        )
        return redirect('contact')

    messages.success(
        request,
        _('Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.'),
    )
    return redirect('contact')


# Create your views here.
class HomeView(TemplateView):
    template_name = 'home.html'


class ContactView(TemplateView):
    template_name = 'contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', ContactForm())
        return context


class SignupView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'converter/signup.html'


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Substitua com os dados reais e URLs das imagens
        context['team_members'] = [
            {
                'name': 'André Flores',
                'role': _('Aluno/Doutorado'),
                'bio': _('Graduado em Ciência da Computação (UFN), Mestre em Microeletrônica (UFRGS) e aluno de Doutorado em Nanociências (UFN).'),
                'image_url': 'img/team/andre_flores.jpg',
                'email': 'andre.santos@ufn.edu.br',  # Opcional
                'lattes_url': 'http://lattes.cnpq.br/4249324194215985',  # Opcional
                'url_linkedin': "https://www.linkedin.com/in/andr%C3%A9-f-dos-santos-b11478b7/"
            },
            {
                'name': 'Gustavo Garcia Pereira',
                'role': _('Aluno/Programador'),
                'bio': _('Graduado em Ciência da Computação (UFN). Desenvolvedor principal da plataforma'),
                'image_url': 'img/team/gustavo_garcia.jpg',
                'email': 'gusgurtavo@gmail.com',  # Opcional
                'lattes_url': '',  # Opcional
                'url_linkedin': "https://www.linkedin.com/in/gustavo-garcia-pereira-078240143/"
            },
            {
                'name': 'Mirkos Martins',
                'role': _('Professor (UFN)'),
                'bio': _('Professor de Ciência da Computação, Engenharia Biomédica, Inteligência Artificial para Engenharias, Modelagem e Simulação e Complexidade de Algoritmos.'),
                'image_url': 'img/team/mirkos_martins.jpg',
                'email': 'mirkos@gmail.com',  # Opcional
                'lattes_url': 'http://lattes.cnpq.br/5382133106359249',  # Opcional
                'url_linkedin': "https://www.linkedin.com/in/mirkos-martins-77a6ab8/"
            },

            # Adicione mais membros conforme necessário
        ]
        return context


@login_required
def profile_view(request):
    """View para edição do perfil do usuário."""
    profile, _created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, _('Perfil atualizado com sucesso!'))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'user/profile.html', {'form': form})
