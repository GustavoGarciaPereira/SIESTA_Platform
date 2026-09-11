#!/bin/sh
set -e

echo "==> Checking database configuration..."
python - <<'EOF'
import os
import sys

import django
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heparin_converter.settings")

try:
    django.setup()
    from django.conf import settings

    engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
except ImproperlyConfigured as exc:
    print(f"ERRO: configuração do Django inválida: {exc}", file=sys.stderr)
    raise SystemExit(1)

if not engine or engine == "django.db.backends.dummy":
    print("ERRO: nenhuma configuração de banco de dados encontrada (DEBUG=False).", file=sys.stderr)
    print("", file=sys.stderr)
    print("Defina UMA das opções abaixo no ambiente do serviço:", file=sys.stderr)
    print("  1. DB_ENGINE + DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT", file=sys.stderr)
    print("  2. DATABASE_URL (postgres://user:senha@host:5432/banco)", file=sys.stderr)
    print("  3. PGHOST/PGDATABASE/PGUSER/PGPASSWORD (Postgres vinculado no Render)", file=sys.stderr)
    print("", file=sys.stderr)
    print("No Render, essas variáveis precisam estar em 'Environment Variables'.", file=sys.stderr)
    print("Um Secret File '.env' fica em /etc/secrets/.env — confirme que ele", file=sys.stderr)
    print("existe e contém as chaves acima (o Django o carrega automaticamente).", file=sys.stderr)
    raise SystemExit(1)

print(f"Database configured: {engine}")
EOF

echo "==> Waiting for database..."
python manage.py wait_for_db

echo "==> Applying migrations..."
python manage.py migrate --fake-initial

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

# .mo files are pre-compiled and versioned — no need for msgfmt at deploy
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "==> Creating superuser '$DJANGO_SUPERUSER_USERNAME'..."
    python manage.py createsuperuser --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
        || echo "    Superuser already exists, skipping."
else
    echo "==> Skipping superuser creation (DJANGO_SUPERUSER_USERNAME/PASSWORD not set)."
fi

WORKERS=${GUNICORN_WORKERS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

echo "==> Starting Gunicorn (workers=$WORKERS, timeout=${TIMEOUT}s)..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile - \
    heparin_converter.wsgi
