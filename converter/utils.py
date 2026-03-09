# Built-in Python imports
import hashlib
import io
import os
import zipfile
from datetime import datetime

# Django imports
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.utils.text import slugify


# Tabela periódica mínima (principais elementos para biomoléculas)
PT = {'H': 1, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'P': 15, 'S': 16, 'Cl': 17, 'Br': 35, 'I': 53}

# Lookup reverso: número atômico → símbolo (derivado de PT, sem hardcoding)
ATOMIC_NUMBER_TO_SYMBOL = {v: k for k, v in PT.items()}


def read_xyz(file_obj):
    """Lê um arquivo XYZ e retorna uma lista de tuplas (símbolo, x, y, z).

    Detecta automaticamente se a primeira coluna contém números atômicos em vez de
    símbolos químicos e os converte.

    Args:
        file_obj: Objeto de arquivo ou similar a arquivo contendo dados XYZ

    Returns:
        tuple: (atoms, atomic_numbers_detected)
            - atoms: Lista de tuplas no formato [(símbolo, x, y, z), ...]
            - atomic_numbers_detected: True se a entrada usava números atômicos

    Raises:
        ValueError: Se o formato do arquivo for inválido ou número atômico desconhecido
    """
    # Decodifica cada linha para texto
    lines = [line.decode('utf-8').strip() for line in file_obj]

    n = int(lines[0])  # Número de átomos
    atoms = []
    atomic_numbers_detected = False

    for i in range(2, 2 + n):
        if i < len(lines) and lines[i].strip():
            parts = lines[i].split()
            if len(parts) >= 4:
                symbol_or_number = parts[0]
                if symbol_or_number.isdigit():
                    atomic_number = int(symbol_or_number)
                    if atomic_number not in ATOMIC_NUMBER_TO_SYMBOL:
                        raise ValueError(f"Número atômico desconhecido: {atomic_number}")
                    symbol = ATOMIC_NUMBER_TO_SYMBOL[atomic_number]
                    atomic_numbers_detected = True
                else:
                    symbol = symbol_or_number
                x, y, z = map(float, parts[1:4])
                atoms.append((symbol, x, y, z))

    return atoms, atomic_numbers_detected


def bounding_box(atoms):
    """Calcula a caixa delimitadora para os átomos.
    
    Args:
        atoms (list): Lista de tuplas no formato [(símbolo, x, y, z), ...]
        
    Returns:
        tuple: (x_min, x_max, y_min, y_max, z_min, z_max)
    """
    xs, ys, zs = zip(*[(a[1], a[2], a[3]) for a in atoms])
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def convert_xyz_to_fdf(xyz_file, system_name, params, pt_table=None):
    """Converte um arquivo XYZ para formato FDF e retorna o conteúdo e as espécies únicas.
    
    Args:
        xyz_file: Arquivo XYZ a ser convertido
        system_name (str): Nome do sistema para o arquivo FDF
        params (dict): Dicionário com parâmetros de simulação SIESTA
        pt_table (dict, optional): Tabela periódica para mapeamento de símbolos.
            Se None, usa a tabela padrão PT.
        
    Returns:
        tuple: (fdf_content (str), unique_species (list)) - Conteúdo FDF e lista de espécies únicas
        
    Raises:
        ValueError: Se o arquivo XYZ for inválido ou vazio
    """
    if pt_table is None:
        pt_table = PT
    
    if hasattr(xyz_file, 'seek'):
        xyz_file.seek(0)

    atoms, atomic_numbers_detected = read_xyz(xyz_file)

    # Simplifiquei a identificação de espécies
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
        atomic_num = pt_table.get(sym, 0)
        dici[sym] = idx
        # NOTA: O '.lda' está fixo aqui. Se você usar outros funcionais (GGA, etc)
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

    # Retorna o conteúdo, a lista de espécies e o flag de detecção de números atômicos
    return output.getvalue(), unique_species, atomic_numbers_detected


def create_zip_archive(request, fdf_content, system_name, unique_species):
    """Cria um arquivo ZIP em memória contendo o .fdf e os arquivos .psf necessários.
    
    Args:
        request: HttpRequest object
        fdf_content (str): Conteúdo do arquivo FDF gerado
        system_name (str): Nome do sistema para nomear os arquivos
        unique_species (list): Lista de símbolos de elementos únicos encontrados
        
    Returns:
        HttpResponse: Resposta HTTP com arquivo ZIP ou FDF individual
        
    Raises:
        N/A - Retorna HttpResponse em caso de erro
    """
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