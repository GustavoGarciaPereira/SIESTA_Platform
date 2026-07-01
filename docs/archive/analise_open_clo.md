# Análise do Projeto SIESTA Platform

## Visão Geral do Projeto

**SIESTA Platform** é uma aplicação web Django 4.2 que converte arquivos de coordenadas moleculares (`.xyz`) em arquivos de entrada para simulações SIESTA (`.fdf`). O projeto é voltado para pesquisadores que utilizam o software de simulação de materiais [SIESTA](https://siesta-project.org/siesta/).

### Objetivo Principal
Fornecer uma interface web acessível para converter arquivos XYZ em formatos compatíveis com o SIESTA, incluindo geração automática de arquivos de pseudopotenciais quando necessário.

## Arquitetura do Sistema

### Estrutura de Aplicações Django
O projeto é organizado em três aplicações principais:

1. **`converter/`** - Funcionalidade central
   - Conversão XYZ → FDF
   - Histórico de conversões
   - Configurações salvas de parâmetros SIESTA
   - Upload e gerenciamento de arquivos

2. **`user/`** - Autenticação e páginas estáticas
   - Sistema de login/cadastro
   - Redefinição de senha
   - Perfil de usuário
   - Páginas estáticas (home, about, contact)

3. **`dashboard/`** - Painel administrativo
   - Visualização staff-only de todas as URLs do sistema
   - Referência para desenvolvimento e depuração

### Estrutura de URLs
| Prefixo | Aplicação | Descrição |
|---------|-----------|-----------|
| `/converter/` | `converter.urls` | Funcionalidades de conversão |
| `/` (raiz) | `user.urls` | Autenticação e páginas estáticas |
| `/dashboard/` | `dashboard.urls` | Painel administrativo |

## Fluxo de Conversão

### Processo Principal
1. **Upload do arquivo**: Usuário envia arquivo `.xyz` através do formulário
2. **Configuração de parâmetros**: Preenchimento do `SIESTAParametersForm` com parâmetros SIESTA
3. **Conversão**: `ConvertView.post()` chama `convert_xyz_to_fdf()` de `converter/utils.py`
4. **Saída**:
   - Download direto do arquivo `.fdf`
   - Ou arquivo `.zip` contendo `.fdf` + arquivos de pseudopotenciais `.psf`
5. **Persistência**: Se autenticado, registro no `ConversionHistory` com `UploadedFile`
6. **Preview**: Modo de visualização retorna JSON (AJAX) ou renderiza template

## Componentes Técnicos

### Modelos de Dados (`converter/models.py`)
Todos os modelos usam `managed = False` - Django NÃO gerencia o schema. Tabelas devem existir antes das migrações.

#### `UploadedFile`
- Armazena arquivos `.xyz` enviados
- Inclui checksum SHA-256 para verificação de integridade
- Relacionamento com usuário

#### `ConversionHistory`
- Registro completo de conversões
- Conteúdo FDF gerado
- Parâmetros SIESTA como JSON
- Contador de downloads

#### `SavedConfiguration`
- Conjuntos reutilizáveis de parâmetros SIESTA
- Único por `(user, name)`
- Contador de usos e data do último uso

#### `UserProfile` (`user/models.py`)
- Extensão OneToOne do modelo `User` do Django
- Informações institucionais e de pesquisa
- Foto de perfil opcional

### Lógica de Conversão (`converter/utils.py`)

#### `convert_xyz_to_fdf()`
Função central que:
1. Lê arquivo XYZ com `read_xyz()`
2. Detecta automaticamente números atômicos vs símbolos químicos
3. Calcula caixa delimitadora com `bounding_box()`
4. Gera conteúdo FDF formatado com todos os parâmetros SIESTA
5. Retorna conteúdo FDF e lista de espécies únicas

#### `create_zip_archive()`
- Cria arquivo ZIP em memória
- Inclui arquivo `.fdf` gerado
- Adiciona arquivos `.psf` do diretório `pseudos/`
- Nomenclatura fixa: `{Symbol}.lda.psf` (hardcoded para LDA)

#### Tabela Periódica
```python
PT = {'H': 1, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'P': 15, 'S': 16, 'Cl': 17, 'Br': 35, 'I': 53}
```
- Elementos comuns em biomoléculas
- Mapeamento símbolo → número atômico

### Views Principais (`converter/views.py`)

#### `ConvertView` (Class-Based View)
- `get()`: Exibe formulário, pré-popula com configuração da sessão
- `post()`: Processa conversão, gerencia histórico, retorna download/preview

#### Views de Suporte
- `history_view()`: Histórico de conversões do usuário
- `download_fdf()`: Download de conversão específica
- Views para configurações salvas (save/load/delete)

### Formulários (`converter/forms.py`)
#### `SIESTAParametersForm`
Contém todos os parâmetros SIESTA configuráveis:
- **PAO Basis**: Tamanho da base, deslocamento de energia
- **MD**: Tipo de execução, número de passos, tolerância de força
- **SCF**: Iterações máximas, tolerância DM, método de solução
- **XC Functional**: LDA/GGA, autores
- **Outros**: Mesh cutoff, temperatura eletrônica, opções de salvamento

## Configuração e Deployment

### Ambiente
- **Django 4.2** com Python 3.10+
- **Banco de dados**: SQLite (dev) / PostgreSQL (produção)
- **Servidor estático**: WhiteNoise com `CompressedManifestStaticFilesStorage`
- **Email**: Console backend (dev) / SMTP (produção)

### Variáveis de Ambiente (`.env`)
| Variável | Propósito |
|----------|-----------|
| `DEBUG` | Modo desenvolvimento (`True`) ou produção (`False`) |
| `SECRET_KEY` | Chave secreta do Django |
| `DB_*` | Configurações PostgreSQL (produção) |
| `EMAIL_*` | Configurações SMTP (produção) |

### Diretórios Importantes
- `pseudos/`: Arquivos `.psf` de pseudopotenciais
- `media/`: Uploads de arquivos
- `static/`: Arquivos estáticos
- `staticfiles/`: Arquivos estáticos coletados

## Pseudopotenciais

### Sistema Atual
- Arquivos seguem padrão: `{Symbol}.lda.psf` (ex: `N.lda.psf`)
- Diretório configurado via `settings.PSEUDOPOTENTIALS_DIR`
- **Limitação**: Funcional XC hardcoded como `lda`, independente do valor do formulário

### Fluxo de Inclusão
1. Identifica espécies únicas no arquivo XYZ
2. Para cada espécie, busca arquivo `.psf` correspondente
3. Inclui no ZIP se encontrado
4. Aviso ao usuário se arquivo faltar

## Sistema de Autenticação

### Funcionalidades
- Login/Logout com redirecionamento configurável
- Cadastro de novos usuários
- Redefinição de senha com templates customizados
- Perfil de usuário estendido

### Templates de Redefinição
Localizados em `converter/templates/converter/`:
- `password_reset_form.html`
- `password_reset_done.html`
- `password_reset_confirm.html`
- `password_reset_complete.html`
- `password_reset_email.html`
- `password_reset_subject.txt`

## Dashboard Administrativo

### Propósito
- Visualização staff-only de todas as URLs do sistema
- Referência para desenvolvimento
- Organização por categorias:
  - Administração
  - Conversão
  - Histórico e Downloads
  - Configurações Salvas
  - Páginas Estáticas
  - Autenticação
  - Perfil

## Configurações Salvas

### Fluxo de Sessão
1. `load_configuration` armazena parâmetros em `request.session['loaded_config']`
2. `ConvertView.get()` lê esta chave para pré-povoar o formulário
3. Configuração pode ser limpa após uso para evitar reuso acidental

### Características
- Nome único por usuário
- Contador de usos e data do último uso
- Opção de configuração padrão
- Descrição opcional

## Tratamento de Erros

### Página 500 Customizada
- `converter/templates/500.html`
- Segue design do sistema (Bootstrap + variáveis CSS)
- Descoberta automática via `APP_DIRS=True`

### Logging
- Logger configurado em `converter/views.py`
- Erros no registro de histórico são logados mas não interrompem fluxo

## Deployment

### Docker
- Imagem base: `python:3.10-slim`
- Dependências de sistema: `libpq-dev`, `gcc`
- Script de entrypoint: `entrypoint.sh`
- Coleta de estáticos durante build

### Render (Produção)
- Configuração PostgreSQL via `dj-database-url`
- WhiteNoise para servir arquivos estáticos
- Variáveis de ambiente para configuração

## Dependências (`requirements.txt`)

### Principais Pacotes
- `Django==4.2.17`: Framework web
- `numpy`: Processamento numérico (potencial uso futuro)
- `psycopg2-binary`: Adaptador PostgreSQL
- `dj-database-url`: Parse de URL de banco de dados
- `python-dotenv`: Carregamento de variáveis de ambiente
- `whitenoise`: Servir arquivos estáticos
- `Pillow`: Processamento de imagens (fotos de perfil)
- `gunicorn`: Servidor WSGI para produção

## Análise de Código

### Pontos Fortes
1. **Arquitetura modular**: Aplicações bem separadas por responsabilidade
2. **Documentação**: Docstrings abrangentes em modelos e funções
3. **Tratamento de erros**: Logging adequado e fallbacks
4. **Flexibilidade**: Suporte a usuários autenticados e anônimos
5. **Extensibilidade**: Estrutura que permite adição de novos recursos

### Áreas para Melhoria
1. **Pseudopotenciais**: Funcional XC hardcoded como `lda`
2. **Modelos não gerenciados**: Requer criação manual de tabelas
3. **Testes**: Cobertura de testes poderia ser expandida
4. **Internacionalização**: Strings em português misturadas com inglês

### Considerações de Segurança
1. **Upload de arquivos**: Validação de tipo e tamanho
2. **Autenticação**: Sistema padrão do Django com validação de senha
3. **Sessões**: Uso apropriado para configurações carregadas
4. **SQL Injection**: Protegido pelo ORM do Django
5. **XSS**: Templates escapam automaticamente

## Conclusão

O **SIESTA Platform** é uma aplicação web bem estruturada que resolve um problema específico da comunidade científica: a conversão de arquivos de coordenadas moleculares para formato de entrada do SIESTA. A arquitetura modular, documentação abrangente e tratamento adequado de erros tornam-na uma base sólida para expansão.

**Potenciais expansões**:
1. Suporte a múltiplos funcionais XC para pseudopotenciais
2. Visualização 3D avançada de moléculas
3. Integração com APIs de cálculos quânticos
4. Sistema de filas para conversões em lote
5. Exportação para outros formatos de simulação

O projeto demonstra boas práticas de desenvolvimento Django e serve como exemplo de aplicação científica web bem implementada.