/**
 * JavaScript para funcionalidade da página de upload/conversão
 * Inclui pré-visualização FDF, visualização 3D e salvamento de configurações
 */

// Mapeamento número atômico → símbolo químico
// Espelho de converter/periodic_table.py — manter sincronizado
const ATOMIC_NUMBER_TO_SYMBOL = {
    1:'H',2:'He',3:'Li',4:'Be',5:'B',6:'C',7:'N',8:'O',9:'F',10:'Ne',
    11:'Na',12:'Mg',13:'Al',14:'Si',15:'P',16:'S',17:'Cl',18:'Ar',
    19:'K',20:'Ca',21:'Sc',22:'Ti',23:'V',24:'Cr',25:'Mn',26:'Fe',
    27:'Co',28:'Ni',29:'Cu',30:'Zn',31:'Ga',32:'Ge',33:'As',34:'Se',
    35:'Br',36:'Kr',37:'Rb',38:'Sr',39:'Y',40:'Zr',41:'Nb',42:'Mo',
    43:'Tc',44:'Ru',45:'Rh',46:'Pd',47:'Ag',48:'Cd',49:'In',50:'Sn',
    51:'Sb',52:'Te',53:'I',54:'Xe',55:'Cs',56:'Ba',57:'La',58:'Ce',
    59:'Pr',60:'Nd',61:'Pm',62:'Sm',63:'Eu',64:'Gd',65:'Tb',66:'Dy',
    67:'Ho',68:'Er',69:'Tm',70:'Yb',71:'Lu',72:'Hf',73:'Ta',74:'W',
    75:'Re',76:'Os',77:'Ir',78:'Pt',79:'Au',80:'Hg',81:'Tl',82:'Pb',
    83:'Bi',84:'Po',85:'At',86:'Rn',87:'Fr',88:'Ra',89:'Ac',90:'Th',
    91:'Pa',92:'U',93:'Np',94:'Pu',95:'Am',96:'Cm',97:'Bk',98:'Cf',
    99:'Es',100:'Fm',101:'Md',102:'No',103:'Lr',104:'Rf',105:'Db',
    106:'Sg',107:'Bh',108:'Hs',109:'Mt',110:'Ds',111:'Rg',112:'Cn',
    113:'Nh',114:'Fl',115:'Mc',116:'Lv',117:'Ts',118:'Og'
};

/**
 * Normaliza um arquivo XYZ substituindo números atômicos por símbolos químicos.
 * O 3Dmol.js não reconhece números atômicos e lança erro ao tentar processar.
 *
 * @param {string} xyzData - Conteúdo bruto do arquivo XYZ
 * @returns {string} - Conteúdo XYZ com símbolos químicos na primeira coluna
 */
function normalizeXYZSymbols(xyzData) {
    return xyzData.split('\n').map((line, index) => {
        // Linhas 0 e 1 são cabeçalho (nº de átomos e linha de comentário)
        if (index < 2) return line;
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 4 && /^\d+$/.test(parts[0])) {
            const symbol = ATOMIC_NUMBER_TO_SYMBOL[parseInt(parts[0])];
            if (symbol) parts[0] = symbol;
        }
        return parts.length >= 4 ? parts.join('  ') : line;
    }).join('\n');
}

document.addEventListener('DOMContentLoaded', function() {
    // Script para pré-visualização FDF
    const previewButton = document.getElementById('previewButton');
    const downloadPreviewButton = document.getElementById('downloadPreviewButton');
    const previewContent = document.getElementById('previewContent');
    const form = document.getElementById('convertForm');
    const modalElement = document.getElementById('previewModal');
    
    let previewModal = null;
    if (modalElement) {
        previewModal = new bootstrap.Modal(modalElement);
    }
    
    if (previewButton) {
        previewButton.addEventListener('click', function() {
            const formData = new FormData(form);
            formData.append('preview', 'true');
            
            previewContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p class="mt-2">Gerando pré-visualização FDF...</p></div>';
            
            if (previewModal) previewModal.show();
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                previewContent.textContent = data.content;
                if (document.getElementById('previewModalLabel')) {
                    document.getElementById('previewModalLabel').textContent = 'Pré-visualização FDF: ' + data.filename;
                }
            })
            .catch(error => {
                console.error('Erro na pré-visualização FDF:', error);
                previewContent.innerHTML = '<div class="alert alert-danger">Erro ao gerar pré-visualização FDF. Verifique se o arquivo XYZ é válido.</div>';
            });
        });
    }

    if (downloadPreviewButton) {
        downloadPreviewButton.addEventListener('click', function() {
            const previewInput = form.querySelector('input[name="preview"]');
            if (previewInput) previewInput.remove();
            form.submit();
        });
    }

    // Script para Visualização 3D com 3Dmol.js
    initialize3DViewer();

    // Script para Salvar Configuração
    initializeSaveConfiguration();
});

/**
 * Inicializa o visualizador 3D para arquivos XYZ
 */
function initialize3DViewer() {
    console.log('🔍 Inicializando visualizador 3D...');
    
    let xyzFileElement = document.querySelector('input[name="xyz_file"]'); 
    let viewerContainer = document.getElementById('molviewer');
    let glviewer = null;

    console.log('📋 Elementos encontrados:');
    console.log('  - input[name="xyz_file"]:', xyzFileElement);
    console.log('  - div#molviewer:', viewerContainer);
    console.log('  - $3Dmol definido?', typeof $3Dmol !== 'undefined' ? '✅ Sim' : '❌ Não');

    if (!xyzFileElement) {
        xyzFileElement = document.getElementById('id_xyz_file');
        console.log('  - Tentando id_xyz_file:', xyzFileElement);
    }

    if (xyzFileElement && viewerContainer) {
        console.log('✅ Elementos encontrados, configurando event listener...');
        
        xyzFileElement.addEventListener('change', function(event) {
            console.log('📁 Arquivo selecionado:', event.target.files[0] ? event.target.files[0].name : 'Nenhum');
            
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const rawXyzData = e.target.result;
                    console.log('📄 Arquivo lido, tamanho:', rawXyzData.length, 'caracteres');

                    console.log('=== RAW (primeiras 5 linhas) ===');
                    console.log(rawXyzData.split('\n').slice(0, 7).join('\n'));

                    // Normaliza números atômicos → símbolos químicos antes de passar ao 3Dmol
                    const xyzData = normalizeXYZSymbols(rawXyzData);

                    console.log('=== NORMALIZADO (primeiras 5 linhas) ===');
                    console.log(xyzData.split('\n').slice(0, 7).join('\n'));

                    // Limpa o container antes de adicionar novo viewer
                    viewerContainer.innerHTML = ''; 

                    try {
                        if (typeof $3Dmol === 'undefined') {
                            throw new Error('3Dmol.js não está carregado');
                        }
                        
                        glviewer = $3Dmol.createViewer(viewerContainer, { backgroundColor: 'white' });
                        glviewer.addModel(xyzData, 'xyz');
                        glviewer.setStyle({}, {stick: {radius: 0.15}, sphere: {scale: 0.25}});
                        glviewer.zoomTo();
                        glviewer.render();
                        
                        console.log('✅ Molécula renderizada com sucesso!');
                    } catch (error) {
                        console.error('❌ Erro ao criar visualizador 3D:', error);
                        viewerContainer.innerHTML = '<div class="alert alert-danger text-center p-3">Erro ao renderizar molécula 3D: ' + error.message + '</div>';
                    }
                };
                reader.onerror = function() {
                    console.error("❌ Erro ao ler o arquivo:", reader.error);
                    viewerContainer.innerHTML = '<div class="alert alert-danger text-center p-3">Erro ao ler o arquivo XYZ.</div>';
                };
                reader.readAsText(file);
            } else {
                console.log('📭 Nenhum arquivo selecionado');
                viewerContainer.innerHTML = '<div class="text-center p-5 text-muted">Selecione um arquivo XYZ acima para visualizar a molécula.</div>';
                if (glviewer) {
                    glviewer.clear();
                    glviewer = null; 
                }
            }
        });
        
        console.log('✅ Event listener configurado com sucesso!');
    } else {
        if (!xyzFileElement) {
            console.error("❌ Elemento input[name='xyz_file'] ou #id_xyz_file não encontrado.");
            const allFileInputs = document.querySelectorAll('input[type="file"]');
            console.log('📋 Todos os inputs de arquivo encontrados:', allFileInputs.length);
            allFileInputs.forEach((input, i) => {
                console.log(`  ${i}: name="${input.name}", id="${input.id}"`);
            });
        }
        if (!viewerContainer) console.error("❌ Elemento div#molviewer não encontrado.");
    }
}

/**
 * Inicializa a funcionalidade de salvar configurações
 */
function initializeSaveConfiguration() {
    const saveConfigButton = document.getElementById('saveConfigSubmit');
    const saveConfigForm = document.getElementById('saveConfigForm');
    const saveConfigModalElement = document.getElementById('saveConfigModal');
    
    if (saveConfigButton && saveConfigForm) {
        saveConfigButton.addEventListener('click', function() {
            const configName = document.getElementById('configName').value;
            const configDescription = document.getElementById('configDescription').value;
            
            if (!configName.trim()) {
                alert('Por favor, informe um nome para a configuração.');
                return;
            }
            
            const form = document.getElementById('convertForm');
            const formData = new FormData(form);
            const params = {};
            
            for (let [key, value] of formData.entries()) {
                if (key !== 'xyz_file' && key !== 'csrfmiddlewaretoken') {
                    if (value === 'on') {
                        params[key] = true;
                    } else if (value === 'off') {
                        params[key] = false;
                    } else {
                        const numValue = parseFloat(value);
                        params[key] = isNaN(numValue) ? value : numValue;
                    }
                }
            }
            
            const saveData = {
                name: configName,
                description: configDescription,
                parameters: JSON.stringify(params)
            };
            
            saveConfigButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';
            saveConfigButton.disabled = true;
            
            const saveUrl = saveConfigButton.dataset.url;
            if (!saveUrl) {
                console.error('URL para salvar configuração não encontrada');
                alert('Erro: URL para salvar configuração não configurada.');
                return;
            }
            
            fetch(saveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: new URLSearchParams(saveData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    if (saveConfigModalElement) {
                        const modal = bootstrap.Modal.getInstance(saveConfigModalElement);
                        if (modal) modal.hide();
                    }
                    alert('Configuração salva com sucesso!');
                    saveConfigForm.reset();
                } else {
                    alert('Erro ao salvar configuração: ' + (data.message || 'Erro desconhecido'));
                }
            })
            .catch(error => {
                console.error('Erro ao salvar configuração:', error);
                alert('Erro ao salvar configuração. Verifique sua conexão e tente novamente.');
            })
            .finally(() => {
                saveConfigButton.innerHTML = 'Salvar Configuração';
                saveConfigButton.disabled = false;
            });
        });
    }
    
    if (saveConfigModalElement) {
        saveConfigModalElement.addEventListener('hidden.bs.modal', function() {
            if (saveConfigForm) {
                saveConfigForm.reset();
            }
        });
    }
}

// Verificar se 3Dmol.js está carregado e inicializar visualizador
if (typeof $3Dmol !== 'undefined') {
    // Já inicializado no DOMContentLoaded
} else {
    console.log('⏳ 3Dmol.js ainda não carregado, aguardando...');
    setTimeout(function() {
        if (typeof $3Dmol !== 'undefined') {
            const viewerContainer = document.getElementById('molviewer');
            if (viewerContainer && viewerContainer.innerHTML.includes('Selecione um arquivo')) {
                initialize3DViewer();
            }
        } else {
            console.error('❌ 3Dmol.js não carregado após timeout');
            const viewerContainer = document.getElementById('molviewer');
            if (viewerContainer) {
                viewerContainer.innerHTML = '<div class="alert alert-warning text-center p-3">A biblioteca 3Dmol.js não foi carregada. A visualização 3D não está disponível.</div>';
            }
        }
    }, 1000);
}