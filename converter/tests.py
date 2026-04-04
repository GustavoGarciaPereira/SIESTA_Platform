import io
import os
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import UploadedFile, ConversionHistory, SavedConfiguration
from .forms import SIESTAParametersForm
from .utils import read_xyz, bounding_box, convert_xyz_to_fdf, create_zip_archive


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


class BoundingBoxTests(TestCase):
    """Testes para a função bounding_box em converter/utils.py."""

    def test_bounding_box_single_atom(self):
        """Testa bounding_box com um único átomo."""
        atoms = [('H', 1.0, 2.0, 3.0)]
        result = bounding_box(atoms)
        expected = (1.0, 1.0, 2.0, 2.0, 3.0, 3.0)
        self.assertEqual(result, expected)

    def test_bounding_box_multiple_atoms(self):
        """Testa bounding_box com múltiplos átomos."""
        atoms = [
            ('H', 0.0, 0.0, 0.0),
            ('O', 1.0, 2.0, 3.0),
            ('C', -1.0, -2.0, -3.0)
        ]
        result = bounding_box(atoms)
        expected = (-1.0, 1.0, -2.0, 2.0, -3.0, 3.0)
        self.assertEqual(result, expected)

    def test_bounding_box_empty_list(self):
        """Testa bounding_box com lista vazia."""
        with self.assertRaises(ValueError):
            bounding_box([])


class ConvertXyzToFdfTests(TestCase):
    """Testes para a função convert_xyz_to_fdf em converter/utils.py."""

    def test_convert_xyz_to_fdf_basic(self):
        """Testa conversão básica de XYZ para FDF."""
        xyz_file = _make_xyz_file(["H  0.0  0.0  0.0", "O  1.0  0.0  0.0"])
        params = {
            'system_name': 'TestSystem',
            'cell_size_x': 50.0,
            'cell_size_y': 50.0,
            'cell_size_z': 50.0,
            'lattice_constant': 1.0,
            'PAO_BasisSize': 'DZP',
            'PAO_EnergyShift': 0.05,
            'MD_TypeOfRun': 'CG',
            'MD_NumCGsteps': 1000,
            'MaxSCFIterations': 100,
            'SpinPolarized': True,
            'MeshCutoff': 200.0,
            'DM_UseSaveDM': True,
            'UseSaveData': True,
            'MD_UseSaveXV': True,
            'MD_UseSaveCG': True,
            'DM_MixingWeight': 0.10,
            'DM_NumberPulay': 3,
            'WriteCoorXmol': True,
            'WriteMullikenPop': 1,
            'XC_functional': 'LDA',
            'XC_authors': 'CA',
            'SolutionMethod': 'diagon',
            'ElectronicTemperature': 80.0,
            'DM_Tolerance': 1.0e-3,
            'MD_MaxForceTol': 0.05
        }

        fdf_content, unique_species, atomic_numbers_detected = convert_xyz_to_fdf(
            xyz_file, 'TestSystem', params
        )

        self.assertFalse(atomic_numbers_detected)
        self.assertEqual(len(unique_species), 2)
        self.assertIn('H', unique_species)
        self.assertIn('O', unique_species)

        # Verifica se o conteúdo FDF contém informações essenciais
        self.assertIn('SystemName    TestSystem', fdf_content)
        self.assertIn('NumberOfAtoms    2', fdf_content)
        self.assertIn('NumberOfSpecies  2', fdf_content)
        self.assertIn('ChemicalSpeciesLabel', fdf_content)
        self.assertIn('AtomicCoordinatesAndAtomicSpecies', fdf_content)

    def test_convert_xyz_to_fdf_with_atomic_numbers(self):
        """Testa conversão com números atômicos no arquivo XYZ."""
        xyz_file = _make_xyz_file(["1  0.0  0.0  0.0", "8  1.0  0.0  0.0"])
        params = {
            'system_name': 'TestSystem',
            'cell_size_x': 50.0,
            'cell_size_y': 50.0,
            'cell_size_z': 50.0,
            'lattice_constant': 1.0,
            'PAO_BasisSize': 'DZP'
        }

        fdf_content, unique_species, atomic_numbers_detected = convert_xyz_to_fdf(
            xyz_file, 'TestSystem', params
        )

        self.assertTrue(atomic_numbers_detected)
        self.assertEqual(len(unique_species), 2)
        self.assertIn('H', unique_species)
        self.assertIn('O', unique_species)

    def test_convert_xyz_to_fdf_empty_file(self):
        """Testa conversão com arquivo XYZ vazio."""
        xyz_file = _make_xyz_file([])
        params = {'system_name': 'TestSystem'}

        with self.assertRaises(ValueError):
            convert_xyz_to_fdf(xyz_file, 'TestSystem', params)

    def test_convert_xyz_to_fdf_custom_pt_table(self):
        """Testa conversão com tabela periódica personalizada."""
        xyz_file = _make_xyz_file(["H  0.0  0.0  0.0", "X  1.0  0.0  0.0"])
        params = {'system_name': 'TestSystem'}
        custom_pt = {'H': 1, 'X': 99}

        fdf_content, unique_species, atomic_numbers_detected = convert_xyz_to_fdf(
            xyz_file, 'TestSystem', params, custom_pt
        )

        self.assertIn('X', unique_species)
        self.assertIn('X.lda', fdf_content)


class CreateZipArchiveTests(TestCase):
    """Testes para a função create_zip_archive em converter/utils.py."""

    def setUp(self):
        from django.test import RequestFactory
        self.factory = RequestFactory()

        # Cria diretório de pseudopotenciais de teste
        import os
        self.test_pseudos_dir = '/tmp/test_pseudos'
        os.makedirs(self.test_pseudos_dir, exist_ok=True)

        # Cria alguns arquivos .psf de teste
        for element in ['H', 'O', 'C']:
            pseudo_path = os.path.join(self.test_pseudos_dir, f"{element}.lda.psf")
            with open(pseudo_path, 'w') as f:
                f.write(f"Pseudopotential content for {element}")

        # Configura settings temporariamente
        from django.conf import settings
        self.original_pseudos_dir = getattr(settings, 'PSEUDOPOTENTIALS_DIR', None)
        settings.PSEUDOPOTENTIALS_DIR = self.test_pseudos_dir

    def tearDown(self):
        # Restaura configuração original
        from django.conf import settings
        if self.original_pseudos_dir:
            settings.PSEUDOPOTENTIALS_DIR = self.original_pseudos_dir
        else:
            delattr(settings, 'PSEUDOPOTENTIALS_DIR')

        # Limpa diretório de teste
        import shutil
        if os.path.exists(self.test_pseudos_dir):
            shutil.rmtree(self.test_pseudos_dir)

    def test_create_zip_archive_basic(self):
        """Testa criação básica de arquivo ZIP."""
        request = self.factory.get('/')
        fdf_content = "SystemName Test\nNumberOfAtoms 2"
        system_name = "TestSystem"
        unique_species = ['H', 'O']

        response = create_zip_archive(request, fdf_content, system_name, unique_species)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.zip', response['Content-Disposition'])

        # Verifica se o conteúdo é um ZIP válido
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            # Deve conter arquivo .fdf
            self.assertIn('testsystem.fdf', zip_f.namelist())

            # Deve conter arquivos .psf para as espécies disponíveis
            self.assertIn('H.lda.psf', zip_f.namelist())
            self.assertIn('O.lda.psf', zip_f.namelist())

            # Verifica conteúdo do arquivo .fdf
            fdf_data = zip_f.read('testsystem.fdf').decode('utf-8')
            self.assertIn('SystemName Test', fdf_data)

    def _add_message_middleware(self, request):
        """Configura suporte a messages para requests do RequestFactory."""
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

    def test_create_zip_archive_missing_pseudos_dir(self):
        """Testa criação de ZIP quando diretório de pseudos não está configurado."""
        from django.conf import settings
        # Remove configuração temporariamente
        if hasattr(settings, 'PSEUDOPOTENTIALS_DIR'):
            delattr(settings, 'PSEUDOPOTENTIALS_DIR')

        request = self.factory.get('/')
        self._add_message_middleware(request)
        fdf_content = "Test content"
        system_name = "TestSystem"
        unique_species = ['H', 'O']

        response = create_zip_archive(request, fdf_content, system_name, unique_species)

        # Deve retornar arquivo .fdf individual, não ZIP
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('.fdf', response['Content-Disposition'])
        self.assertNotEqual(response['Content-Type'], 'application/zip')

        # Restaura configuração
        settings.PSEUDOPOTENTIALS_DIR = self.test_pseudos_dir

    def test_create_zip_archive_missing_pseudo_file(self):
        """Testa criação de ZIP quando algum arquivo .psf está faltando."""
        request = self.factory.get('/')
        self._add_message_middleware(request)
        fdf_content = "Test content"
        system_name = "TestSystem"
        # 'X' não tem arquivo .psf no diretório de teste
        unique_species = ['H', 'O', 'X']

        response = create_zip_archive(request, fdf_content, system_name, unique_species)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        # Verifica se contém os arquivos disponíveis
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            self.assertIn('H.lda.psf', zip_f.namelist())
            self.assertIn('O.lda.psf', zip_f.namelist())
            # 'X.lda.psf' não deve estar presente
            self.assertNotIn('X.lda.psf', zip_f.namelist())

    def test_create_zip_archive_empty_species(self):
        """Testa criação de ZIP com lista de espécies vazia."""
        request = self.factory.get('/')
        fdf_content = "Test content"
        system_name = "TestSystem"
        unique_species = []

        response = create_zip_archive(request, fdf_content, system_name, unique_species)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        # Deve conter apenas o arquivo .fdf
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            self.assertEqual(len(zip_f.namelist()), 1)
            self.assertIn('testsystem.fdf', zip_f.namelist())

    def test_create_zip_archive_slugified_filename(self):
        """Testa se o nome do arquivo é corretamente slugificado."""
        request = self.factory.get('/')
        fdf_content = "Test content"
        # Nome com espaços e caracteres especiais
        system_name = "Test System Name (v1.0)"
        unique_species = ['H']

        response = create_zip_archive(request, fdf_content, system_name, unique_species)

        self.assertIn('attachment', response['Content-Disposition'])
        # Nome deve ser slugificado (Django remove pontos com slugify)
        self.assertIn('test-system-name-v10.zip', response['Content-Disposition'])


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
            }
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
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_file = SimpleUploadedFile('test.xyz', b'2\nTest\nH 0 0 0\nO 1 0 0', content_type='text/plain')
        form_data = {
            'system_name': 'Test System',
            'lattice_constant': 1.0,
            'cell_size_x': 50.0,
            'cell_size_y': 50.0,
            'cell_size_z': 50.0,
            'padding': 1.0,
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

        form = SIESTAParametersForm(data=form_data, files={'xyz_file': mock_file})
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


class ConvertViewTests(TestCase):
    """Testes para a ConvertView (view principal de conversão)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_get_view(self):
        """Testa acesso GET à view de conversão."""
        response = self.client.get(reverse('convert'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/upload.html')
        self.assertContains(response, 'form')

    def test_post_view_with_valid_data(self):
        """Testa POST com dados válidos para conversão."""
        # Cria um arquivo XYZ simulado
        xyz_content = "2\nTest\nH  0.0  0.0  0.0\nO  1.0  0.0  0.0"

        with open('test.xyz', 'w') as f:
            f.write(xyz_content)

        with open('test.xyz', 'rb') as f:
            response = self.client.post(reverse('convert'), {
                'xyz_file': f,
                'system_name': 'TestSystem',
                'lattice_constant': 1.0,
                'cell_size_x': 50.0,
                'cell_size_y': 50.0,
                'cell_size_z': 50.0,
                'padding': 1.0,
                'PAO_BasisSize': 'DZP',
                'PAO_EnergyShift': 0.05,
                'MD_TypeOfRun': 'CG',
                'MD_NumCGsteps': 1000,
                'MaxSCFIterations': 100,
                'SpinPolarized': True,
                'MeshCutoff': 200.0,
                'DM_UseSaveDM': True,
                'UseSaveData': True,
                'MD_UseSaveXV': True,
                'MD_UseSaveCG': True,
                'DM_MixingWeight': 0.10,
                'DM_NumberPulay': 3,
                'WriteCoorXmol': True,
                'WriteMullikenPop': 1,
                'XC_functional': 'LDA',
                'XC_authors': 'CA',
                'SolutionMethod': 'diagon',
                'ElectronicTemperature': 80.0,
                'DM_Tolerance': 1.0e-3,
                'MD_MaxForceTol': 0.05,
                'download_pseudos': False,
            })

        # Remove arquivo temporário
        import os
        os.remove('test.xyz')

        # Deve retornar um arquivo FDF para download
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.fdf', response['Content-Disposition'])

    def test_post_view_with_preview(self):
        """Testa POST com preview (não download)."""
        xyz_content = "2\nTest\nH  0.0  0.0  0.0\nO  1.0  0.0  0.0"

        with open('test.xyz', 'w') as f:
            f.write(xyz_content)

        with open('test.xyz', 'rb') as f:
            response = self.client.post(reverse('convert'), {
                'xyz_file': f,
                'system_name': 'TestSystem',
                'lattice_constant': 1.0,
                'cell_size_x': 50.0,
                'cell_size_y': 50.0,
                'cell_size_z': 50.0,
                'PAO_BasisSize': 'DZP',
                'preview': 'true',  # Solicita preview
            })

        import os
        os.remove('test.xyz')

        # Deve retornar a página com preview
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/upload.html')

    def test_post_view_with_invalid_data(self):
        """Testa POST com dados inválidos."""
        response = self.client.post(reverse('convert'), {
            # Arquivo XYZ ausente - deve falhar
            'system_name': 'TestSystem',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/upload.html')
        # Deve conter erros de formulário
        self.assertContains(response, 'error')

    def test_post_view_anonymous_user(self):
        """Testa POST com usuário anônimo (deve funcionar)."""
        self.client.logout()

        xyz_content = "1\nTest\nH  0.0  0.0  0.0"

        with open('test.xyz', 'w') as f:
            f.write(xyz_content)

        with open('test.xyz', 'rb') as f:
            response = self.client.post(reverse('convert'), {
                'xyz_file': f,
                'system_name': 'TestSystem',
                'lattice_constant': 1.0,
                'cell_size_x': 50.0,
                'cell_size_y': 50.0,
                'cell_size_z': 50.0,
                'padding': 1.0,
                'PAO_BasisSize': 'DZP',
                'PAO_EnergyShift': 0.05,
                'MD_TypeOfRun': 'CG',
                'MD_NumCGsteps': 500,
                'MD_MaxForceTol': 0.05,
                'MaxSCFIterations': 100,
                'MeshCutoff': 200.0,
                'DM_MixingWeight': 0.10,
                'DM_NumberPulay': 3,
                'DM_Tolerance': 1.0e-3,
                'WriteMullikenPop': 1,
                'XC_functional': 'LDA',
                'XC_authors': 'CA',
                'SolutionMethod': 'diagon',
                'ElectronicTemperature': 80.0,
                'download_pseudos': False,
            })

        import os
        os.remove('test.xyz')

        # Deve funcionar mesmo para usuários anônimos
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')


class DownloadFdfTests(TestCase):
    """Testes para a view download_fdf."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

        # Cria uma conversão de teste
        self.conversion = ConversionHistory.objects.create(
            user=self.user,
            uploaded_file=None,
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

    def test_download_fdf_valid(self):
        """Testa download de FDF válido."""
        response = self.client.get(reverse('download_fdf', args=[self.conversion.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])

        # Verifica se o contador foi incrementado
        self.conversion.refresh_from_db()
        self.assertEqual(self.conversion.download_count, 1)

    def test_download_fdf_invalid_id(self):
        """Testa download com ID inválido."""
        response = self.client.get(reverse('download_fdf', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_download_fdf_other_user(self):
        """Testa download de conversão de outro usuário."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        other_conversion = ConversionHistory.objects.create(
            user=other_user,
            uploaded_file=None,
            original_filename='other.xyz',
            system_name='Other System',
            fdf_content='%block other\n%endblock',
            parameters={},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )

        response = self.client.get(reverse('download_fdf', args=[other_conversion.id]))
        self.assertEqual(response.status_code, 404)

    def test_download_fdf_unauthenticated(self):
        """Testa download sem autenticação."""
        self.client.logout()
        response = self.client.get(reverse('download_fdf', args=[self.conversion.id]))
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class DeleteHistoryTests(TestCase):
    """Testes para a view delete_history."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

        self.conversion = ConversionHistory.objects.create(
            user=self.user,
            uploaded_file=None,
            original_filename='test.xyz',
            system_name='Test System',
            fdf_content='test',
            parameters={},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )

    def test_delete_history_valid(self):
        """Testa exclusão válida do histórico."""
        self.assertEqual(ConversionHistory.objects.count(), 1)

        response = self.client.get(reverse('delete_history', args=[self.conversion.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('converter_history'))
        self.assertEqual(ConversionHistory.objects.count(), 0)

    def test_delete_history_invalid_id(self):
        """Testa exclusão com ID inválido."""
        response = self.client.get(reverse('delete_history', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_history_other_user(self):
        """Testa exclusão de histórico de outro usuário."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        other_conversion = ConversionHistory.objects.create(
            user=other_user,
            uploaded_file=None,
            original_filename='other.xyz',
            system_name='Other System',
            fdf_content='other',
            parameters={},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )

        response = self.client.get(reverse('delete_history', args=[other_conversion.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ConversionHistory.objects.count(), 2)  # Nenhuma exclusão


class DownloadPseudosTests(TestCase):
    """Testes para a view download_pseudos."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

        # Cria diretório de pseudopotenciais de teste
        import os
        self.test_pseudos_dir = '/tmp/test_pseudos_download'
        os.makedirs(self.test_pseudos_dir, exist_ok=True)

        # Cria alguns arquivos .psf de teste
        for element in ['H', 'O', 'C']:
            pseudo_path = os.path.join(self.test_pseudos_dir, f"{element}.lda.psf")
            with open(pseudo_path, 'w') as f:
                f.write(f"Pseudopotential content for {element}")

        # Configura settings temporariamente
        from django.conf import settings
        self.original_pseudos_dir = getattr(settings, 'PSEUDOPOTENTIALS_DIR', None)
        settings.PSEUDOPOTENTIALS_DIR = self.test_pseudos_dir

        # Cria uma conversão de teste com conteúdo FDF que contém ChemicalSpeciesLabel
        fdf_content = """SystemName Test System
NumberOfAtoms 3
NumberOfSpecies 3
%block ChemicalSpeciesLabel
1 1 H.lda
2 8 O.lda
3 6 C.lda
%endblock ChemicalSpeciesLabel
AtomicCoordinatesFormat Ang
%block AtomicCoordinatesAndAtomicSpecies
0.0 0.0 0.0 1
1.0 0.0 0.0 2
0.0 1.0 0.0 3
%endblock AtomicCoordinatesAndAtomicSpecies"""

        self.conversion = ConversionHistory.objects.create(
            user=self.user,
            uploaded_file=None,
            original_filename='test.xyz',
            system_name='Test System',
            fdf_content=fdf_content,
            parameters={'meshcutoff': '200 Ry'},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )

    def tearDown(self):
        # Restaura configuração original
        from django.conf import settings
        if self.original_pseudos_dir:
            settings.PSEUDOPOTENTIALS_DIR = self.original_pseudos_dir
        else:
            delattr(settings, 'PSEUDOPOTENTIALS_DIR')

        # Limpa diretório de teste
        import shutil
        if os.path.exists(self.test_pseudos_dir):
            shutil.rmtree(self.test_pseudos_dir)

    def test_download_pseudos_valid(self):
        """Testa download de pseudopotenciais válido."""
        response = self.client.get(reverse('download_pseudos', args=[self.conversion.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('test-system_pseudos.zip', response['Content-Disposition'])

        # Verifica se o conteúdo é um ZIP válido
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            # Deve conter arquivo .fdf
            self.assertIn('test-system.fdf', zip_f.namelist())

            # Deve conter arquivos .psf para as espécies
            self.assertIn('H.lda.psf', zip_f.namelist())
            self.assertIn('O.lda.psf', zip_f.namelist())
            self.assertIn('C.lda.psf', zip_f.namelist())

            # Verifica conteúdo do arquivo .fdf
            fdf_data = zip_f.read('test-system.fdf').decode('utf-8')
            self.assertIn('SystemName Test System', fdf_data)

    def test_download_pseudos_invalid_id(self):
        """Testa download com ID inválido."""
        response = self.client.get(reverse('download_pseudos', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_download_pseudos_other_user(self):
        """Testa download de pseudopotenciais de conversão de outro usuário."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        other_conversion = ConversionHistory.objects.create(
            user=other_user,
            uploaded_file=None,
            original_filename='other.xyz',
            system_name='Other System',
            fdf_content='%block ChemicalSpeciesLabel\n1 1 H.lda\n%endblock',
            parameters={},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )

        response = self.client.get(reverse('download_pseudos', args=[other_conversion.id]))
        self.assertEqual(response.status_code, 404)

    def test_download_pseudos_unauthenticated(self):
        """Testa download de pseudopotenciais sem autenticação."""
        self.client.logout()
        response = self.client.get(reverse('download_pseudos', args=[self.conversion.id]))
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_download_pseudos_missing_pseudos_dir(self):
        """Testa download quando diretório de pseudos não está configurado."""
        from django.conf import settings
        # Remove configuração temporariamente
        if hasattr(settings, 'PSEUDOPOTENTIALS_DIR'):
            delattr(settings, 'PSEUDOPOTENTIALS_DIR')

        response = self.client.get(reverse('download_pseudos', args=[self.conversion.id]))

        # Deve retornar ZIP mesmo sem arquivos .psf
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        # Verifica se contém apenas o arquivo .fdf
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            self.assertIn('test-system.fdf', zip_f.namelist())
            # Não deve conter arquivos .psf
            self.assertNotIn('H.lda.psf', zip_f.namelist())

        # Restaura configuração
        settings.PSEUDOPOTENTIALS_DIR = self.test_pseudos_dir

    def test_download_pseudos_missing_pseudo_file(self):
        """Testa download quando algum arquivo .psf está faltando."""
        # Remove um arquivo .psf do diretório de teste
        import os
        os.remove(os.path.join(self.test_pseudos_dir, 'O.lda.psf'))

        response = self.client.get(reverse('download_pseudos', args=[self.conversion.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        # Verifica se contém os arquivos disponíveis
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            self.assertIn('test-system.fdf', zip_f.namelist())
            self.assertIn('H.lda.psf', zip_f.namelist())
            self.assertIn('C.lda.psf', zip_f.namelist())
            # 'O.lda.psf' não deve estar presente
            self.assertNotIn('O.lda.psf', zip_f.namelist())

    def test_download_pseudos_no_chemical_species(self):
        """Testa download quando FDF não contém ChemicalSpeciesLabel."""
        # Cria conversão sem ChemicalSpeciesLabel
        conv_no_species = ConversionHistory.objects.create(
            user=self.user,
            uploaded_file=None,
            original_filename='no_species.xyz',
            system_name='No Species',
            fdf_content='SystemName No Species\nNumberOfAtoms 1',
            parameters={},
            conversion_date=timezone.now(),
            completion_date=timezone.now(),
            file_size=1024,
            status='completed',
            error_message='',
            download_count=0
        )

        response = self.client.get(reverse('download_pseudos', args=[conv_no_species.id]))

        # Deve retornar ZIP com apenas o arquivo .fdf
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zip_f:
            self.assertEqual(len(zip_f.namelist()), 1)
            self.assertIn('no-species.fdf', zip_f.namelist())
