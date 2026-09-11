# Built-in Python imports
import hashlib
import json
import logging
# Django imports
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.decorators.http import require_POST

# Configure logger
logger = logging.getLogger(__name__)

# Third-party imports
# (none currently)

# Local imports
from .forms import SIESTAParametersForm
from .models import ConversionHistory, SavedConfiguration, SimulationPreset, UploadedFile
from .utils import convert_xyz_to_fdf, create_zip_archive, read_xyz, bounding_box
from .periodic_table import ATOMIC_NUMBER_TO_SYMBOL, SYMBOL_TO_ATOMIC_NUMBER as PT


class ConvertView(View):
    """View para conversão de arquivos XYZ para formato FDF do SIESTA.

    Esta view permite upload de arquivos XYZ, visualização 3D da molécula,
    configuração de parâmetros de simulação SIESTA e geração de arquivos FDF.

    Attributes:
        template_name (str): Nome do template a ser renderizado
    """
    template_name = 'converter/upload.html'

    def _context(self, form, **extra):
        """Contexto comum, incluindo tabela periódica e presets para o JS."""
        presets = list(SimulationPreset.objects.filter(is_active=True))
        context = {
            'form': form,
            'periodic_table_json': json.dumps(ATOMIC_NUMBER_TO_SYMBOL),
            'presets': presets,
            'presets_data': [
                {'id': preset.id, 'parameters': preset.parameters}
                for preset in presets
            ],
        }
        context.update(extra)
        return context

    def get(self, request):
        """Processa requisição GET para exibir formulário de conversão.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse: Resposta HTTP com formulário de conversão
        """
        # Verificar se há configuração carregada na sessão
        loaded_config = request.session.pop('loaded_config', None)
        request.session.pop('loaded_config_name', None)
        if loaded_config:
            # Criar formulário com dados da configuração carregada
            form = SIESTAParametersForm(initial=loaded_config)
        else:
            form = SIESTAParametersForm()
        return render(request, self.template_name, self._context(form))

    def post(self, request):
        """Processa requisição POST para conversão XYZ para FDF.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse: Resposta HTTP com preview ou download
        """
        form = SIESTAParametersForm(request.POST, request.FILES)

        def _invalid_response():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                message = _('Formulário inválido.')
                for field_errors in form.errors.get_json_data().values():
                    if field_errors:
                        message = field_errors[0]['message']
                        break
                return JsonResponse({'status': 'error', 'message': message}, status=400)
            return render(request, self.template_name, self._context(form))

        if not form.is_valid():
            return _invalid_response()

        # Obtém dados do formulário
        xyz_file = request.FILES['xyz_file']
        params = form.cleaned_data

        # Se o nome do sistema não for fornecido, use o nome do arquivo
        system_name = params['system_name']
        if not system_name:
            system_name = xyz_file.name.rsplit('.', 1)[0]
        system_name = system_name or 'system'

        try:
            # Calcular dimensões da molécula e ajustar célula com padding
            xyz_file.seek(0)
            # Atenção: não usar "_" aqui — ele é o gettext importado.
            atoms, _atomic_numbers_detected = read_xyz(xyz_file)
            if atoms:
                x_min, x_max, y_min, y_max, z_min, z_max = bounding_box(atoms)
                mol_dx = x_max - x_min
                mol_dy = y_max - y_min
                mol_dz = z_max - z_min
                pad = params.get('padding', 1.0)
                rec_x = mol_dx + 2 * pad
                rec_y = mol_dy + 2 * pad
                rec_z = mol_dz + 2 * pad

                if params['cell_size_x'] < rec_x:
                    messages.info(request,
                        _("Dimensão X da célula ajustada de %(old).1f "
                          "para %(new).1f Å (molécula: %(mol).1f Å + padding: %(pad).1f Å).")
                        % {'old': params['cell_size_x'], 'new': rec_x, 'mol': mol_dx, 'pad': pad})
                    params['cell_size_x'] = rec_x
                if params['cell_size_y'] < rec_y:
                    messages.info(request,
                        _("Dimensão Y da célula ajustada de %(old).1f "
                          "para %(new).1f Å (molécula: %(mol).1f Å + padding: %(pad).1f Å).")
                        % {'old': params['cell_size_y'], 'new': rec_y, 'mol': mol_dy, 'pad': pad})
                    params['cell_size_y'] = rec_y
                if params['cell_size_z'] < rec_z:
                    messages.info(request,
                        _("Dimensão Z da célula ajustada de %(old).1f "
                          "para %(new).1f Å (molécula: %(mol).1f Å + padding: %(pad).1f Å).")
                        % {'old': params['cell_size_z'], 'new': rec_z, 'mol': mol_dz, 'pad': pad})
                    params['cell_size_z'] = rec_z

            # Converte o arquivo
            fdf_content, unique_species, atomic_numbers_detected = convert_xyz_to_fdf(
                xyz_file, system_name, params, PT
            )
        except (ValueError, UnicodeDecodeError) as e:
            form.add_error('xyz_file', e)
            return _invalid_response()

        if atomic_numbers_detected:
            messages.warning(
                request,
                _("Números atômicos detectados no arquivo XYZ. "
                  "Eles foram automaticamente convertidos para símbolos químicos."),
            )

        if params.get('XC_functional', 'LDA') != 'LDA':
            messages.warning(
                request,
                _("O servidor disponibiliza apenas pseudopotenciais LDA. "
                  "O FDF referencia arquivos .lda.psf independentemente do funcional escolhido."),
            )

        # Registrar histórico apenas para usuários autenticados
        # (conversões anônimas não têm dono e não podem ser acessadas depois)
        if request.user.is_authenticated:
            try:
                # Calcular checksum do conteúdo
                xyz_file.seek(0)
                content = xyz_file.read().decode('utf-8')
                checksum = hashlib.sha256(content.encode()).hexdigest()

                uploaded = UploadedFile.objects.create(
                    user=request.user,
                    file=xyz_file,
                    original_name=xyz_file.name,
                    file_type='xyz',
                    size=xyz_file.size,
                    checksum=checksum,
                    upload_date=timezone.now(),
                    is_temp=False
                )

                # Serializar parâmetros excluindo campos não serializáveis (ex: InMemoryUploadedFile)
                serializable_params = {
                    k: v for k, v in params.items()
                    if isinstance(v, (str, int, float, bool, list, dict, type(None)))
                }

                now = timezone.now()
                conversion_history = ConversionHistory.objects.create(
                    user=request.user,
                    uploaded_file=uploaded,
                    original_filename=xyz_file.name,
                    system_name=system_name,
                    fdf_content=fdf_content,
                    parameters=serializable_params,
                    conversion_date=now,
                    completion_date=now,
                    file_size=xyz_file.size,
                    status='completed',
                    error_message='',
                    download_count=0
                )

                request.session['last_conversion_id'] = conversion_history.id

            except Exception as e:
                # Log do erro, mas não interrompe o fluxo principal
                logger.error(f"Erro ao registrar histórico: {e}")

        if 'preview' in request.POST:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'content': fdf_content,
                    'filename': f"{slugify(system_name)}.fdf"
                })
            return render(request, self.template_name, self._context(
                form,
                preview_content=fdf_content,
                preview_filename=f"{slugify(system_name)}.fdf",
            ))

        if params.get('download_pseudos'):
            return create_zip_archive(request, fdf_content, system_name, unique_species)

        response = HttpResponse(fdf_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{slugify(system_name)}.fdf"'
        return response


# History views
@login_required
def history_view(request):
    """View para exibir o histórico de conversões do usuário."""
    qs = ConversionHistory.objects.filter(user=request.user).order_by('-conversion_date')
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    conversions = paginator.get_page(page_number)
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
@require_POST
def delete_history(request, conv_id):
    """View para excluir uma entrada do histórico de conversões."""
    conv = get_object_or_404(ConversionHistory, id=conv_id, user=request.user)
    conv.delete()
    messages.success(request, _('Entrada do histórico excluída com sucesso.'))
    return redirect('converter_history')


def _extract_species_from_fdf(fdf_content):
    """Extrai os símbolos dos elementos do bloco ChemicalSpeciesLabel no FDF.

    Args:
        fdf_content (str): Conteúdo completo do arquivo FDF

    Returns:
        list: Lista de símbolos de elementos (ex: ['H', 'O', 'C'])
    """
    elements = []
    seen = set()
    in_block = False
    for line in fdf_content.split('\n'):
        if '%block ChemicalSpeciesLabel' in line:
            in_block = True
            continue
        if '%endblock ChemicalSpeciesLabel' in line:
            break
        if in_block and line.strip():
            parts = line.strip().split()
            if len(parts) >= 3:
                # Formato: "idx atomic_number symbol.XC" (ex: "1 6 C.lda")
                symbol_part = parts[2]
                if '.' in symbol_part:
                    symbol = symbol_part.split('.')[0]
                    if symbol not in seen:
                        seen.add(symbol)
                        elements.append(symbol)
    return elements


@login_required
def download_pseudos(request, conv_id):
    """View para baixar pseudopotenciais de uma conversão específica."""
    conv = get_object_or_404(ConversionHistory, id=conv_id, user=request.user)
    elements = _extract_species_from_fdf(conv.fdf_content)

    conv.download_count += 1
    conv.save(update_fields=['download_count'])

    return create_zip_archive(request, conv.fdf_content, conv.system_name, elements)


# Saved Configuration views
@login_required
@require_POST
def save_configuration(request):
    """View para salvar uma configuração atual (POST via AJAX)."""
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    parameters = request.POST.get('parameters')  # JSON string vindo do formulário

    if not name:
        return JsonResponse({'status': 'error', 'message': _('Nome é obrigatório')}, status=400)

    try:
        # Converter string JSON para dict
        params_dict = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': _('Parâmetros inválidos')}, status=400)

    try:
        config = SavedConfiguration.objects.create(
            user=request.user,
            name=name,
            description=description,
            parameters=params_dict,
            is_default=False,
            created_at=timezone.now(),
            last_used=timezone.now(),
            use_count=0
        )
    except Exception:
        logger.exception("Erro ao salvar configuração do usuário %s", request.user)
        return JsonResponse(
            {'status': 'error', 'message': _('Não foi possível salvar a configuração.')},
            status=400,
        )

    return JsonResponse({'status': 'ok', 'config_id': config.id})


@login_required
def my_configurations(request):
    """View para listar as configurações salvas do usuário."""
    configs = SavedConfiguration.objects.filter(user=request.user).order_by('-last_used')
    return render(request, 'converter/my_configs.html', {'configs': configs})


@login_required
@require_POST
def load_configuration(request, config_id):
    """View para carregar uma configuração salva."""
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    
    # Atualizar contador de uso
    config.use_count += 1
    config.last_used = timezone.now()
    config.save(update_fields=['use_count', 'last_used'])
    
    # Armazenar configuração na sessão
    request.session['loaded_config'] = config.parameters
    request.session['loaded_config_name'] = config.name
    
    messages.success(request, _('Configuração "%(name)s" carregada com sucesso!') % {'name': config.name})
    return redirect('convert')


@login_required
@require_POST
def delete_configuration(request, config_id):
    """View para excluir uma configuração salva."""
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    config_name = config.name
    config.delete()
    
    messages.success(request, _('Configuração "%(name)s" excluída com sucesso!') % {'name': config_name})
    return redirect('my_configurations')
