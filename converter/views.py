import os

from django.urls import reverse_lazy
import numpy as np
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .forms import UploadFileForm
from django.views import View
from django.views.generic import CreateView, TemplateView

# def xyz_to_fdf(input_xyz, output_fdf):
#     """
#     Converte um arquivo XYZ para FDF.

#     :param input_xyz: Caminho para o arquivo XYZ de entrada.
#     :param output_fdf: Caminho para o arquivo FDF de saída.
#     """
#     # Dicionário de conversão do símbolo atômico para o índice da espécie
#     species_map = {
#         'C': 1,
#         'N': 2,
#         'O': 3,
#         'H': 4,
#         'S': 5
#     }

#     # Ler o arquivo xyz
#     with open(input_xyz, 'r') as f:
#         lines = f.readlines()

#     # Primeira linha: número de átomos
#     num_atoms = int(lines[0].strip())

#     # Linhas de coordenadas começam após a linha do número de átomos
#     coord_lines = lines[2:]

#     # Preparar lista para armazenar dados atômicos
#     atoms = []
#     for line in coord_lines:
#         if line.strip():
#             parts = line.split()
#             symbol = parts[0]
#             x = float(parts[1])
#             y = float(parts[2])
#             z = float(parts[3])
#             if symbol not in species_map:
#                 raise ValueError(f"Elemento '{symbol}' não está mapeado para nenhuma espécie química.")
#             specie_index = species_map[symbol]
#             atoms.append((x, y, z, specie_index))

#     # Escrever o arquivo de saída .fdf exatamente conforme o gabarito fornecido
#     with open(output_fdf, 'w') as out:
#         # Cabeçalho do sistema
#         out.write("SystemName       Enoxaparin\n")
#         out.write("SystemLabel      Enoxaparin\n")
#         out.write(f"NumberOfAtoms    {num_atoms}\n")
#         out.write("NumberOfSpecies  5\n")
#         out.write("%block ChemicalSpeciesLabel\n")
#         out.write(" 1   6    C.lda\n")
#         out.write(" 2   7    N.lda\n")
#         out.write(" 3   8    O.lda\n")
#         out.write(" 4   1    H.lda\n")
#         out.write(" 5   16   S.lda\n")
#         out.write("%endblock ChemicalSpeciesLabel\n\n")

#         out.write("LatticeConstant 1.0 Ang\n")
#         out.write("%block LatticeVectors\n")
#         out.write("  50.000 0.000  0.000\n")
#         out.write("  0.000  50.000 0.000\n")
#         out.write("  0.000  0.000  50.000\n")
#         out.write("%endblock LatticeVectors\n\n")

#         out.write("AtomicCoordinatesFormat NotScaledCartesianAng\n")
#         out.write("AtomCoorFormatOut   NotScaledCartesianAng\n")
#         out.write("%block AtomicCoordinatesAndAtomicSpecies \n")

#         # Escrever coordenadas atômicas com índices conforme o gabarito
#         # Mantendo 3 espaços iniciais e o mesmo padrão de espaçamento
#         for (x, y, z, si) in atoms:
#             out.write(f"   {x:10.5f}        {y:10.5f}       {z:10.5f}      {si}\n")

#         out.write("%endblock AtomicCoordinatesAndAtomicSpecies\n\n")

#         # Demais parâmetros fixos exatamente conforme o gabarito
#         out.write("PAO.BasisSize     DZP\n")
#         out.write("PAO.EnergyShift   0.05 eV\n")
#         out.write("MD.TypeOfRun      CG\n")
#         out.write("MD.NumCGsteps     1000\n")
#         out.write("MaxSCFIterations  100\n")
#         out.write("SpinPolarized true\n")
#         out.write("MD.MaxForceTol    0.05 eV/Ang\n")
#         out.write("MeshCutoff        200.0 Ry\n")
#         out.write("DM.UseSaveDM     true\n")
#         out.write("UseSaveData      true\n")
#         out.write("MD.UseSaveXV     true\n")
#         out.write("MD.UseSaveCG     true\n")
#         out.write("DM.MixingWeight   0.10\n")
#         out.write("DM.NumberPulay    3\n")
#         out.write("WriteCoorXmol\n")
#         out.write("WriteMullikenPop 1\n")
#         out.write("XC.functional      LDA\n")
#         out.write("XC.authors        CA \n")
#         out.write("SolutionMethod diagon\n")
#         out.write("ElectronicTemperature  80 meV\n")
#         out.write("DM.Tolerance         0.1000000000E-02\n")

from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.text import slugify
from django import forms
import io
from collections import OrderedDict

from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.text import slugify
from django import forms
import io
from collections import OrderedDict

class SIESTAParametersForm(forms.Form):

    lattice_constant = forms.FloatField(
            label='LatticeConstant (Ang)',
            initial=1.0,  # Baseado em "LatticeConstant 1.0 Ang" no trecho de código original
            help_text="Valor da constante de rede em Angstroms. Os vetores da rede (abaixo) são multiplicados por este valor pelo SIESTA."
        )
    cell_size_x = forms.FloatField(
        label='Tamanho da Célula X (para Vetor A: [X, 0, 0])',
        initial=50.0, # Valor padrão conforme solicitado
        help_text="Componente X do primeiro vetor da rede (A_x). Valor adimensional, que será multiplicado pela LatticeConstant."
    )
    cell_size_y = forms.FloatField(
        label='Tamanho da Célula Y (para Vetor B: [0, Y, 0])',
        initial=50.0, # Valor padrão conforme solicitado
        help_text="Componente Y do segundo vetor da rede (B_y). Valor adimensional, que será multiplicado pela LatticeConstant."
    )
    cell_size_z = forms.FloatField(
        label='Tamanho da Célula Z (para Vetor C: [0, 0, Z])',
        initial=50.0, # Valor padrão conforme solicitado
        help_text="Componente Z do terceiro vetor da rede (C_z). Valor adimensional, que será multiplicado pela LatticeConstant."
    )


    # Upload e parâmetros básicos
    xyz_file = forms.FileField(label='Arquivo XYZ')
    system_name = forms.CharField(label='Nome do Sistema', required=False,
                                 help_text='Deixe em branco para usar o nome do arquivo')
    padding = forms.FloatField(label='Espaçamento de borda (Å)', initial=10.0, min_value=0.0)

    # Parâmetros de base
    PAO_BasisSize = forms.ChoiceField(
        label='PAO.BasisSize',
        choices=[('SZ', 'SZ'), ('DZ', 'DZ'), ('SZP', 'SZP'), ('DZP', 'DZP')],
        initial='DZP'
    )
    PAO_EnergyShift = forms.FloatField(
        label='PAO.EnergyShift (eV)',
        initial=0.05,
        min_value=0.001,
        help_text='Valor em eV'
    )

    # Parâmetros MD
    MD_TypeOfRun = forms.ChoiceField(
        label='MD.TypeOfRun',
        choices=[('CG', 'CG'), ('Verlet', 'Verlet'), ('Nose', 'Nose'),
                ('ParrinelloRahman', 'ParrinelloRahman'), ('NoseParrinelloRahman', 'NoseParrinelloRahman')],
        initial='CG'
    )
    MD_NumCGsteps = forms.IntegerField(
        label='MD.NumCGsteps',
        initial=500,
        min_value=1
    )
    MD_MaxForceTol = forms.FloatField(
        label='MD.MaxForceTol (eV/Ang)',
        initial=0.05,
        min_value=0.001
    )

    # Parâmetros SCF
    MaxSCFIterations = forms.IntegerField(
        label='MaxSCFIterations',
        initial=100,
        min_value=1
    )
    SpinPolarized = forms.BooleanField(
        label='SpinPolarized',
        initial=True,
        required=False
    )
    MeshCutoff = forms.FloatField(
        label='MeshCutoff (Ry)',
        initial=200.0,
        min_value=50.0
    )

    # Parâmetros DM
    DM_UseSaveDM = forms.BooleanField(
        label='DM.UseSaveDM',
        initial=True,
        required=False
    )
    UseSaveData = forms.BooleanField(
        label='UseSaveData',
        initial=True,
        required=False
    )
    MD_UseSaveXV = forms.BooleanField(
        label='MD.UseSaveXV',
        initial=True,
        required=False
    )
    MD_UseSaveCG = forms.BooleanField(
        label='MD.UseSaveCG',
        initial=True,
        required=False
    )
    DM_MixingWeight = forms.FloatField(
        label='DM.MixingWeight',
        initial=0.10,
        min_value=0.01,
        max_value=1.0
    )
    DM_NumberPulay = forms.IntegerField(
        label='DM.NumberPulay',
        initial=3,
        min_value=0
    )
    DM_Tolerance = forms.FloatField(
        label='DM.Tolerance',
        initial=1.0E-3,
        help_text='Valor em formato científico (ex: 1.0E-3)'
    )

    # Parâmetros de saída
    WriteCoorXmol = forms.BooleanField(
        label='WriteCoorXmol',
        initial=True,
        required=False
    )
    WriteMullikenPop = forms.IntegerField(
        label='WriteMullikenPop',
        initial=1,
        min_value=0,
        max_value=3
    )

    # Parâmetros de XC e solução
    XC_functional = forms.ChoiceField(
        label='XC.functional',
        choices=[('LDA', 'LDA'), ('GGA', 'GGA'), ('PBE', 'PBE')],
        initial='LDA'
    )
    XC_authors = forms.ChoiceField(
        label='XC.authors',
        choices=[('CA', 'CA'), ('PZ', 'PZ'), ('PW92', 'PW92'),
                ('PBE', 'PBE'), ('revPBE', 'revPBE'), ('RPBE', 'RPBE')],
        initial='CA'
    )
    SolutionMethod = forms.ChoiceField(
        label='SolutionMethod',
        choices=[('diagon', 'diagon'), ('OrderN', 'OrderN')],
        initial='diagon'
    )
    ElectronicTemperature = forms.FloatField(
        label='ElectronicTemperature (meV)',
        initial=80,
        min_value=0.0,
        help_text='Valor em meV'
    )

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
        fdf_content = self.convert_xyz_to_fdf(xyz_file, system_name, params)

        # Verifica se é uma solicitação de pré-visualização ou download
        if 'preview' in request.POST:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Retorna apenas o conteúdo para AJAX
                return JsonResponse({
                    'content': fdf_content,
                    'filename': f"{slugify(system_name)}.fdf"
                })
            else:
                # Renderiza a página com pré-visualização
                return render(request, self.template_name, {
                    'form': form,
                    'preview_content': fdf_content,
                    'preview_filename': f"{slugify(system_name)}.fdf"
                })
        else:
            # Prepara o arquivo para download
            response = HttpResponse(fdf_content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{slugify(system_name)}.fdf"'
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
        """Converte um arquivo XYZ para formato FDF do SIESTA mantendo as coordenadas originais"""
        # Restaurar o arquivo para o início (caso já tenha sido lido)
        if hasattr(xyz_file, 'seek'):
            xyz_file.seek(0)

        # Lê o arquivo XYZ
        atoms = self.read_xyz(xyz_file)

        # Mapeamento para os tipos de espécies específicos
        species_map = {
            'C': 1,
            'N': 2,
            'O': 3,
            'H': 4,
            'S': 5,
        }

        # Identifica espécies únicas presentes no arquivo
        unique_species = sorted([sym for sym in set(sym for sym, *_ in atoms) if sym in species_map])

        # Cria o arquivo FDF
        output = io.StringIO()

        output.write(f"SystemName    {system_name}\n")
        output.write(f"SystemLabel    {system_name}\n")  # Espaço após Label para corresponder ao exemplo
        output.write(f"NumberOfAtoms    {len(atoms)}\n")
        output.write(f"NumberOfSpecies  {len(unique_species)}\n")

        # Bloco de espécies químicas
        output.write("%block ChemicalSpeciesLabel\n")
        for sym in unique_species:
            species_num = species_map.get(sym, 0)
            atomic_num = self.PT.get(sym, 0)
            output.write(f" {species_num}   {atomic_num}    {sym}.lda\n")
        output.write("%endblock ChemicalSpeciesLabel\n\n")

        # Define o tamanho da célula de simulação (caixa)
        cell_size_x = params.get('cell_size_x', 50.0)  # Usar 50.0 como padrão
        cell_size_y = params.get('cell_size_y', 50.0)  # Usar 50.0 como padrão
        cell_size_z = params.get('cell_size_z', 50.0)  # Usar 50.0 como padrão
        lc = params.get('lattice_constant', 1.0)  # Usar 50.0 como padrão

        # Constante de rede e vetores
        output.write(f"LatticeConstant {lc:.1f} Ang\n")
        output.write("%block LatticeVectors\n")
        output.write(f"  {cell_size_x:.3f} 0.000  0.000\n")
        output.write(f"  0.000  {cell_size_y:.3f} 0.000\n")
        output.write(f"  0.000  0.000  {cell_size_z:.3f}\n")
        output.write("%endblock LatticeVectors\n\n")

        # Coordenadas atômicas
        output.write("AtomicCoordinatesFormat NotScaledCartesianAng\n")
        output.write("AtomCoorFormatOut   NotScaledCartesianAng\n")  # Linha necessária no formato esperado
        output.write("%block AtomicCoordinatesAndAtomicSpecies \n")

        # Escreve as coordenadas com formatação exata
        for sym, x, y, z in atoms:
            species_num = species_map.get(sym, 0)
            # '<10.5f' para formatação com 5 casas decimais e alinhamento à esquerda em campo de largura 10
            output.write(f"   {x:<10.6f}    {y:<10.6f}    {z:<10.6f}    {species_num}\n")

        output.write("%endblock AtomicCoordinatesAndAtomicSpecies\n\n")

        # Adiciona os parâmetros SIESTA do formulário
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

        return output.getvalue()


from django.contrib.auth import authenticate, login
from .forms import UserCreationForm
from django.views import View
from django.shortcuts import render, redirect

class HomeView(TemplateView):
    template_name = 'home.html'
    
    
class SignupView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'converter/signup.html'