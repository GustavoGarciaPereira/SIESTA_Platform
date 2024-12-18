# Usar imagem base do Python
FROM python:3.10-slim

# Configurar diretório de trabalho no container
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos do projeto
COPY . .

# Instalar dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1

RUN python manage.py migrate
RUN python manage.py collectstatic --noinput
RUN DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=1234 python manage.py createsuperuser --noinput

# Executar o servidor com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "heparin_converter.wsgi"]