/**
 * JavaScript para funcionalidade da página de upload/conversão
 * Inclui pré-visualização FDF, visualização 3D e salvamento de configurações
 */

// Mapeamento número atômico → símbolo químico injetado pelo servidor
// (fonte única: converter/periodic_table.py, via window.ATOMIC_NUMBER_TO_SYMBOL)
const ATOMIC_NUMBER_TO_SYMBOL = window.ATOMIC_NUMBER_TO_SYMBOL || {};

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
            .then(async response => {
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.message || 'Falha ao gerar pré-visualização FDF.');
                }
                return data;
            })
            .then(data => {
                previewContent.textContent = data.content;
                if (document.getElementById('previewModalLabel')) {
                    document.getElementById('previewModalLabel').textContent = 'Pré-visualização FDF: ' + data.filename;
                }
            })
            .catch(error => {
                console.error('Erro na pré-visualização FDF:', error);
                previewContent.innerHTML = '<div class="alert alert-danger">' +
                    (error.message || 'Erro ao gerar pré-visualização FDF. Verifique se o arquivo XYZ é válido.') +
                    '</div>';
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
    let xyzFileElement = document.querySelector('input[name="xyz_file"]');
    let viewerContainer = document.getElementById('molviewer');
    let glviewer = null;

    if (!xyzFileElement) {
        xyzFileElement = document.getElementById('id_xyz_file');
    }

    if (xyzFileElement && viewerContainer) {
        xyzFileElement.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Normaliza números atômicos → símbolos químicos antes de passar ao 3Dmol
                    const xyzData = normalizeXYZSymbols(e.target.result);

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
                    } catch (error) {
                        console.error('Erro ao criar visualizador 3D:', error);
                        viewerContainer.innerHTML = '<div class="alert alert-danger text-center p-3">Erro ao renderizar molécula 3D: ' + error.message + '</div>';
                    }
                };
                reader.onerror = function() {
                    console.error('Erro ao ler o arquivo XYZ:', reader.error);
                    viewerContainer.innerHTML = '<div class="alert alert-danger text-center p-3">Erro ao ler o arquivo XYZ.</div>';
                };
                reader.readAsText(file);
            } else {
                viewerContainer.innerHTML = '<div class="text-center p-5 text-muted">Selecione um arquivo XYZ acima para visualizar a molécula.</div>';
                if (glviewer) {
                    glviewer.clear();
                    glviewer = null;
                }
            }
        });
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
                    } else {
                        const numValue = parseFloat(value);
                        params[key] = isNaN(numValue) ? value : numValue;
                    }
                }
            }

            // Checkboxes desmarcados não entram no FormData: registra explicitamente
            // como false para que o round-trip da configuração salva funcione.
            form.querySelectorAll('input[type="checkbox"][name]').forEach(cb => {
                params[cb.name] = cb.checked;
            });
            
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

// Se o 3Dmol.js carregar depois do DOMContentLoaded, inicializa o visualizador
if (typeof $3Dmol === 'undefined') {
    setTimeout(function() {
        if (typeof $3Dmol !== 'undefined') {
            const viewerContainer = document.getElementById('molviewer');
            if (viewerContainer && viewerContainer.innerHTML.includes('Selecione um arquivo')) {
                initialize3DViewer();
            }
        } else {
            console.error('3Dmol.js não carregado após timeout');
            const viewerContainer = document.getElementById('molviewer');
            if (viewerContainer) {
                viewerContainer.innerHTML = '<div class="alert alert-warning text-center p-3">A biblioteca 3Dmol.js não foi carregada. A visualização 3D não está disponível.</div>';
            }
        }
    }, 1000);
}