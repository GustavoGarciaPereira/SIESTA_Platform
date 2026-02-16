import io
import os
import zipfile
import hashlib
import json
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views import View
from django.utils.decorators import method_decorator

from .forms import (
    SIESTAParametersForm
)
from .models import UploadedFile, ConversionHistory, SavedConfiguration
class ConvertView(View):
    template_name = 'converter/upload.html'

    # Tabela periódica mínima (principais elementos para biomoléculas)
    PT = {'H':1, 'C':6, 'N':7, 'O':8, 'F':9, 'P':15, 'S':16, 'Cl':17, 'Br':35, 'I':53}

    def get(self, request):
        form = SIESTAParametersForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SIESTAParametersForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        # Obtém dados do formulário
        xyz_file = request.FILES['xyz_file']
        params = form.cleaned_data

        # Se o nome do sistema não for fornecido, use o nome do arquivo
        system_name = params['system_name']
        if not system_name:
            system_name = xyz_file.name.rsplit('.', 1)[0]

        # Converte o arquivo
        fdf_content, unique_species = self.convert_xyz_to_fdf(xyz_file, system_name, params)

        # Registrar histórico se usuário estiver autenticado
        conversion_history = None
        if request.user.is_authenticated:
            try:
                # Calcular checksum do conteúdo
                xyz_file.seek(0)
                content = xyz_file.read().decode('utf-8')
                checksum = hashlib.sha256(content.encode()).hexdigest()
                
                # 1. Criar registro do arquivo enviado
                uploaded = UploadedFile.objects.create(
                    user=request.user,
                    file=xyz_file,
                    original_name=xyz_file.name,
                    file_type='xyz',
                    size=xyz_file.size,
                    checksum=checksum,
                    upload_date=datetime.now(),
                    is_temp=False
                )
                
                # 2. Salvar histórico
                conversion_history = ConversionHistory.objects.create(
                    user=request.user,
                    uploaded_file=uploaded,
                    original_filename=xyz_file.name,
                    system_name=system_name,
                    fdf_content=fdf_content,
                    parameters=params,
                    conversion_date=datetime.now(),
                    completion_date=datetime.now(),
                    file_size=xyz_file.size,
                    status='completed',
                    error_message='',
                    download_count=0
                )
                
                # Guardar o ID da conversão na sessão para uso posterior
                request.session['last_conversion_id'] = conversion_history.id
                
            except Exception as e:
                # Log do erro, mas não interrompe o fluxo principal
                print(f"Erro ao registrar histórico: {e}")

        if 'preview' in request.POST:
            # Lógica de preview permanece a mesma
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'content': fdf_content,
                    'filename': f"{slugify(system_name)}.fdf"
                })
            else:
                return render(request, self.template_name, {
                    'form': form,
                    'preview_content': fdf_content,
                    'preview_filename': f"{slugify(system_name)}.fdf"
                })
        else:
            # ### ALTERADO ###: Lógica de download com opção de ZIP
            if params.get('download_pseudos'):
                # Chama a função para criar o arquivo ZIP
                zip_response = self.create_zip_archive(request, fdf_content, system_name, unique_species)
                return zip_response
            else:
                # Comportamento antigo: baixar apenas o .fdf
                response = HttpResponse(fdf_content, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="{slugify(system_name)}.fdf"'
                return response


    def create_zip_archive(self, request, fdf_content, system_name, unique_species):
        """Cria um arquivo ZIP em memória contendo o .fdf e os arquivos .psf necessários."""
        
        # Verifica se o diretório de pseudopotenciais foi configurado
        if not hasattr(settings, 'PSEUDOPOTENTIALS_DIR') or not os.path.isdir(settings.PSEUDOPOTENTIALS_DIR):
            messages.error(request, "O diretório de pseudopotenciais não está configurado no servidor. Apenas o arquivo .fdf será baixado.")
            response = HttpResponse(fdf_content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{slugify(system_name)}.fdf"'
            return response

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_f:
            # 1. Adiciona o arquivo .fdf ao zip
            fdf_filename = f"{slugify(system_name)}.fdf"
            zip_f.writestr(fdf_filename, fdf_content)

            # 2. Adiciona os arquivos .psf ao zip
            pseudos_dir = settings.PSEUDOPOTENTIALS_DIR
            for sym in unique_species:
                # Assumindo que o funcional é 'lda' por enquanto, como no seu código original.
                # Para maior flexibilidade, isso poderia vir do formulário.
                pseudo_filename = f"{sym}.lda.psf" 
                pseudo_path = os.path.join(pseudos_dir, pseudo_filename)

                if os.path.exists(pseudo_path):
                    # Adiciona o arquivo ao zip sem a estrutura de diretórios do servidor
                    zip_f.write(pseudo_path, arcname=pseudo_filename)
                else:
                    # Informa ao usuário que um arquivo .psf não foi encontrado
                    messages.warning(request, f"Aviso: O arquivo de pseudopotencial '{pseudo_filename}' não foi encontrado no servidor e não foi incluído no .zip.")

        # Prepara a resposta HTTP para o arquivo ZIP
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{slugify(system_name)}.zip"'
        return response



    def read_xyz(self, file_obj):
        """Lê um arquivo XYZ e retorna uma lista de tuplas (símbolo, x, y, z)"""
        # Decodifica cada linha para texto
        lines = [line.decode('utf-8').strip() for line in file_obj]

        n = int(lines[0])  # Número de átomos
        comment = lines[1]  # Linha de comentário
        atoms = []

        for i in range(2, 2 + n):
            if i < len(lines) and lines[i].strip():
                parts = lines[i].split()
                if len(parts) >= 4:
                    symbol = parts[0]
                    x, y, z = map(float, parts[1:4])
                    atoms.append((symbol, x, y, z))

        return atoms

    def bounding_box(self, atoms):
        """Calcula a caixa delimitadora para os átomos"""
        xs, ys, zs = zip(*[(a[1], a[2], a[3]) for a in atoms])
        return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

    def convert_xyz_to_fdf(self, xyz_file, system_name, params):
        """Converte um arquivo XYZ para formato FDF e retorna o conteúdo e as espécies únicas."""
        if hasattr(xyz_file, 'seek'):
            xyz_file.seek(0)

        atoms = self.read_xyz(xyz_file)
        
        # ### ALTERADO ###: Simplifiquei a identificação de espécies
        unique_species = sorted(list(set(atom[0] for atom in atoms)))

        output = io.StringIO()

        # ... (lógica de escrita do FDF, sem alterações) ...
        output.write(f"SystemName    {system_name}\n")
        output.write(f"SystemLabel    {system_name}\n")
        output.write(f"NumberOfAtoms    {len(atoms)}\n")
        output.write(f"NumberOfSpecies  {len(unique_species)}\n")
        
        dici = {}
        output.write("%block ChemicalSpeciesLabel\n")
        for idx, sym in enumerate(unique_species, start=1):
            atomic_num = self.PT.get(sym, 0)
            dici[sym] = idx
            # ### NOTA ###: O '.lda' está fixo aqui. Se você usar outros funcionais (GGA, etc)
            # que exigem arquivos .psf diferentes (ex: C.pbe.psf), esta linha precisará
            # ser tornada dinâmica com base no valor de XC.functional do formulário.
            output.write(f" {idx}   {atomic_num}    {sym}.lda\n")
        output.write("%endblock ChemicalSpeciesLabel\n\n")

        cell_size_x = params.get('cell_size_x', 50.0)
        cell_size_y = params.get('cell_size_y', 50.0)
        cell_size_z = params.get('cell_size_z', 50.0)
        lc = params.get('lattice_constant', 1.0)

        output.write(f"LatticeConstant {lc:.1f} Ang\n")
        output.write("%block LatticeVectors\n")
        output.write(f"  {cell_size_x:.3f} 0.000  0.000\n")
        output.write(f"  0.000  {cell_size_y:.3f} 0.000\n")
        output.write(f"  0.000  0.000  {cell_size_z:.3f}\n")
        output.write("%endblock LatticeVectors\n\n")

        output.write("AtomicCoordinatesFormat NotScaledCartesianAng\n")
        output.write("AtomCoorFormatOut   NotScaledCartesianAng\n")
        output.write("%block AtomicCoordinatesAndAtomicSpecies \n")

        for sym, x, y, z in atoms:
            species_idx = dici.get(sym)
            if species_idx:
                output.write(f"   {x:<10.6f}    {y:<10.6f}    {z:<10.6f}    {species_idx}\n")

        output.write("%endblock AtomicCoordinatesAndAtomicSpecies\n\n")

        # ... (resto da escrita dos parâmetros, sem alterações) ...
        output.write(f"PAO.BasisSize    {params.get('PAO_BasisSize', 'DZP')}\n")
        output.write(f"PAO.EnergyShift   {params.get('PAO_EnergyShift', 0.05)} eV\n")
        output.write(f"MD.TypeOfRun    {params.get('MD_TypeOfRun', 'CG')}\n")
        output.write(f"MD.NumCGsteps    {params.get('MD_NumCGsteps', 1000)}\n")
        output.write(f"MaxSCFIterations  {params.get('MaxSCFIterations', 100)}\n")
        if params.get('SpinPolarized', True):
            output.write("SpinPolarized true\n")
        output.write(f"MD.MaxForceTol    {params.get('MD_MaxForceTol', 0.05)} eV/Ang\n")
        output.write(f"MeshCutoff    {params.get('MeshCutoff', 200.0)} Ry\n")
        if params.get('DM_UseSaveDM', True):
            output.write("DM.UseSaveDM    true\n")
        if params.get('UseSaveData', True):
            output.write("UseSaveData    true\n")
        if params.get('MD_UseSaveXV', True):
            output.write("MD.UseSaveXV    true\n")
        if params.get('MD_UseSaveCG', True):
            output.write("MD.UseSaveCG    true\n")
        output.write(f"DM.MixingWeight   {params.get('DM_MixingWeight', 0.10):.2f}\n")
        output.write(f"DM.NumberPulay    {params.get('DM_NumberPulay', 3)}\n")
        if params.get('WriteCoorXmol', True):
            output.write("WriteCoorXmol\n")
        output.write(f"WriteMullikenPop {params.get('WriteMullikenPop', 1)}\n")
        output.write(f"XC.functional    {params.get('XC_functional', 'LDA')}\n")
        output.write(f"XC.authors    {params.get('XC_authors', 'CA')} \n")
        output.write(f"SolutionMethod {params.get('SolutionMethod', 'diagon')}\n")
        output.write(f"ElectronicTemperature  {params.get('ElectronicTemperature', 80)} meV\n")
        output.write(f"DM.Tolerance    {params.get('DM_Tolerance', 1.0E-3):.8E}\n")

        # ### ALTERADO ###: Retorna o conteúdo e a lista de espécies
        return output.getvalue(), unique_species


# History views
@login_required
def history_view(request):
    """View para exibir o histórico de conversões do usuário."""
    conversions = ConversionHistory.objects.filter(user=request.user).order_by('-conversion_date')
    return render(request, 'converter/history.html', {'conversions': conversions})


@login_required
def download_fdf(request, conv_id):
    """View para baixar o arquivo FDF de uma conversão específica."""
    try:
        conv = ConversionHistory.objects.get(id=conv_id, user=request.user)
    except ConversionHistory.DoesNotExist:
        raise Http404("Conversão não encontrada.")
    
    response = HttpResponse(conv.fdf_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{slugify(conv.system_name)}.fdf"'
    
    # Incrementar contador de downloads
    conv.download_count += 1
    conv.save()
    
    return response


@login_required
def download_pseudos(request, conv_id):
    """View para baixar pseudopotenciais de uma conversão específica."""
    conv = get_object_or_404(ConversionHistory, id=conv_id, user=request.user)
    
    # Extrair elementos do conteúdo FDF
    # Procura por linhas que contenham ChemicalSpeciesLabel
    elements = []
    lines = conv.fdf_content.split('\n')
    in_block = False
    for line in lines:
        if '%block ChemicalSpeciesLabel' in line:
            in_block = True
            continue
        if '%endblock ChemicalSpeciesLabel' in line:
            break
        if in_block and line.strip():
            parts = line.strip().split()
            if len(parts) >= 3:
                # Formato: "idx atomic_number symbol.lda"
                symbol_part = parts[2]
                # Remove o sufixo .lda
                if '.' in symbol_part:
                    symbol = symbol_part.split('.')[0]
                    elements.append(symbol)
    
    # Gerar o zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Adicionar o arquivo FDF
        fdf_filename = f"{slugify(conv.system_name)}.fdf"
        zip_file.writestr(fdf_filename, conv.fdf_content)
        
        # Adicionar pseudopotenciais
        pseudos_dir = settings.PSEUDOPOTENTIALS_DIR if hasattr(settings, 'PSEUDOPOTENTIALS_DIR') else 'pseudos'
        for el in elements:
            pseudo_filename = f"{el}.lda.psf"
            pseudo_path = os.path.join(pseudos_dir, pseudo_filename)
            if os.path.exists(pseudo_path):
                zip_file.write(pseudo_path, arcname=pseudo_filename)
    
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{slugify(conv.system_name)}_pseudos.zip"'
    
    return response


# Saved Configuration views
@login_required
def save_configuration(request):
    """View para salvar uma configuração atual."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        parameters = request.POST.get('parameters')  # JSON string vindo do formulário
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Nome é obrigatório'}, status=400)
        
        try:
            # Converter string JSON para dict
            params_dict = json.loads(parameters) if parameters else {}
            
            # Criar configuração salva
            config = SavedConfiguration.objects.create(
                user=request.user,
                name=name,
                description=description,
                parameters=params_dict,
                is_default=False,
                created_at=datetime.now(),
                last_used=datetime.now(),
                use_count=0
            )
            
            return JsonResponse({'status': 'ok', 'config_id': config.id})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Parâmetros inválidos'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@login_required
def my_configurations(request):
    """View para listar as configurações salvas do usuário."""
    configs = SavedConfiguration.objects.filter(user=request.user).order_by('-last_used')
    return render(request, 'converter/my_configs.html', {'configs': configs})


@login_required
def load_configuration(request, config_id):
    """View para carregar uma configuração salva."""
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    
    # Atualizar contador de uso
    config.use_count += 1
    config.last_used = datetime.now()
    config.save()
    
    # Armazenar configuração na sessão
    request.session['loaded_config'] = config.parameters
    request.session['loaded_config_name'] = config.name
    
    messages.success(request, f'Configuração "{config.name}" carregada com sucesso!')
    return redirect('convert')


@login_required
def delete_configuration(request, config_id):
    """View para excluir uma configuração salva."""
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    config_name = config.name
    config.delete()
    
    messages.success(request, f'Configuração "{config_name}" excluída com sucesso!')
    return redirect('my_configurations')
