#!/bin/sh

# Aplicar migrações do banco de dados
echo "Applying database migrations..."
python manage.py migrate

# Coletar arquivos estáticos (se ainda não feito no Dockerfile ou se precisar ser dinâmico)
# python manage.py collectstatic --noinput

# Iniciar o servidor Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 heparin_converter.wsgi
