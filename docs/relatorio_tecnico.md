# Relatório Técnico — SIESTA Platform

**Repositório:** `heparin_converter`
**Commit analisado:** `5fec10b` (branch `main` limpa, 85 commits, sincronizada com `origin/main`)
**Data do relatório:** 10/09/2026
**Stack:** Django 4.2.17 · Python 3.10 · Bootstrap 5.3 · Three.js 0.160 + Rust/WASM · SQLite (dev) / PostgreSQL (prod)
**Dimensão:** ~4.000 linhas Python + templates HTML + crate Rust
**Validação executada:** `python manage.py test converter user dashboard visualizer api` → **131/131 testes passando**. 7 testes Rust separados (`cargo test`).

> Este relatório foi produzido por leitura estática integral do código, complementada pela execução da suíte de testes. Nenhum arquivo do projeto foi modificado durante a análise.

---

## 1. Visão geral

Aplicação web Django que cobre o ciclo de uso do SIESTA:

1. **Conversor XYZ → FDF** com ~30 parâmetros SIESTA, preview AJAX e download `.fdf`/`.zip` com pseudopotenciais.
2. **Visualizador 3D de `.out`** (Three.js + parser/cálculo de campo elétrico em Rust/WASM, tudo no navegador).
3. **Autenticação, histórico de conversões e configurações salvas**.
4. **Dashboard staff-only** e páginas institucionais.

## 2. Arquitetura

| App | Prefixo | Conteúdo |
|---|---|---|
| `converter` | `/converter/` | models (UploadedFile, ConversionHistory, SavedConfiguration), utils (`read_xyz`, `bounding_box`, `convert_xyz_to_fdf`, `create_zip_archive`), forms, 10 rotas, 18 templates |
| `user` | `/` | Home/login/signup/about/contact/profile + password reset; `UserProfile` 1:1 com `User` |
| `dashboard` | `/dashboard/` | Catálogo hardcoded de URLs (staff only), sem models |
| `visualizer` | `/visualizer/` | `OutFile`, upload `.out`, APIs de conteúdo/átomos, Rust→WASM (`parse_siesta_out_full`, `compute_field_3d`, `trace_field_lines`, RK4) |

Templates globais (`base.html`, `home.html`, `about.html`, `contact.html`, auth) vivem fisicamente em `converter/templates/`, mas são renderizados pelo app `user` — acoplamento entre apps. `INSTALLED_APPS` em `heparin_converter/settings.py:41-52`; rotas raiz em `heparin_converter/urls.py`.

### Banco de dados

- `converter`: `UploadedFile`, `ConversionHistory` (nullable para anônimos), `SavedConfiguration` (`unique_together = (user, name)`).
- `user`: `UserProfile` (`email_verified` morto, `created_at`/`updated_at`).
- `visualizer`: `OutFile` (dono, arquivo, `atom_count`, `uploaded_at`).
- `dashboard`: sem models.
- 4 migrações no total (`converter` 2, `user` 1, `visualizer` 1).

## 3. Funcionalidades por app

- **Conversor** (`converter/views.py`): `ConvertView` (público, aceita anônimo), detecção automática de célula via bounding box + padding, preview AJAX/inline, download ZIP/FDF, fallback quando não há `PSEUDOPOTENTIALS_DIR`.
- **Histórico/configs**: paginação (10/página), download incrementa `download_count`, configs salvas `unique_together (user, name)` e carregamento via sessão (`loaded_config`).
- **Auth**: fluxo completo de reset com templates customizados; em DEBUG o e-mail sai no console.
- **Visualizador**: valida `.out`/`.txt` ≤10 MB, isola por dono (`get_object_or_404(..., user=request.user)`), 19 testes Django.

## 4. Infraestrutura

- **Dev:** SQLite + console email. **Prod:** PostgreSQL via variáveis `DB_*` (o `dj_database_url` está importado em `settings.py:14` mas **nunca é usado**), WhiteNoise, Gunicorn.
- Docker (estágio único), `docker-compose` com web+Postgres 13, `entrypoint.sh` (wait-for-db, migrate, collectstatic, superuser).
- i18n: pt-BR + en, `locale/` com `.po`/`.mo` (restam ~24–27 msgstr vazios e 8 fuzzy por idioma).
- `pseudos/`: apenas 5 arquivos LDA (`C, H, N, O, S`); sufixo `.lda` hardcoded mesmo com XC=GGA/PBE.
- Documentação auxiliar: `README.md`, `reasonix.md`, `.clinerules`, `docs/archive/*`, `relatorio.md` (log antigo), scripts SQL avulsos.

## 5. Testes

| App | Testes |
|---|---|
| converter | 58 |
| user | 37 |
| dashboard | 7 |
| visualizer | 22 |
| api | 7 |
| **Total Django** | **131 (OK)** |
| Rust | 7 |

Lacunas: ramo AJAX do preview, round-trip de configs salvas com booleanos, upload real de imagem, fluxo feliz do reset com token, e nenhum teste de JS.

## 6. Pontos fortes

- Código organizado, com boa separação de responsabilidades e cobertura de testes razoável.
- i18n funcional, Docker/WhiteNoise configurados, fluxo anônimo suportado.
- Visualizador é o diferencial: processamento pesado no cliente via WASM, isolamento por usuário correto.

## 7. Problemas e riscos priorizados

### Crítico

1. **`LOGIN_URL` ausente** (`settings.py:176-177`): `@login_required` redireciona para `/accounts/login/`, rota inexistente. Os testes mascaram com `assertIn('/login/')`.
2. **`contact_submit_view` é fachada** (`user/views.py:15-30`): mostra “mensagem enviada” sem enviar nada, sem formulário no template e sem `@require_POST`.
3. **Segredos**: `.env copy` contém credenciais reais e um token JWT; o Dockerfile faz `COPY . .` **sem `.dockerignore`**, levando `.env`, backups e `venv/` (Python 3.8) para a imagem.
4. **Exclusões/alterações via GET** (`delete_history`, `delete_configuration`, `load_configuration`) — sem POST/CSRF.
5. **XYZ malformado derruba a conversão com 500** (`converter/views.py:116`, sem try/except).
6. **Hardening de produção ausente**: sem `SECURE_*`, cookies seguros, HSTS ou `CSRF_TRUSTED_ORIGINS`; `ALLOWED_HOSTS=['.onrender.com']` hardcoded e o `docker-compose` não define `DEBUG`, tornando `localhost:8000` inválido (`DisallowedHost`).
7. **Histórico anônimo órfão**: grava `ConversionHistory` para anônimos, mas nenhuma view os alcança (lixo + `fdf_content` duplicado).

### Alto

8. Visualizador **não é 3D de fato**: o Rust achata todas as cargas em `z=0` (`visualizer/rust/src/lib.rs:126,189`); grade z fixa `[-2,2]`.
9. **Parser `.out` frágil e duplicado** (Rust vs `_parse_atoms_python`), com regras divergentes; Mulliken incompatível zera todas as cargas silenciosamente.
10. **Bugs de UI no visualizador**: off-by-one ao limpar a cena (`visualize.html:228`, `>6` mas há 5 objetos fixos), `infoText +=` acumula textos, divisão por zero se `nx/ny/nz==1` (`lib.rs:155`).
11. **`str(e)` vazado ao cliente** em `save_configuration` (`converter/views.py:307-308`), incluindo `IntegrityError`.
12. **Pseudos LDA hardcoded** com XC GGA/PBE e só 5 elementos — FDF aponta para pseudo inexistente.
13. **Configs salvas perdem booleanos desmarcados** (checkboxes ausentes do POST; `initial=True` restaura tudo marcado).
14. **Sem validação no upload `.xyz`**: sem extensão, tamanho máximo ou limite de átomos.
15. **`entrypoint.sh` chama `manage.py wait_for_db` inexistente** (só funciona pelo fallback inline).
16. Dependência de **CDN externo** (Three.js, Bootstrap, 3Dmol) sem fallback local.

### Médio/baixo

17. `SavedConfiguration.is_default` e `UserProfile.email_verified` são campos mortos; checkbox “remember” do login é decorativo; `lattes_url` com placeholder `SEU_ID_LATTES_ANDRE` (`user/views.py:66`).
18. Teste `dashboard...test_no_models_in_dashboard` é vacuoso (path `/workspace/dashboard`).
19. Rota legada duplicada `download_fdf_legacy`; e-mail de reset diz “24h” mas o token vale 3 dias; logout via GET deprecado no Django 4.2.
20. Campos de data manuais (sem `auto_now_add`), sem `__str__` nos models, imports mortos (`json`, `slugify`, `gettext`, `method_decorator`), `.pyc` órfãos, mensagens duplicadas em `base.html` + templates.
21. Tabela periódica duplicada (`converter/periodic_table.py` × `static/js/upload.js`).

## 8. Inconsistências de documentação

- **CLAUDE.md** fala em 3 apps (omite `visualizer`) e ainda descreve `managed=False`; o `.clinerules` cita rota inexistente `/converter/configurations/` e `DATABASE_URL`.
- **README** omite o problema de `ALLOWED_HOSTS` no Docker e lista `dj-database-url` como usado.
- `relatorio.md` é um log antigo de 88 testes (não um relatório acadêmico); `backup2/3.sql` só têm tabelas nativas (com hashes de senha) e os SQLs avulsos divergem dos models (`SERIAL` vs `BigAutoField`, `user_id NOT NULL`).

## 9. Próximos passos sugeridos (em ordem)

1. Definir `LOGIN_URL = 'login'` e `PASSWORD_RESET_TIMEOUT` — correção de 1 linha com grande impacto.
2. Criar `.dockerignore` e remover `.env copy`/backups do disco.
3. Envolver a conversão em `try/except` com erro amigável no form.
4. Compose: definir `DEBUG=True` para uso local.
5. Corrigir os bugs do visualizador (z real, limpeza de cena, `infoText`) e unificar o parser.
6. Validação de upload `.xyz` e hardening de produção.
