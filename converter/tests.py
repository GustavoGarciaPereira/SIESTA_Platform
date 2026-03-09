import io

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import json

from .models import UploadedFile, ConversionHistory, SavedConfiguration
from .forms import SIESTAParametersForm
from .utils import read_xyz


def _make_xyz_file(atom_lines):
    """Cria um objeto BytesIO simulando um arquivo XYZ a partir de linhas de átomos."""
    n = len(atom_lines)
    content = f"{n}\ncomentario\n" + "\n".join(atom_lines)
    return io.BytesIO(content.encode('utf-8'))


class ReadXyzTests(TestCase):
    """Testes para a função read_xyz em converter/utils.py."""

    def test_symbols_unchanged(self):
        """XYZ com símbolos químicos: retorna os átomos corretamente, flag=False."""
        file_obj = _make_xyz_file(["H  0.0  0.0  0.0", "O  1.0  0.0  0.0"])
        atoms, detected = read_xyz(file_obj)
        self.assertFalse(detected)
        self.assertEqual(len(atoms), 2)
        self.assertEqual(atoms[0][0], 'H')
        self.assertEqual(atoms[1][0], 'O')

    def test_atomic_numbers_converted(self):
        """XYZ com números atômicos: converte para símbolos, flag=True."""
        file_obj = _make_xyz_file(["1  0.0  0.0  0.0", "8  1.0  0.0  0.0"])
        atoms, detected = read_xyz(file_obj)
        self.assertTrue(detected)
        self.assertEqual(len(atoms), 2)
        self.assertEqual(atoms[0][0], 'H')
        self.assertEqual(atoms[1][0], 'O')

    def test_unknown_atomic_number_raises(self):
        """Número atômico desconhecido deve levantar ValueError."""
        file_obj = _make_xyz_file(["999  0.0  0.0  0.0"])
        with self.assertRaises(ValueError):
            read_xyz(file_obj)

    def test_coordinates_preserved(self):
        """As coordenadas devem ser preservadas corretamente após conversão."""
        file_obj = _make_xyz_file(["6  1.5  2.5  3.5"])
        atoms, detected = read_xyz(file_obj)
        self.assertTrue(detected)
        self.assertEqual(atoms[0][0], 'C')
        self.assertAlmostEqual(atoms[0][1], 1.5)
        self.assertAlmostEqual(atoms[0][2], 2.5)
        self.assertAlmostEqual(atoms[0][3], 3.5)


class ModelTests(TestCase):
    """Testes para os modelos do aplicativo converter."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_create_uploaded_file(self):
        """Testa a criação de um UploadedFile."""
        uploaded = UploadedFile.objects.create(
            user=self.user,
            file=None,
            original_name='test.xyz',
            file_type='xyz',
            size=1024,
            checksum='abc123',
            upload_date=timezone.now(),
            is_temp=False
        )
        self.assertEqual(UploadedFile.objects.count(), 1)
        self.assertEqual(uploaded.original_name, 'test.xyz')
        self.assertEqual(uploaded.user.username, 'testuser')
    
    def test_create_conversion_history(self):
        """Testa a criação de um ConversionHistory."""
        uploaded = UploadedFile.objects.create(
            user=self.user,
            file=None,
            original_name='test.xyz',
            file_type='xyz',
            size=1024,
            checksum='abc123',
            upload_date=timezone.now(),
            is_temp=False
        )
        
        conv = ConversionHistory.objects.create(
            user=self.user,
            uploaded_file=uploaded,
            original_filename='test.xyz',
            system_name='Test System',
            fdf_content='%block test\n%endblock',
            parameters={'meshcutoff': '200 Ry'},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )
        
        self.assertEqual(ConversionHistory.objects.count(), 1)
        self.assertEqual(conv.system_name, 'Test System')
        self.assertEqual(conv.status, 'completed')
        self.assertEqual(conv.download_count, 0)
    
    def test_create_saved_configuration(self):
        """Testa a criação de um SavedConfiguration."""
        config = SavedConfiguration.objects.create(
            user=self.user,
            name='Test Config',
            description='Test configuration',
            parameters={'meshcutoff': '200 Ry', 'XC_functional': 'LDA'},
            is_default=False,
            created_at=timezone.now(),
            last_used=timezone.now(),
            use_count=0
        )
        
        self.assertEqual(SavedConfiguration.objects.count(), 1)
        self.assertEqual(config.name, 'Test Config')
        self.assertEqual(config.use_count, 0)
        self.assertFalse(config.is_default)


class ViewTests(TestCase):
    """Testes para as views do aplicativo converter."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_history_view_authenticated(self):
        """Testa o acesso à view de histórico com usuário autenticado."""
        response = self.client.get(reverse('converter_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/history.html')
    
    def test_history_view_unauthenticated(self):
        """Testa o acesso à view de histórico sem autenticação."""
        self.client.logout()
        response = self.client.get(reverse('converter_history'))
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_my_configurations_view(self):
        """Testa o acesso à view de configurações salvas."""
        response = self.client.get(reverse('my_configurations'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/my_configs.html')
    
    def test_save_configuration_view(self):
        """Testa a view de salvar configuração."""
        params = {
            'meshcutoff': '200 Ry',
            'XC_functional': 'LDA',
            'system_name': 'Test'
        }
        
        response = self.client.post(
            reverse('save_configuration'),
            {
                'name': 'Test Config',
                'description': 'Test description',
                'parameters': json.dumps(params)
            },
            content_type='application/x-www-form-urlencoded'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertTrue('config_id' in data)
        
        # Verifica se a configuração foi criada
        self.assertEqual(SavedConfiguration.objects.count(), 1)
        config = SavedConfiguration.objects.first()
        self.assertEqual(config.name, 'Test Config')
        self.assertEqual(config.user, self.user)
    
    def test_load_configuration_view(self):
        """Testa a view de carregar configuração."""
        # Primeiro cria uma configuração
        config = SavedConfiguration.objects.create(
            user=self.user,
            name='Test Config',
            description='Test',
            parameters={'meshcutoff': '200 Ry'},
            is_default=False,
            created_at=timezone.now(),
            last_used=timezone.now(),
            use_count=0
        )
        
        response = self.client.get(reverse('load_configuration', args=[config.id]))
        self.assertEqual(response.status_code, 302)  # Redireciona para convert
        self.assertEqual(response.url, reverse('convert'))
        
        # Verifica se o use_count foi incrementado
        config.refresh_from_db()
        self.assertEqual(config.use_count, 1)
    
    def test_delete_configuration_view(self):
        """Testa a view de excluir configuração."""
        config = SavedConfiguration.objects.create(
            user=self.user,
            name='Test Config',
            description='Test',
            parameters={'meshcutoff': '200 Ry'},
            is_default=False,
            created_at=timezone.now(),
            last_used=timezone.now(),
            use_count=0
        )
        
        self.assertEqual(SavedConfiguration.objects.count(), 1)
        
        response = self.client.get(reverse('delete_configuration', args=[config.id]))
        self.assertEqual(response.status_code, 302)  # Redireciona para my_configurations
        self.assertEqual(response.url, reverse('my_configurations'))
        
        # Verifica se a configuração foi excluída
        self.assertEqual(SavedConfiguration.objects.count(), 0)


class FormTests(TestCase):
    """Testes para os formulários do aplicativo converter."""
    
    def test_siesta_parameters_form_valid(self):
        """Testa o formulário SIESTAParametersForm com dados válidos."""
        form_data = {
            'system_name': 'Test System',
            'lattice_constant': 1.0,
            'cell_size_x': 50.0,
            'cell_size_y': 50.0,
            'cell_size_z': 50.0,
            'PAO_BasisSize': 'DZP',
            'PAO_EnergyShift': 0.05,
            'MD_TypeOfRun': 'CG',
            'MD_NumCGsteps': 500,
            'MD_MaxForceTol': 0.05,
            'MaxSCFIterations': 100,
            'SpinPolarized': True,
            'MeshCutoff': 200.0,
            'DM_UseSaveDM': True,
            'UseSaveData': True,
            'MD_UseSaveXV': True,
            'MD_UseSaveCG': True,
            'DM_MixingWeight': 0.10,
            'DM_NumberPulay': 3,
            'DM_Tolerance': 1.0e-3,
            'WriteCoorXmol': True,
            'WriteMullikenPop': 1,
            'XC_functional': 'LDA',
            'XC_authors': 'CA',
            'SolutionMethod': 'diagon',
            'ElectronicTemperature': 80.0,
            'download_pseudos': False,
        }
        
        form = SIESTAParametersForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_siesta_parameters_form_invalid(self):
        """Testa o formulário SIESTAParametersForm com dados inválidos."""
        form_data = {
            'system_name': 'Test System',
            'MeshCutoff': -50.0,  # Valor negativo, inválido
        }
        
        form = SIESTAParametersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('MeshCutoff', form.errors)
