#!/bin/sh

# Aplicar migrações do banco de dados
echo "Applying database migrations..."
python manage.py migrate

# Criar superusuário (se as variáveis de ambiente estiverem definidas)
# É importante notar que este comando falhará se o superusuário já existir.
# Isso é geralmente aceitável para a configuração inicial.
echo "Creating superuser..."
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin} \
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com} \
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-1234} \
python manage.py createsuperuser --noinput || echo "Superuser already exists or an error occurred."

# Coletar arquivos estáticos (se não foi feito no Dockerfile)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput --clear

# Iniciar o servidor Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 heparin_converter.wsgi
