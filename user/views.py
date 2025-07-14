from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import (
    UserCreationForm,
)


def contact_submit_view(request):
    if request.method == 'POST':
        # Aqui você poderia, no futuro, pegar os dados do formulário:
        # name = request.POST.get('name')
        # email = request.POST.get('email')
        # subject = request.POST.get('subject')
        # message_body = request.POST.get('message')
        
        # Lógica de processamento (ex: enviar email, salvar no DB) iria aqui.
        # Por enquanto, apenas simulamos o sucesso.
        
        messages.success(request, 'Sua mensagem foi "enviada" com sucesso! Entraremos em contato em breve (esta é uma simulação).')
        return redirect('contact') # Redireciona de volta para a página de contato

    # Se não for POST, redireciona para a página de contato (ou pode mostrar um erro)
    messages.error(request, 'Método inválido para esta ação.')
    return redirect('contact')


# Create your views here.
class HomeView(TemplateView):
    template_name = 'home.html'
    
class ContactView(TemplateView):
    template_name = 'contact.html' # Certifique-se que 'contact.html' está no seu diretório de templates
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
                'role': 'Aluno/Doutorado',
                'bio': 'Graduado em Ciência da Computação (UFN), Mestre em Microeletrônica (UFRGS) e aluno de Doutorado em Nanociências (UFN).',
                'image_url': 'https://lasimon.vercel.app/assets/img/team/andre_flores.jpg', # Substitua pela URL da imagem real
                'email': 'andre.santos@ufn.edu.br', # Opcional
                'lattes_url': 'http://lattes.cnpq.br/4249324194215985', # Opcional
                'url_linkedin':"https://www.linkedin.com/in/andr%C3%A9-f-dos-santos-b11478b7/"
            },
            {
                'name': 'Gustavo Garcia Pereira',
                'role': 'Aluno/Programador',
                'bio': 'Graduado em Ciência da Computação (UFN). Desenvovedor principal da plataforma',
                'image_url': 'https://avatars.githubusercontent.com/u/19331198?v=4', # Substitua pela URL da imagem real
                'email': 'gusgurtavo@gmail.com', # Opcional
                'lattes_url': 'http://lattes.cnpq.br/SEU_ID_LATTES_ANDRE', # Opcional
                'url_linkedin':"https://www.linkedin.com/in/gustavo-garcia-pereira-078240143/"
            },
            {
                'name': 'Mirkos Martins',
                'role': 'Professor (UFN)',
                'bio': 'Professor de Ciência da Computação, Engenharia Biomédica, Inteligência Artificial para Engenharias, Modelagem e Simulação e Complexidade de Algoritmos.',
                'image_url': 'https://avatars.githubusercontent.com/u/5223402?v=4', # Substitua pela URL da imagem real
                'email': 'mirkos@gmail.com', # Opcional
                'lattes_url': 'http://lattes.cnpq.br/5382133106359249', # Opcional
                'url_linkedin':"https://www.linkedin.com/in/mirkos-martins-77a6ab8/"
            },
            
            # Adicione mais membros conforme necessário
        ]
        # Você pode manter as outras seções ou removê-las se a página for só sobre a equipe
        context['show_mission_vision'] = False # Defina como True se quiser mostrar as outras seções
        return context
