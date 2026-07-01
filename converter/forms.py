# converter/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _


class SIESTAParametersForm(forms.Form):
    download_pseudos = forms.BooleanField(
        label=_("Incluir arquivos de pseudopotencial (.psf) no download"),
        required=False,
        initial=False,
        help_text=_(
            "Se marcado, o download será um arquivo .zip contendo "
            "o .fdf e os arquivos .psf necessários."
        ),
    )

    lattice_constant = forms.FloatField(
        label=_("LatticeConstant (Ang)"),
        initial=1.0,
        help_text=_(
            "Valor da constante de rede em Angstroms. Os vetores da rede "
            "(abaixo) são multiplicados por este valor pelo SIESTA."
        ),
    )
    cell_size_x = forms.FloatField(
        label=_("Tamanho da Célula X (para Vetor A: [X, 0, 0])"),
        initial=50.0,
        help_text=_(
            "Componente X do primeiro vetor da rede (A_x). "
            "Valor adimensional, multiplicado pela LatticeConstant."
        ),
    )
    cell_size_y = forms.FloatField(
        label=_("Tamanho da Célula Y (para Vetor B: [0, Y, 0])"),
        initial=50.0,
        help_text=_(
            "Componente Y do segundo vetor da rede (B_y). "
            "Valor adimensional, multiplicado pela LatticeConstant."
        ),
    )
    cell_size_z = forms.FloatField(
        label=_("Tamanho da Célula Z (para Vetor C: [0, 0, Z])"),
        initial=50.0,
        help_text=_(
            "Componente Z do terceiro vetor da rede (C_z). "
            "Valor adimensional, multiplicado pela LatticeConstant."
        ),
    )

    xyz_file = forms.FileField(label=_("Arquivo XYZ"))
    system_name = forms.CharField(
        label=_("Nome do Sistema"),
        required=False,
        help_text=_("Deixe em branco para usar o nome do arquivo"),
    )
    padding = forms.FloatField(
        label=_("Espaçamento de borda (Å)"),
        initial=1.0,
        min_value=0.0,
    )

    PAO_BasisSize = forms.ChoiceField(
        label=_("PAO.BasisSize"),
        choices=[("SZ", "SZ"), ("DZ", "DZ"), ("SZP", "SZP"), ("DZP", "DZP")],
        initial="DZP",
    )
    PAO_EnergyShift = forms.FloatField(
        label=_("PAO.EnergyShift (eV)"),
        initial=0.05,
        min_value=0.001,
        help_text=_("Valor em eV"),
    )

    MD_TypeOfRun = forms.ChoiceField(
        label=_("MD.TypeOfRun"),
        choices=[
            ("CG", "CG"),
            ("Verlet", "Verlet"),
            ("Nose", "Nose"),
            ("ParrinelloRahman", "ParrinelloRahman"),
            ("NoseParrinelloRahman", "NoseParrinelloRahman"),
        ],
        initial="CG",
    )
    MD_NumCGsteps = forms.IntegerField(
        label=_("MD.NumCGsteps"), initial=500, min_value=1
    )
    MD_MaxForceTol = forms.FloatField(
        label=_("MD.MaxForceTol (eV/Ang)"), initial=0.05, min_value=0.001
    )

    MaxSCFIterations = forms.IntegerField(
        label=_("MaxSCFIterations"), initial=100, min_value=1
    )
    SpinPolarized = forms.BooleanField(
        label=_("SpinPolarized"), initial=True, required=False
    )
    MeshCutoff = forms.FloatField(
        label=_("MeshCutoff (Ry)"), initial=200.0, min_value=50.0
    )

    DM_UseSaveDM = forms.BooleanField(
        label=_("DM.UseSaveDM"), initial=True, required=False
    )
    UseSaveData = forms.BooleanField(
        label=_("UseSaveData"), initial=True, required=False
    )
    MD_UseSaveXV = forms.BooleanField(
        label=_("MD.UseSaveXV"), initial=True, required=False
    )
    MD_UseSaveCG = forms.BooleanField(
        label=_("MD.UseSaveCG"), initial=True, required=False
    )
    DM_MixingWeight = forms.FloatField(
        label=_("DM.MixingWeight"), initial=0.10, min_value=0.01, max_value=1.0
    )
    DM_NumberPulay = forms.IntegerField(
        label=_("DM.NumberPulay"), initial=3, min_value=0
    )
    DM_Tolerance = forms.FloatField(
        label=_("DM.Tolerance"),
        initial=1.0e-3,
        help_text=_("Valor em formato científico (ex: 1.0E-3)"),
    )

    WriteCoorXmol = forms.BooleanField(
        label=_("WriteCoorXmol"), initial=True, required=False
    )
    WriteMullikenPop = forms.IntegerField(
        label=_("WriteMullikenPop"), initial=1, min_value=0, max_value=3
    )

    XC_functional = forms.ChoiceField(
        label=_("XC.functional"),
        choices=[("LDA", "LDA"), ("GGA", "GGA"), ("PBE", "PBE")],
        initial="LDA",
    )
    XC_authors = forms.ChoiceField(
        label=_("XC.authors"),
        choices=[
            ("CA", "CA"),
            ("PZ", "PZ"),
            ("PW92", "PW92"),
            ("PBE", "PBE"),
            ("revPBE", "revPBE"),
            ("RPBE", "RPBE"),
        ],
        initial="CA",
    )
    SolutionMethod = forms.ChoiceField(
        label=_("SolutionMethod"),
        choices=[("diagon", "diagon"), ("OrderN", "OrderN")],
        initial="diagon",
    )
    ElectronicTemperature = forms.FloatField(
        label=_("ElectronicTemperature (meV)"),
        initial=80,
        min_value=0.0,
        help_text=_("Valor em meV"),
    )
