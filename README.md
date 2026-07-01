# 🧪 SIESTA Platform — Plataforma de Simulação de Materiais

**SIESTA Platform** é uma aplicação web Django 4.2 que cobre o ciclo completo de trabalho com o software de simulação de materiais [SIESTA](https://siesta-project.org/siesta/): da geração de arquivos de entrada (`.fdf`) à visualização 3D interativa de resultados (`.out`).

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Rust](https://img.shields.io/badge/Rust-WASM-orange.svg)](https://www.rust-lang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-107%2F5%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Funcionalidades

### ⚛️ Conversor XYZ → FDF
- Upload de arquivo `.xyz` com visualização 3D em tempo real ([3Dmol.js](https://3dmol.csb.pitt.edu/))
- **Tabela periódica completa** (118 elementos) com detecção automática de números atômicos
- **Célula automática**: `bounding_box()` + `padding` ajusta dimensões para conter a molécula
- **~30 parâmetros SIESTA**: PAO, MD, SCF, DM, XC functional, SolutionMethod
- Download do `.fdf` ou `.zip` com pseudopotenciais (`.psf`)
- Preview AJAX do FDF antes do download

### 🧲 Visualizador 3D de Resultados (`.out`)
- Upload de arquivo `.out` do SIESTA
- **Visualização 3D** com [Three.js](https://threejs.org/) + **Rust/WASM**:
  - Átomos como esferas coloridas por carga de Mulliken (azul = negativo, vermelho = positivo)
  - Vetores de campo elétrico em grade 3D configurável
  - Linhas de campo traçadas via integração RK4
- Todo o processamento ocorre no navegador (zero carga no servidor)

### 👤 Autenticação e Histórico
- Cadastro, login, logout, recuperação de senha
- **Histórico de conversões** com paginação e download/reescuta
- **Configurações salvas**: salve e reutilize conjuntos de parâmetros
- Perfil de usuário com instituição e área de pesquisa
- Dashboard administrativo (staff-only)

### 🎨 Interface
- Bootstrap 5 com tema escuro customizado (CSS variables)
- Fontes Inter + JetBrains Mono
- Totalmente responsivo (desktop e mobile)
- Bootstrap Icons

### 🐳 Deploy
- Containerização completa com Docker + Docker Compose
- PostgreSQL em produção, SQLite em desenvolvimento
- WhiteNoise para servir arquivos estáticos (compressão Brotli/Gzip)
- Gunicorn como servidor WSGI
- Entrypoint com wait-for-db, migrações automáticas e criação de superusuário

---

## 🏗️ Arquitetura

```
heparin_converter/          # Configuração do projeto Django
├── converter/              # App: conversão XYZ→FDF + histórico + configs
├── user/                   # App: autenticação + páginas institucionais
├── dashboard/              # App: painel staff-only
├── visualizer/             # App: visualização 3D de resultados .out
│   └── rust/               #   Crate Rust → WASM (siesta-field-wasm)
├── static/                 # CSS/JS customizados
├── pseudos/                # Arquivos de pseudopotencial (.psf)
├── Dockerfile + entrypoint.sh
└── docker-compose.yml
```

### Apps

| App | URL prefix | Responsabilidade |
|-----|-----------|-----------------|
| `converter` | `/converter/` | Conversão XYZ→FDF, histórico, configurações salvas |
| `user` | `/` | Home, login, signup, about, contact, perfil |
| `dashboard` | `/dashboard/` | Lista de URLs (staff only) |
| `visualizer` | `/visualizer/` | Upload e visualização 3D de `.out` |

### Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.10 + Django 4.2 |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| 3D (input) | 3Dmol.js 2.0 (CDN) |
| 3D (resultados) | Three.js 0.160 + Rust/WASM |
| Banco (dev) | SQLite3 |
| Banco (prod) | PostgreSQL 13 |
| WSGI | Gunicorn |
| Estáticos | WhiteNoise (CompressedManifestStaticFilesStorage) |
| Container | Docker + Docker Compose |

---

## 🚀 Começando

### Pré-requisitos

- [Docker](https://www.docker.com/get-started) e Docker Compose (recomendado)
- Ou Python 3.10+ com `pip` e virtualenv
- Para compilar o WASM: [Rust](https://rustup.rs/) + [wasm-pack](https://rustwasm.github.io/wasm-pack/installer/)

### Docker (Recomendado)

```bash
git clone https://github.com/GustavoGarciaPereira/SIESTA_Platform.git
cd SIESTA_Platform

# Criar .env
echo "DEBUG=True" > .env
echo "SECRET_KEY='django-insecure-fallback-key-for-local-development'" >> .env

# Iniciar
docker-compose up --build
# → http://localhost:8000
```

### Instalação Manual

```bash
git clone https://github.com/GustavoGarciaPereira/SIESTA_Platform.git
cd SIESTA_Platform

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

echo "DEBUG=True" > .env
echo "SECRET_KEY='django-insecure-dev-key'" >> .env

python manage.py migrate
python manage.py createsuperuser   # opcional
python manage.py runserver
# → http://localhost:8000
```

### Compilar o WASM (visualizador 3D)

```bash
cd visualizer/rust
wasm-pack build --target web --out-dir pkg --release
cp pkg/*.js pkg/*.wasm ../static/visualizer/wasm/
cd ../..
python manage.py collectstatic --noinput
```

---

## 🧪 Testes

```bash
# Todos os testes Django (107)
python manage.py test converter user dashboard visualizer

# Testes Rust (5)
cargo test --manifest-path visualizer/rust/Cargo.toml

# App específico
python manage.py test visualizer
python manage.py test converter.tests.ReadXyzTests
```

---

## 📄 Variáveis de Ambiente (`.env`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DEBUG` | `False` | `True` = SQLite + console email |
| `SECRET_KEY` | — | Chave secreta Django (obrigatória) |
| `DB_ENGINE` | — | Engine PostgreSQL (produção) |
| `DB_NAME` | — | Nome do banco (produção) |
| `DB_USER` | — | Usuário do banco (produção) |
| `DB_PASSWORD` | — | Senha do banco (produção) |
| `DB_HOST` | — | Host do banco (produção) |
| `DB_PORT` | — | Porta do banco (produção) |
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP (produção) |
| `EMAIL_HOST_USER` | — | Email (produção) |
| `EMAIL_HOST_PASSWORD` | — | Senha do email (produção) |

---

## 🗺️ Roadmap

### ✅ Concluído
- [x] Conversor XYZ → FDF com 30 parâmetros
- [x] Tabela periódica completa (118 elementos)
- [x] Cálculo automático de célula (`bounding_box` + `padding`)
- [x] Histórico de conversões com paginação
- [x] Configurações salvas (CRUD)
- [x] Visualizador 3D de resultados `.out` (Rust/WASM + Three.js)
- [x] Limpeza estrutural (dead code, phantom deps, duplicações)

### 🔜 Em breve
- [ ] Processamento assíncrono com Celery + Redis
- [ ] API REST (Django REST Framework + JWT)
- [ ] Modelo `Pseudopotential` com gestão no admin
- [ ] Presets de simulação + tooltips

---

## 🤝 Contribuições

Contribuições são bem-vindas! Abra uma **Issue** ou envie um **Pull Request**.

## 📄 Licença

MIT License.
