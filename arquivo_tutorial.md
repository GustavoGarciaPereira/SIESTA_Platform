# **Tutorial: Iniciando um Projeto Django e uma Aplicação**

## **Pré-requisitos**
1. **Python instalado** (versão 3.8 ou superior).  
   Verifique com:  
   ```bash
   python --version
   ```
2. **PIP** (gerenciador de pacotes Python).  
3. Ambiente virtual recomendado (ex: `venv`).

---

## **Passo 1: Instalação do Django**
```bash
pip install django
```

---

## **Passo 2: Criar um Projeto Django**
Um projeto é um contêiner para configurações e aplicações.  
Execute no terminal:
```bash
django-admin startproject meu_projeto
```
Estrutura do projeto gerada:
```
meu_projeto/
  ├── manage.py
  └── meu_projeto/
      ├── __init__.py
      ├── settings.py
      ├── urls.py
      └── wsgi.py
```

---

## **Passo 3: Iniciar uma Aplicação**
Aplicações são módulos que implementam funcionalidades específicas.  
Execute:
```bash
cd meu_projeto
python manage.py startapp minha_app
```
Estrutura da aplicação:
```
minha_app/
  ├── migrations/
  ├── __init__.py
  ├── admin.py
  ├── apps.py
  ├── models.py
  ├── tests.py
  └── views.py
```

---

## **Passo 4: Configurar o Projeto**
1. **Registrar a aplicação**:  
   Adicione `'minha_app'` à lista `INSTALLED_APPS` em `meu_projeto/settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'minha_app',
   ]
   ```

2. **Configurar banco de dados** (opcional):  
   Por padrão, Django usa SQLite. Para outros bancos, modifique `DATABASES` em `settings.py`.

3. **Configurar fuso horário/idioma**:  
   Em `settings.py`:
   ```python
   TIME_ZONE = 'America/Sao_Paulo'
   LANGUAGE_CODE = 'pt-br'
   ```

---

## **Passo 5: Criar uma View Simples**
1. Defina uma view em `minha_app/views.py`:
   ```python
   from django.http import HttpResponse

   def home(request):
       return HttpResponse("Bem-vindo ao meu projeto científico!")
   ```

2. Mapeie a URL em `minha_app/urls.py` (crie o arquivo se não existir):
   ```python
   from django.urls import path
   from . import views

   urlpatterns = [
       path('', views.home, name='home'),
   ]
   ```

3. Inclua as URLs da aplicação no projeto (`meu_projeto/urls.py`):
   ```python
   from django.contrib import admin
   from django.urls import include, path

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', include('minha_app.urls')),
   ]
   ```

---

## **Passo 6: Executar o Servidor de Desenvolvimento**
```bash
python manage.py runserver
```
Acesse `http://localhost:8000` no navegador para ver a mensagem de boas-vindas.

---

## **Passo 7: Migrações do Banco de Dados**
Crie e aplique migrações para inicializar o banco de dados:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## **Passo 8: Interface de Administração**
1. Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```
2. Registre modelos em `minha_app/admin.py` (exemplo com um modelo `Artigo`):
   ```python
   from django.contrib import admin
   from .models import Artigo

   admin.site.register(Artigo)
   ```
3. Acesse `http://localhost:8000/admin` para gerenciar dados.

---

## **Boas Práticas para Artigos Científicos**
1. **Versionamento**: Use Git para rastrear alterações.
2. **Documentação**: Inclua um `README.md` explicando o projeto.
3. **Segurança**: Nunca exponha `SECRET_KEY` ou `DEBUG=True` em produção.
4. **Reprodutibilidade**: Liste dependências em `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```

---

## **Conclusão**
Este tutorial fornece os passos essenciais para iniciar um projeto Django e uma aplicação, adequado para protótipos científicos. Para funcionalidades avançadas, explore:  
- Templates HTML
- Formulários
- APIs REST (com Django REST Framework)
- Testes automatizados

---

**Referências**  
- Documentação Oficial do Django: https://docs.djangoproject.com  
- Django REST Framework: https://www.django-rest-framework.org