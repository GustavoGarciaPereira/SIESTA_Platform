# Built-in Python imports
import hashlib
import io
import json
import logging
import os
import zipfile
from datetime import datetime

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views import View

# Configure logger
logger = logging.getLogger(__name__)

# Third-party imports
# (none currently)

# Local imports
from .forms import SIESTAParametersForm
from .models import ConversionHistory, SavedConfiguration, UploadedFile
from .utils import convert_xyz_to_fdf, create_zip_archive, PT
class ConvertView(View):
    """View para conversão de arquivos XYZ para formato FDF do SIESTA.
    
    Esta view permite upload de arquivos XYZ, visualização 3D da molécula,
    configuração de parâmetros de simulação SIESTA e geração de arquivos FDF.
    
    Attributes:
        template_name (str): Nome do template a ser renderizado
        PT (dict): Tabela periódica mínima para elementos comuns em biomoléculas
    """
    template_name = 'converter/upload.html'

    # Tabela periódica mínima (principais elementos para biomoléculas)
    PT = {'H':1, 'C':6, 'N':7, 'O':8, 'F':9, 'P':15, 'S':16, 'Cl':17, 'Br':35, 'I':53}

    def get(self, request):
        """Processa requisição GET para exibir formulário de conversão.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse: Resposta HTTP com formulário de conversão
        """
        # Verificar se há configuração carregada na sessão
        loaded_config = request.session.get('loaded_config')
        if loaded_config:
            # Criar formulário com dados da configuração carregada
            form = SIESTAParametersForm(initial=loaded_config)
            # Limpar a configuração da sessão após usar (opcional, mas evita reuso acidental)
            # request.session.pop('loaded_config', None)
            # request.session.pop('loaded_config_name', None)
        else:
            form = SIESTAParametersForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Processa requisição POST para conversão XYZ para FDF.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse: Resposta HTTP com preview ou download
        """
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
        fdf_content, unique_species = convert_xyz_to_fdf(xyz_file, system_name, params, self.PT)

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
                logger.error(f"Erro ao registrar histórico: {e}")

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
                zip_response = create_zip_archive(request, fdf_content, system_name, unique_species)
                return zip_response
            else:
                # Comportamento antigo: baixar apenas o .fdf
                response = HttpResponse(fdf_content, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="{slugify(system_name)}.fdf"'
                return response


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
