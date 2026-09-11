"""Testes da API REST (DRF + JWT)."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from converter.models import ConversionHistory, SavedConfiguration
from visualizer.models import OutFile


class ApiAuthTests(TestCase):
    """Autenticação por token JWT."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='ApiPass123!')

    def test_token_obtain(self):
        response = self.client.post(
            '/api/v1/auth/token/',
            {'username': 'apiuser', 'password': 'ApiPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_invalid_credentials(self):
        response = self.client.post(
            '/api/v1/auth/token/',
            {'username': 'apiuser', 'password': 'senha-errada'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_endpoints_require_authentication(self):
        response = self.client.get('/api/v1/conversions/')
        self.assertEqual(response.status_code, 401)


class ApiScopeTests(TestCase):
    """Isolamento de dados por usuário."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='ApiPass123!')
        self.other = User.objects.create_user(username='other', password='OtherPass123!')
        self.client.force_authenticate(self.user)

    def _conversion(self, user, name):
        return ConversionHistory.objects.create(
            user=user,
            original_filename=f'{name}.xyz',
            system_name=name,
            fdf_content='fdf',
            parameters={},
            conversion_date=timezone.now(),
            file_size=1,
            status='completed',
            error_message='',
            download_count=0,
        )

    def test_conversions_are_scoped_to_user(self):
        self._conversion(self.user, 'A')
        self._conversion(self.other, 'B')

        response = self.client.get('/api/v1/conversions/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['system_name'], 'A')

    def test_configuration_create_sets_user_and_defaults(self):
        response = self.client.post(
            '/api/v1/configurations/',
            {'name': 'API Config', 'description': 'via API', 'parameters': {'PAO_BasisSize': 'DZP'}},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        config = SavedConfiguration.objects.get(id=response.data['id'])
        self.assertEqual(config.user, self.user)
        self.assertFalse(config.is_default)
        self.assertEqual(config.use_count, 0)
        self.assertIsNotNone(config.created_at)

    def test_configurations_are_scoped_to_user(self):
        SavedConfiguration.objects.create(
            user=self.other, name='Outra', description='', parameters={},
            is_default=False, created_at=timezone.now(), last_used=timezone.now(), use_count=0,
        )
        response = self.client.get('/api/v1/configurations/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_out_files_are_scoped_to_user(self):
        OutFile.objects.create(user=self.user, system_name='A', atom_count=1)
        OutFile.objects.create(user=self.other, system_name='B', atom_count=1)

        response = self.client.get('/api/v1/out-files/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['system_name'], 'A')
