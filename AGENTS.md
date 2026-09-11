# AGENTS.md

Guia para agentes de IA (opencode, Claude Code, Cursor, etc.) que trabalham neste repositório.

## Regra principal do projeto

**Nenhuma alteração deve ser commitada sem validação explícita do mantenedor.** Sempre mostre o diff/resumo e aguarde o "ok". Nunca faça `git commit`, `git push` ou crie PR por iniciativa própria.

## Visão geral

**SIESTA Platform** é uma aplicação Django 4.2 que cobre o ciclo de trabalho com o software [SIESTA](https://siesta-project.org/siesta/):

1. Conversão de arquivos `.xyz` em arquivos de entrada `.fdf` (com download de pseudopotenciais).
2. Visualização 3D de arquivos de saída `.out` (Three.js + Rust/WASM).
3. Autenticação, histórico de conversões, configurações salvas e dashboard staff-only.

## Comandos

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
printf 'DEBUG=True\nSECRET_KEY=django-insecure-fallback-key-for-local-development\n' > .env
python manage.py migrate
```

### Desenvolvimento

```bash
python manage.py runserver        # http://localhost:8000
python manage.py createsuperuser
python manage.py collectstatic    # necessário após mexer em estáticos
```

### Testes

```bash
python manage.py test                                   # descobre todos os apps
python manage.py test converter user dashboard visualizer  # suíte completa (111 testes)
python manage.py test converter.tests.ConvertViewTests  # app/classe específica

cargo test --manifest-path visualizer/rust/Cargo.toml   # 7 testes Rust
bash visualizer/rust/build.sh                           # rebuild do WASM
```

Ao alterar `visualizer/rust/src/lib.rs`, **rebuilde o WASM** (`build.sh`) antes de considerar a tarefa concluída — os binários em `visualizer/static/visualizer/wasm/` são versionados.

### Docker

```bash
docker compose up --build
```

O `docker-compose.yml` define `DEBUG=True` (SQLite + console e-mail) para uso local.

## Arquitetura

Quatro apps Django sob `heparin_converter/`:

| App | Prefixo | Responsabilidade |
|-----|---------|------------------|
| `converter` | `/converter/` | Conversão XYZ→FDF, histórico, configurações salvas |
| `user` | `/` | Home, login, signup, about, contato, perfil, password reset |
| `dashboard` | `/dashboard/` | Catálogo de URLs (staff only) |
| `visualizer` | `/visualizer/` | Upload/visualização 3D de `.out` (Rust/WASM + Three.js) |

Templates globais (`base.html`, `home.html`, `about.html`, `contact.html`, auth) vivem em `converter/templates/` mesmo sendo usados pelo app `user`.

### Fluxo de conversão

1. Upload do `.xyz` + `SIESTAParametersForm` (`converter/forms.py`).
2. `ConvertView.post()` valida o form (extensão `.xyz`, ≤ 5 MB, XC coerente) e chama `convert_xyz_to_fdf()` (`converter/utils.py`).
3. Erros de parsing viram erro de formulário (nunca 500).
4. Download `.fdf` ou `.zip` (`.fdf` + `.psf`; ausentes geram `AVISO_pseudopotenciais_faltantes.txt`).
5. Histórico é salvo **somente para usuários autenticados**.
6. Preview: JSON (AJAX) ou render com `preview_content`.

### Models

- `converter`: `UploadedFile`, `ConversionHistory` (user nullable), `SavedConfiguration` (`unique_together (user, name)`).
- `user`: `UserProfile` 1:1 com `User`; criado automaticamente via signal `user/signals.py`.
- `visualizer`: `OutFile` (isolado por dono).
- Models gerenciados pelo Django (sem `managed = False`); migrações criam as tabelas.

### Pseudopotenciais

`pseudos/{Symbol}.lda.psf` (apenas C, H, N, O, S). O sufixo `.lda` é fixo no FDF e no ZIP; `XC_functional != LDA` emite aviso, mas continua referenciando `.lda.psf`.

## Convenções importantes

- **Mutações exigem POST:** `delete_history`, `delete_configuration`, `load_configuration`, `delete_out`, `contact_submit`, `save_configuration` usam `@require_POST`.
- **Autenticação:** `LOGIN_URL = 'login'`; views usam `@login_required`. Login tem opção "Lembrar meus dados" (14 dias) via `CustomLoginView`.
- **Filtrar por dono:** sempre `get_object_or_404(Model, id=..., user=request.user)`.
- **i18n:** `LANGUAGE_CODE='pt-br'`, idiomas `pt-br`/`en`, catálogos em `locale/`; use `{% trans %}`/`gettext`. O `DefaultLanguageMiddleware` mantém pt-BR até o usuário escolher outro idioma no seletor (cookie). Após adicionar strings:
  ```bash
  python manage.py makemessages -l pt_BR -l en --no-obsolete --ignore=venv
  python manage.py compilemessages
  ```
  **Sempre** use `--ignore=venv` (senão o xgettext varre o virtualenv e polui os `.po`).
- **Tabela periódica:** fonte única em `converter/periodic_table.py`; o frontend recebe via `window.ATOMIC_NUMBER_TO_SYMBOL` injetado em `upload.html` (não duplicar no JS).
- **Pseudos e estáticos:** `CompressedManifestStaticFilesStorage` — rode `collectstatic` após mudanças em `static/`.

## Variáveis de ambiente (`.env`)

| Variável | Efeito |
|----------|--------|
| `DEBUG` | `True` = SQLite + console e-mail; `False` = PostgreSQL + SMTP + hardening |
| `SECRET_KEY` | Obrigatória em produção |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Hosts/origens (produção, separados por vírgula) |
| `DB_*` | PostgreSQL de produção (`DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_SSLMODE`) |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | SMTP de produção |
| `CONTACT_EMAIL` | Destino do formulário de contato |

## Testes — convenções e pegadinhas

- `RequestFactory` puro não tem middleware de mensagens; se a view usa `messages`, adicione `FallbackStorage`.
- Não passe `content_type='application/x-www-form-urlencoded'` com `dict` no `client.post()`.
- Mensagens de erro estão em português (`'Erro'`, `'bi-exclamation-circle'`, `'e-mail'`).
- `slugify` remove pontos: `v1.0` → `v10`.
- Novos testes devem acompanhar correções; a suíte precisa ficar 100% verde antes de pedir validação.

## Estrutura de diretórios (resumo)

```
converter/        # app principal + templates globais
user/             # auth, perfil, contato
dashboard/        # catálogo staff
visualizer/       # app 3D
  rust/           # crate siesta-field-wasm
  static/visualizer/wasm/  # WASM versionado
pseudos/          # .psf (LDA)
locale/           # pt_BR + en
static/           # CSS/JS do projeto
heparin_converter/settings.py
```
