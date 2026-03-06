# Django imports
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def dashboard_view(request):
    url_groups = [
        {
            'name': 'Administração',
            'urls': [
                {'name': 'Admin', 'url_name': 'admin:index', 'description': 'Painel administrativo do Django', 'params': None},
            ]
        },
        {
            'name': 'Conversão',
            'urls': [
                {'name': 'Conversor', 'url_name': 'convert', 'description': 'Página principal de conversão XYZ → FDF', 'params': None},
            ]
        },
        {
            'name': 'Histórico e Downloads',
            'urls': [
                {'name': 'Histórico', 'url_name': 'converter_history', 'description': 'Histórico de conversões do usuário', 'params': None},
                {'name': 'Download FDF', 'url_name': 'download_fdf', 'description': 'Download do arquivo FDF (requer ID da conversão)', 'params': ['conv_id']},
                {'name': 'Download Pseudos', 'url_name': 'download_pseudos', 'description': 'Download dos pseudopotenciais (requer ID da conversão)', 'params': ['conv_id']},
            ]
        },
        {
            'name': 'Configurações Salvas',
            'urls': [
                {'name': 'Salvar Configuração', 'url_name': 'save_configuration', 'description': 'Salva a configuração atual (POST via AJAX)', 'params': None},
                {'name': 'Minhas Configurações', 'url_name': 'my_configurations', 'description': 'Lista configurações salvas pelo usuário', 'params': None},
                {'name': 'Carregar Configuração', 'url_name': 'load_configuration', 'description': 'Carrega uma configuração (requer ID)', 'params': ['config_id']},
                {'name': 'Excluir Configuração', 'url_name': 'delete_configuration', 'description': 'Exclui uma configuração (requer ID)', 'params': ['config_id']},
            ]
        },
        {
            'name': 'Páginas Estáticas',
            'urls': [
                {'name': 'Home', 'url_name': 'home', 'description': 'Página inicial', 'params': None},
                {'name': 'Sobre', 'url_name': 'about', 'description': 'Sobre o projeto', 'params': None},
                {'name': 'Contato', 'url_name': 'contact', 'description': 'Formulário de contato', 'params': None},
                {'name': 'Enviar Contato', 'url_name': 'contact_submit', 'description': 'Endpoint para envio do contato (POST)', 'params': None},
            ]
        },
        {
            'name': 'Autenticação',
            'urls': [
                {'name': 'Login', 'url_name': 'login', 'description': 'Página de login', 'params': None},
                {'name': 'Logout', 'url_name': 'logout', 'description': 'Logout', 'params': None},
                {'name': 'Registro', 'url_name': 'signup', 'description': 'Criar nova conta', 'params': None},
                {'name': 'Recuperar Senha', 'url_name': 'password_reset', 'description': 'Solicitar redefinição de senha', 'params': None},
                {'name': 'Redefinir Senha (confirm)', 'url_name': 'password_reset_confirm', 'description': 'Confirmar redefinição (requer uid e token)', 'params': ['uidb64', 'token']},
                {'name': 'Redefinição Completa', 'url_name': 'password_reset_complete', 'description': 'Senha redefinida com sucesso', 'params': None},
            ]
        },
        {
            'name': 'Perfil',
            'urls': [
                {'name': 'Perfil', 'url_name': 'profile', 'description': 'Editar perfil do usuário', 'params': None},
            ]
        },
    ]
    return render(request, 'dashboard/dashboard.html', {'url_groups': url_groups})