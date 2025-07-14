# converter/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _

class UploadFileForm(forms.Form):
    xyz_file = forms.FileField(label='Selecione o arquivo Heparin.xyz', 
                               help_text='Apenas arquivos com extensão .xyz são permitidos.')

    def clean_xyz_file(self):
        file = self.cleaned_data.get('xyz_file', False)
        if file:
            if not file.name.endswith('.xyz'):
                raise forms.ValidationError("Apenas arquivos .xyz são permitidos.")
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("O arquivo é muito grande. O tamanho máximo é de 5MB.")
        return file

class SIESTAParametersForm(forms.Form):
    download_pseudos = forms.BooleanField(
            label='Incluir arquivos de pseudopotencial (.psf) no download',
            required=False,
            initial=False,
            help_text='Se marcado, o download será um arquivo .zip contendo o .fdf e os arquivos .psf necessários.'
        )

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
    padding = forms.FloatField(label='Espaçamento de borda (Å)', initial=1.0, min_value=0.0)

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
