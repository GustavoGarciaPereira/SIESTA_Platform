"""
Testes para as views do aplicativo dashboard.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class DashboardViewsTests(TestCase):
    """Testes para as views do dashboard."""

    def setUp(self):
        self.client = Client()

        # Cria um usuário staff
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            email='staff@example.com',
            is_staff=True
        )

        # Cria um usuário normal (não staff)
        self.normal_user = User.objects.create_user(
            username='normaluser',
            password='testpass123',
            email='normal@example.com',
            is_staff=False
        )

    def test_dashboard_view_staff_access(self):
        """Testa acesso ao dashboard por usuário staff."""
        self.client.login(username='staffuser', password='testpass123')

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')

        # Verifica se o contexto contém url_groups
        self.assertIn('url_groups', response.context)

        # Verifica se há grupos de URLs
        url_groups = response.context['url_groups']
        self.assertGreater(len(url_groups), 0)

        # Verifica alguns grupos esperados
        group_names = [group['name'] for group in url_groups]
        expected_groups = ['Administração', 'Conversão', 'Histórico e Downloads']
        for expected in expected_groups:
            self.assertIn(expected, group_names)

    def test_dashboard_view_non_staff_access(self):
        """Testa acesso ao dashboard por usuário não staff."""
        self.client.login(username='normaluser', password='testpass123')

        response = self.client.get(reverse('dashboard'))

        # Deve redirecionar para o login da plataforma (403 ou redirecionamento)
        self.assertIn(response.status_code, [302, 403])

        if response.status_code == 302:
            self.assertIn('/login/', response.url)

    def test_dashboard_view_unauthenticated(self):
        """Testa acesso ao dashboard sem autenticação."""
        response = self.client.get(reverse('dashboard'))

        # Deve redirecionar para o login da plataforma
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_content_structure(self):
        """Testa a estrutura do conteúdo do dashboard."""
        self.client.login(username='staffuser', password='testpass123')

        response = self.client.get(reverse('dashboard'))
        url_groups = response.context['url_groups']

        # Verifica estrutura de cada grupo
        for group in url_groups:
            self.assertIn('name', group)
            self.assertIn('urls', group)
            self.assertIsInstance(group['urls'], list)

            # Verifica estrutura de cada URL
            for url_info in group['urls']:
                self.assertIn('name', url_info)
                self.assertIn('url_name', url_info)
                self.assertIn('description', url_info)

                # params pode ser None ou lista
                if url_info.get('params') is not None:
                    self.assertIsInstance(url_info['params'], list)
                    # Entradas com parâmetros devem ter exemplo resolvido
                    self.assertTrue(url_info['example_url'])

    def test_dashboard_specific_groups(self):
        """Testa grupos específicos do dashboard."""
        self.client.login(username='staffuser', password='testpass123')

        response = self.client.get(reverse('dashboard'))
        url_groups = response.context['url_groups']

        # Mapeia grupos por nome para fácil acesso
        groups_by_name = {group['name']: group for group in url_groups}

        # Testa grupo de Administração
        self.assertIn('Administração', groups_by_name)
        admin_group = groups_by_name['Administração']
        admin_urls = [url['url_name'] for url in admin_group['urls']]
        self.assertIn('admin:index', admin_urls)

        # Testa grupo de Conversão
        self.assertIn('Conversão', groups_by_name)
        converter_group = groups_by_name['Conversão']
        converter_urls = [url['url_name'] for url in converter_group['urls']]
        self.assertIn('convert', converter_urls)

        # Testa grupo de Autenticação
        self.assertIn('Autenticação', groups_by_name)
        auth_group = groups_by_name['Autenticação']
        auth_urls = [url['url_name'] for url in auth_group['urls']]
        expected_auth_urls = ['login', 'logout', 'signup', 'password_reset']
        for url in expected_auth_urls:
            self.assertIn(url, auth_urls)

    def test_dashboard_url_count(self):
        """Testa se o dashboard lista um número razoável de URLs."""
        self.client.login(username='staffuser', password='testpass123')

        response = self.client.get(reverse('dashboard'))
        url_groups = response.context['url_groups']

        # Conta total de URLs
        total_urls = sum(len(group['urls']) for group in url_groups)

        # Deve haver pelo menos algumas URLs
        self.assertGreater(total_urls, 10)

        # Verifica distribuição por grupo
        for group in url_groups:
            self.assertGreater(len(group['urls']), 0,
                             f"Grupo '{group['name']}' está vazio")


class DashboardModelTests(TestCase):
    """Testes relacionados a modelos do dashboard (se houver)."""

    def test_no_models_in_dashboard(self):
        """Verifica que o dashboard não tem modelos próprios."""
        from django.apps import apps

        config = apps.get_app_config('dashboard')
        self.assertIsNone(
            config.models_module,
            "Dashboard não deve ter modelos próprios",
        )
