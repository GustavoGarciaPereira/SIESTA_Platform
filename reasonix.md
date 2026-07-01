# 🧪 SIESTA Platform — Guia do Desenvolvedor

> Última atualização: 2025-07-15 (pós-limpeza estrutural — commit `09902af`)

---

## 📌 Visão Geral

**SIESTA Platform** é uma aplicação web Django 4.2 que converte arquivos de coordenadas moleculares (`.xyz`) em arquivos de entrada para o software de simulação de materiais [SIESTA](https://siesta-project.org/siesta/) (`.fdf`). Oferece interface web com visualização 3D interativa (3Dmol.js), controle completo sobre parâmetros de simulação, download empacotado de pseudopotenciais, e sistema de autenticação com histórico de conversões e configurações salvas.

**Público-alvo:** Pesquisadores, estudantes e profissionais de ciência dos materiais que utilizam DFT/SIESTA e precisam gerar inputs de simulação sem editar manualmente arquivos FDF.

### Stack

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.10+ |
| Framework | Django 4.2 |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Visualização 3D | 3Dmol.js 2.0 (CDN) |
| Banco (dev) | SQLite3 |
| Banco (prod) | PostgreSQL 13 |
| Servidor WSGI | Gunicorn |
| Estáticos | WhiteNoise (CompressedManifestStaticFilesStorage) |
| Container | Docker + Docker Compose |
| Deploy alvo | Render.com |

---

## 🏗️ Arquitetura

### Estrutura de Diretórios (pós-limpeza)

```
.
├── heparin_converter/          # Config do projeto Django
│   ├── settings.py             # DEBUG condicional (SQLite vs PostgreSQL)
│   ├── urls.py                 # URLconf raiz
│   ├── wsgi.py                 # Entrada WSGI (Gunicorn)
│   └── asgi.py                 # Scaffold ASGI (futuro)
├── converter/                  # App principal — conversão XYZ→FDF
│   ├── models.py               # UploadedFile, ConversionHistory, SavedConfiguration
│   ├── views.py                # ConvertView (CBV) + FBVs (history, config, download)
│   ├── forms.py                # SIESTAParametersForm (~30 campos)
│   ├── utils.py                # read_xyz, bounding_box, convert_xyz_to_fdf, create_zip_archive
│   ├── periodic_table.py       # Tabela periódica completa (118 elementos) — fonte única
│   ├── admin.py                # Registro dos 3 models no admin
│   ├── urls.py                 # /converter/* — convert, history, config, download
│   ├── tests.py                # ~70 testes (utils, models, forms, views)
│   └── templates/              # Templates do app + páginas estáticas
│       ├── base.html           # Layout base (navbar, footer, Bootstrap CDN)
│       ├── home.html, about.html, contact.html, 500.html
│       └── converter/          # upload.html, history.html, login.html, signup.html, etc.
├── user/                       # App de autenticação + páginas institucionais
│   ├── models.py               # UserProfile (OneToOne → User)
│   ├── views.py                # HomeView, SignupView, AboutView, ContactView, profile_view
│   ├── forms.py                # UserCreationForm, UserProfileForm
│   ├── admin.py                # UserProfileAdmin
│   ├── urls.py                 # / — home, login, signup, password_reset, about, contact, profile
│   ├── test_views.py           # ~35 testes
│   └── templates/user/         # profile.html
├── dashboard/                  # App administrativo (staff-only)
│   ├── views.py                # dashboard_view — lista categorizada de URLs
│   ├── urls.py                 # /dashboard/
│   ├── test_views.py           # 7 testes
│   └── templates/dashboard/    # dashboard.html
├── static/                     # Estáticos fonte (CSS + JS customizados)
│   ├── css/base.css            # Design system completo (variáveis, navbar, cards, tabelas)
│   └── js/upload.js            # Lógica do upload: 3Dmol, preview AJAX, save config
├── pseudos/                    # Pseudopotenciais .psf (5 elementos LDA)
├── docs/archive/               # Documentação histórica arquivada
├── requirements.txt            # Dependências (limpas — sem numpy, typing_extensions)
├── Dockerfile                  # Build da imagem (python:3.10-slim, Gunicorn)
├── entrypoint.sh               # Wait-for-db, migrate, collectstatic, superuser, Gunicorn
├── docker-compose.yml          # Serviços: web + db (PostgreSQL 13)
└── manage.py
```

### Fluxo de Conversão (síncrono atual)

```
1. GET  /converter/convert/
   └─ ConvertView.get() → render upload.html com SIESTAParametersForm

2. Usuário seleciona .xyz → JS (upload.js):
   ├─ FileReader lê o arquivo
   ├─ normalizeXYZSymbols() converte nºs atômicos → símbolos (118 elementos)
   └─ 3Dmol.js renderiza molécula 3D no div#molviewer

3. POST /converter/convert/ (submit ou preview)
   ├─ SIESTAParametersForm.is_valid()
   ├─ read_xyz(file) → [(símbolo, x, y, z), ...]
   ├─ bounding_box(atoms) → dimensões da molécula
   ├─ Ajusta cell_size_x/y/z com padding (se menores que molécula + 2×padding)
   ├─ convert_xyz_to_fdf(xyz_file, system_name, params, PT)
   │   ├─ Bloco ChemicalSpeciesLabel (ex: "1 6 C.lda")
   │   ├─ LatticeVectors (matriz diagonal)
   │   ├─ AtomicCoordinatesAndAtomicSpecies
   │   └─ Parâmetros: PAO, MD, SCF, DM, XC, SolutionMethod
   ├─ Se download_pseudos=True:
   │   └─ create_zip_archive() → .zip com .fdf + .psf
   ├─ Se usuário autenticado: salva UploadedFile + ConversionHistory
   └─ Retorna HttpResponse (download) ou JsonResponse (preview AJAX)
```

### Modelos de Dados

| Modelo | Tabela | Responsabilidade |
|--------|--------|-----------------|
| `UploadedFile` | `converter_uploadedfile` | Arquivos .xyz enviados, com SHA-256 |
| `ConversionHistory` | `converter_conversionhistory` | Histórico de conversões: FDF gerado, parâmetros (JSON), status |
| `SavedConfiguration` | `converter_savedconfiguration` | Conjuntos de parâmetros reutilizáveis (unique por user+name) |
| `UserProfile` | `user_userprofile` | Extensão 1-1 do User: instituição, área de pesquisa, foto |

---

## 🧠 Decisões Técnicas

### Por que Celery + Redis (planejado — Onda 1A)

O processamento atual é **síncrono na thread HTTP**. Para arquivos com milhares de átomos ou múltiplos usuários simultâneos, isso satura os workers Gunicorn (default: 2). A escolha de **Celery + Redis** (em vez de RQ ou threads) se justifica por:
- **Redis** já será usado como broker + result backend (setup simples no docker-compose)
- **Celery** tem ecossistema maduro para Django (`django-celery-results`, `task_acks_late`)
- Permite escalar workers independentemente do servidor web
- Timeouts configuráveis por task (`task_time_limit=300`)

### Por que Django REST Framework + SimpleJWT (planejado — Onda 1C)

A API REST permitirá integração com scripts Python, Jupyter Notebooks e pipelines de CI/CD. **SimpleJWT** foi escolhido sobre TokenAuthentication nativo do DRF porque:
- Tokens JWT são **stateless** — sem consulta ao DB por request
- Suporte nativo a refresh tokens rotativos
- Access tokens de curta duração (30 min) + refresh tokens (24h)
- Fácil integração com clientes HTTP (basta header `Authorization: Bearer <token>`)

### Por que centralizar a tabela periódica em `periodic_table.py`

Antes da limpeza, `PT` existia em **3 lugares** com os mesmos 10 elementos:
- `converter/utils.py` (definição principal)
- `converter/views.py` (atributo de classe `ConvertView.PT`)
- `static/js/upload.js` (objeto `ATOMIC_NUMBER_TO_SYMBOL`)

A refatoração:
1. Extraiu `PT` para `converter/periodic_table.py` com **118 elementos**
2. `utils.py` e `views.py` importam do módulo centralizado
3. `upload.js` sincronizado manualmente com o mesmo mapeamento

Isso elimina duplicação e prepara o terreno para a Onda 1B (sufixo XC dinâmico — o hardcoded `.lda` ainda precisa ser resolvido).

### Por que unificar `download_pseudos()` e `create_zip_archive()`

Ambas as funções criavam ZIPs com `.fdf` + `.psf` usando lógica quase idêntica. A refatoração:
1. Extraiu o parser de elementos do FDF para `_extract_species_from_fdf()`
2. Fez `download_pseudos()` delegar para `create_zip_archive()`
3. Removeu ~30 linhas de código duplicado
4. Comportamento unificado: fallback para `.fdf` puro quando pseudos dir ausente

### Estratégia de Versionamento

- **Git**: branch `main`, commits atômicos com mensagens convencionais (`chore:`, `feat:`, `fix:`)
- **`.gitignore`**: cobre `venv/`, `__pycache__/`, `.env`, `media/`, `staticfiles/`, `*.sqlite3`, `AI/`, `.ai/`
- **Migrações**: manter apenas as migrações iniciais (`0001_initial`, `0002_alter_*`)

---

## 📐 Regras de Codificação

### Nomeação

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Models | PascalCase | `ConversionHistory`, `UserProfile` |
| CBVs | PascalCase + sufixo View | `ConvertView`, `HomeView` |
| FBVs | snake_case + sufixo _view | `history_view`, `profile_view` |
| Funções auxiliares | snake_case | `read_xyz`, `bounding_box`, `create_zip_archive` |
| URL names | snake_case com prefixo do app | `converter_history`, `download_fdf` |
| Templates | snake_case | `upload.html`, `my_configs.html` |

### Imports — Ordem Obrigatória

```python
# 1. Built-in Python
import io
import json
import os

# 2. Django
from django.conf import settings
from django.contrib import messages
from django.views import View

# 3. Third-party
# (none currently — Celery, DRF virão aqui)

# 4. Local
from .models import ConversionHistory
from .utils import convert_xyz_to_fdf
from .periodic_table import SYMBOL_TO_ATOMIC_NUMBER as PT
```

### Testes

- **Framework**: `django.test.TestCase` (unittest)
- **Arquivos**: `converter/tests.py`, `user/test_views.py`, `dashboard/test_views.py`
- **Cobertura mínima esperada**: models (criação), forms (válido + inválido), views (GET + POST + auth)
- **Dados de teste**: `setUp()` — nunca usar fixtures
- **Comando**: `python manage.py test converter user dashboard` — deve passar 88 testes

### Validação

- **Sempre** usar Django Forms para validação de entrada (nunca acessar `request.POST` raw)
- `SIESTAParametersForm` cobre todos os ~30 parâmetros com tipos apropriados (`FloatField(min_value=)`, `ChoiceField`, `IntegerField`)
- Validação de arquivo: extensão `.xyz`, tamanho máximo 5 MB

### Logging

- Usar `logging.getLogger(__name__)` em todos os módulos
- Atualmente: apenas `converter/views.py` tem logging (erro no registro de histórico)
- Onda 2C expandirá para logging estruturado em todas as operações críticas

---

## 🗺️ Roadmap

### ✅ Fase 0 — Limpeza Estrutural (Concluído — commit `09902af`)

- [x] Remover dependências fantasmas (`numpy`, `typing_extensions`)
- [x] Deletar arquivos vazios/órfãos (14 arquivos)
- [x] Arquivar relatórios históricos → `docs/archive/`
- [x] Remover `UploadFileForm` redundante
- [x] Extrair tabela periódica → `periodic_table.py` (118 elementos)
- [x] Integrar `bounding_box()` + `padding` no fluxo de conversão
- [x] Unificar `download_pseudos()` com `create_zip_archive()`
- [x] Corrigir `list_display` duplicado no `UserProfileAdmin`
- [x] Sincronizar JS `ATOMIC_NUMBER_TO_SYMBOL` com 118 elementos
- [x] Remover imports mortos em `utils.py` e `views.py`

### 🔴 Onda 1 — Bloqueadores (Próxima fase)

| ID | Tarefa | Status | Esforço |
|----|--------|--------|---------|
| 1A | Processamento assíncrono com Celery + Redis | ⬜ Pendente | 4-5 dias |
| 1B | Sufixo XC dinâmico nos pseudopotenciais (.lda/.gga/.pbe) | ⬜ Pendente | 1-2 dias |
| 1C | API REST com Django REST Framework + SimpleJWT | ⬜ Pendente | 3-4 dias |
| 1D | Validação robusta de XYZ + tratamento de erros | ⬜ Pendente | 1-2 dias |

**Dependências:** 1A → 1C (API depende do modelo assíncrono)

### 🟡 Onda 2 — Diferenciadores

| ID | Tarefa | Status | Esforço |
|----|--------|--------|---------|
| 2A | Modelo `Pseudopotential` + gestão no admin | ⬜ Pendente | 2-3 dias |
| 2B | Presets de simulação + tooltips ricos | ⬜ Pendente | 3-4 dias |
| 2C | Logging estruturado + Sentry + health check | ⬜ Pendente | 2 dias |
| 2D | Segurança: rate limiting, email verification, headers | ⬜ Pendente | 2-3 dias |
| 2E | Cálculo automático de célula (`bounding_box` + `padding`) | 🟨 Parcial | ~0.5 dia restante |
| 2F | Dashboard administrativo com métricas reais | ⬜ Pendente | 2-3 dias |

**Nota 2E:** `bounding_box()` e `padding` já estão integrados ao `ConvertView.post()`. Resta: ajustar a UI para mostrar dimensões calculadas vs. manuais, e warning visual no formulário.

### 🟢 Onda 3 — Polimento

| ID | Tarefa | Status |
|----|--------|--------|
| 3A | Correções de bugs menores | ⬜ Pendente |
| 3B | Proteção anti-clique-duplo no formulário | ⬜ Pendente |
| 3C | Limpeza automática de arquivos `.xyz` órfãos | ⬜ Pendente |
| 3D | WebSockets (Django Channels) para notificações em tempo real | ⬜ Pendente |
| 3E | Expansão de testes (cobertura → 80%) | ⬜ Pendente |

---

## 🚀 Como Executar

### Setup Local (sem Docker)

```bash
# Criar e ativar virtualenv
python -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar .env (obrigatório)
echo "DEBUG=True" > .env
echo "SECRET_KEY='django-insecure-dev-key'" >> .env

# Aplicar migrações
python manage.py migrate

# (Opcional) Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
# → http://localhost:8000
```

### Docker

```bash
# Build e início
docker-compose up --build

# Acesso
# → http://localhost:8000
# → Admin: http://localhost:8000/admin/
# → Dashboard (staff): http://localhost:8000/dashboard/
```

### Testes

```bash
# Todos os testes
python manage.py test converter user dashboard

# App específico
python manage.py test converter

# Teste único
python manage.py test converter.tests.ViewTests.test_history_view_authenticated
```

### Variáveis de Ambiente (.env)

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `DEBUG` | `True` = SQLite + console email | Sim |
| `SECRET_KEY` | Chave secreta Django | Sim |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Conexão PostgreSQL (produção) | Apenas se `DEBUG=False` |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP (produção) | Apenas se `DEBUG=False` |

---

## 🔜 Próximos Passos Imediatos

### Esta semana (Onda 1A — início)

1. **Adicionar Redis ao `docker-compose.yml`**
   ```yaml
   redis:
     image: redis:7-alpine
     ports: ["6379:6379"]
     volumes: [redis_data:/data]
     command: redis-server --appendonly yes
   ```

2. **Instalar Celery**: `pip install celery[redis]` → `requirements.txt`

3. **Criar `heparin_converter/celery.py`** com configuração do app Celery

4. **Criar `converter/tasks.py`** com `convert_xyz_to_fdf_task`:
   - Recebe bytes do XYZ + params
   - Executa conversão
   - Salva `ConversionHistory` com status `'processing'` → `'completed'` / `'failed'`
   - Atualiza campo `task_id` no model

5. **Adaptar `ConvertView.post()`**:
   - Ler arquivo como bytes
   - Submeter task: `result = convert_xyz_to_fdf_task.delay(...)`
   - Retornar JSON `{task_id, status_url}`

6. **Novas views**: `task_status` (polling), `task_download` (download quando pronto)

7. **Frontend**: spinner + polling a cada 2s no `upload.js`

### Pré-requisitos para a Onda 1A

- [ ] Container Redis rodando
- [ ] Worker Celery respondendo
- [ ] Campo `task_id` adicionado ao model `ConversionHistory`
- [ ] Migração gerada para o novo campo

---

## 📋 Checklist de Deploy

- [ ] `DEBUG=False` no `.env` de produção
- [ ] `SECRET_KEY` forte e único
- [ ] `ALLOWED_HOSTS` inclui o domínio do Render
- [ ] Banco PostgreSQL configurado (Render provisiona automaticamente)
- [ ] `python manage.py collectstatic --noinput` (executado no entrypoint)
- [ ] Volume para `media/` configurado (Render Disk ou S3)
- [ ] Health check: `GET /` retorna 200
- [ ] Admin acessível em `/admin/`
