# Django imports
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse


def _url_entry(name, url_name, description, params=None):
    """Monta a entrada do catálogo, resolvendo um exemplo de URL quando há parâmetros."""
    example_url = ''
    if params:
        try:
            example_url = reverse(url_name, args=[1] * len(params))
        except NoReverseMatch:
            example_url = ''
    return {
        'name': name,
        'url_name': url_name,
        'description': description,
        'params': params,
        'example_url': example_url,
    }


@staff_member_required(login_url='login')
def dashboard_view(request):
    url_groups = [
        {
            'name': 'Administração',
            'urls': [
                _url_entry('Admin', 'admin:index', 'Painel administrativo do Django'),
            ]
        },
        {
            'name': 'Conversão',
            'urls': [
                _url_entry('Conversor', 'convert', 'Página principal de conversão XYZ → FDF'),
            ]
        },
        {
            'name': 'Histórico e Downloads',
            'urls': [
                _url_entry('Histórico', 'converter_history', 'Histórico de conversões do usuário'),
                _url_entry('Download FDF', 'download_fdf', 'Download do arquivo FDF (requer ID da conversão)', ['conv_id']),
                _url_entry('Download Pseudos', 'download_pseudos', 'Download dos pseudopotenciais (requer ID da conversão)', ['conv_id']),
                _url_entry('Excluir do Histórico', 'delete_history', 'Exclui uma conversão (requer ID, POST)', ['conv_id']),
            ]
        },
        {
            'name': 'Configurações Salvas',
            'urls': [
                _url_entry('Salvar Configuração', 'save_configuration', 'Salva a configuração atual (POST via AJAX)'),
                _url_entry('Minhas Configurações', 'my_configurations', 'Lista configurações salvas pelo usuário'),
                _url_entry('Carregar Configuração', 'load_configuration', 'Carrega uma configuração (requer ID, POST)', ['config_id']),
                _url_entry('Excluir Configuração', 'delete_configuration', 'Exclui uma configuração (requer ID, POST)', ['config_id']),
            ]
        },
        {
            'name': 'Visualizador 3D',
            'urls': [
                _url_entry('Upload .out', 'visualizer:upload_out', 'Upload de arquivo .out do SIESTA'),
                _url_entry('Visualizar .out', 'visualizer:visualize', 'Visualizador 3D (requer ID)', ['out_id']),
                _url_entry('Conteúdo .out', 'visualizer:out_content', 'Conteúdo bruto do .out (requer ID)', ['out_id']),
                _url_entry('Átomos (JSON)', 'visualizer:out_atoms', 'Átomos parseados em JSON (requer ID)', ['out_id']),
            ]
        },
        {
            'name': 'Páginas Estáticas',
            'urls': [
                _url_entry('Home', 'home', 'Página inicial'),
                _url_entry('Sobre', 'about', 'Sobre o projeto'),
                _url_entry('Contato', 'contact', 'Formulário de contato'),
                _url_entry('Enviar Contato', 'contact_submit', 'Endpoint para envio do contato (POST)'),
            ]
        },
        {
            'name': 'Autenticação',
            'urls': [
                _url_entry('Login', 'login', 'Página de login'),
                _url_entry('Logout', 'logout', 'Logout'),
                _url_entry('Registro', 'signup', 'Criar nova conta'),
                _url_entry('Recuperar Senha', 'password_reset', 'Solicitar redefinição de senha'),
                _url_entry('E-mail Enviado', 'password_reset_done', 'Confirmação de envio do e-mail'),
                _url_entry('Redefinir Senha (confirm)', 'password_reset_confirm', 'Confirmar redefinição (requer uid e token)', ['uidb64', 'token']),
                _url_entry('Redefinição Completa', 'password_reset_complete', 'Senha redefinida com sucesso'),
            ]
        },
        {
            'name': 'Perfil',
            'urls': [
                _url_entry('Perfil', 'profile', 'Editar perfil do usuário'),
            ]
        },
    ]
    return render(request, 'dashboard/dashboard.html', {'url_groups': url_groups})
