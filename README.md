# SIESTA Platform - Conversor XYZ para FDF

**SIESTA Platform** é uma aplicação web desenvolvida em Django, projetada para simplificar o fluxo de trabalho de pesquisadores e estudantes que utilizam o software de simulação de materiais [SIESTA](https://siesta-project.org/siesta/). A plataforma oferece uma interface intuitiva para converter arquivos de coordenadas moleculares (formato `.xyz`) em arquivos de entrada para o SIESTA (formato `.fdf`), com controle total sobre os parâmetros de simulação.

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

 <!-- Substitua pelo URL de um screenshot da sua aplicação -->

## ✨ Funcionalidades Principais

- **Conversor XYZ para FDF**: Faça o upload de um arquivo `.xyz` e obtenha um arquivo `.fdf` pronto para uso, configurado através de um formulário web detalhado.
- **Visualizador 3D Interativo**: Visualize sua molécula em 3D diretamente no navegador antes de gerar o arquivo de entrada, utilizando a biblioteca [3Dmol.js](https://3dmol.csb.pitt.edu/).
- **Configuração Abrangente**: Ajuste dezenas de parâmetros do SIESTA, incluindo base de orbitais (PAO), dinâmica molecular (MD), parâmetros de SCF, funcional de troca e correlação (XC), e muito mais.
- **Download de Pseudopotenciais**: Opção para baixar um arquivo `.zip` contendo não apenas o `.fdf` gerado, mas também todos os arquivos de pseudopotencial (`.psf`) necessários para a simulação.
- **Sistema de Autenticação**: Crie uma conta, faça login e gerencie suas sessões. (Preparado para futuras funcionalidades de histórico de conversões).
- **Interface Moderna e Responsiva**: Construída com Bootstrap 5, a plataforma é fácil de usar em desktops e dispositivos móveis.
- **Pronto para Produção**: O projeto está totalmente containerizado com Docker e configurado para deploy em serviços como Render, Heroku, etc.

## 🚀 Começando

Você pode executar o projeto localmente usando Docker (recomendado) ou manualmente com um ambiente virtual Python.

### Pré-requisitos

- [Docker](https://www.docker.com/get-started) e [Docker Compose](https://docs.docker.com/compose/install/)
- Ou [Python 3.10+](https://www.python.org/) e `pip`

### 1. Instalação com Docker (Recomendado)

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/GustavoGarciaPereira/SIESTA_Platform.git
    cd SIESTA_Platform
    ```

2.  **Crie um arquivo de ambiente (`.env`):**
    Crie um arquivo chamado `.env` na raiz do projeto. Você pode começar com estas configurações básicas:
    ```env
    DEBUG=True
    SECRET_KEY='django-insecure-fallback-key-for-local-development'
    ```

3.  **Construa e inicie os containers:**
    ```bash
    docker-compose up --build
    ```
    O servidor estará rodando e aplicará as migrações automaticamente.

4.  **Acesse a aplicação:**
    Abra seu navegador e acesse `http://localhost:8000`.

### 2. Instalação Manual (Ambiente Virtual)

1.  **Clone o repositório e navegue até ele:**
    ```bash
    git clone https://github.com/GustavoGarciaPereira/SIESTA_Platform.git
    cd SIESTA_Platform
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Crie um arquivo `.env` na raiz do projeto:**
    ```env
    DEBUG=True
    SECRET_KEY='django-insecure-fallback-key-for-local-development'
    ```

5.  **Aplique as migrações do banco de dados:**
    ```bash
    python manage.py migrate
    ```

6.  **Crie um superusuário (opcional, para acesso ao admin):**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Inicie o servidor de desenvolvimento:**
    ```bash
    python manage.py runserver
    ```

8.  **Acesse a aplicação:**
    Abra seu navegador e acesse `http://localhost:8000`.

## 🛠️ Estrutura do Projeto

O projeto segue a arquitetura padrão do Django, com uma clara separação de responsabilidades:

-   `heparin_converter/`: O diretório principal do projeto Django, contendo as configurações (`settings.py`) e as URLs principais (`urls.py`).
-   `converter/`: A aplicação Django responsável por toda a lógica de conversão, incluindo:
    -   `views.py`: Contém a `ConvertView` que processa os uploads e gera os arquivos.
    -   `forms.py`: Define o `SIESTAParametersForm` com todos os campos para os parâmetros do SIESTA.
    -   `templates/converter/`: Contém o template `upload.html`, a interface principal do conversor.
-   `user/`: A aplicação Django para gerenciamento de usuários e páginas estáticas (home, sobre, contato).
-   `Dockerfile` e `entrypoint.sh`: Arquivos de configuração para containerização com Docker.
-   `requirements.txt`: Lista de dependências Python do projeto.

## 💡 Pontos de Melhoria e Futuro do Projeto

A plataforma atual é uma base robusta. As próximas etapas podem incluir:

1.  **Modelos de Dados**: Implementar modelos no banco de dados para salvar o histórico de conversões de cada usuário e permitir que salvem configurações de simulação favoritas.
2.  **Processamento Assíncrono**: Utilizar Celery ou Django-RQ para processar conversões em segundo plano, melhorando a experiência do usuário em arquivos grandes.
3.  **Integração Direta com SIESTA**: Adicionar a capacidade de submeter e executar simulações diretamente da plataforma, gerenciando filas e recursos computacionais.
4.  **Análise de Resultados**: Integrar ferramentas para visualizar e analisar os arquivos de saída do SIESTA (ex: gráficos de bandas, densidade de estados).
5.  **API REST**: Desenvolver uma API para permitir que outras ferramentas ou scripts interajam com o conversor de forma programática.
6.  **Cobertura de Testes**: Expandir os testes unitários e de integração para garantir a robustez da lógica de conversão.

## 🤝 Contribuições

Contribuições são muito bem-vindas! Se você tem sugestões de melhorias ou encontrou algum bug, sinta-se à vontade para abrir uma **Issue** ou enviar um **Pull Request**.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.
