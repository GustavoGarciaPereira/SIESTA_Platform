#!/bin/sh
set -e

echo "==> Waiting for database..."
python manage.py wait_for_db 2>/dev/null || python - <<'EOF'
import os, time, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heparin_converter.settings")
django.setup()
from django.db import connections
from django.db.utils import OperationalError
retries = 10
for i in range(retries):
    try:
        connections["default"].ensure_connection()
        print("Database ready.")
        break
    except OperationalError:
        print(f"Database unavailable, retrying ({i+1}/{retries})...")
        time.sleep(2)
else:
    print("Could not connect to database. Aborting.")
    raise SystemExit(1)
EOF

echo "==> Applying migrations..."
python manage.py migrate --fake-initial

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "==> Creating superuser '$DJANGO_SUPERUSER_USERNAME'..."
    python manage.py createsuperuser --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
        || echo "    Superuser already exists, skipping."
else
    echo "==> Skipping superuser creation (DJANGO_SUPERUSER_USERNAME/PASSWORD not set)."
fi

WORKERS=${GUNICORN_WORKERS:-$(( $(nproc) * 2 + 1 ))}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

echo "==> Starting Gunicorn (workers=$WORKERS, timeout=${TIMEOUT}s)..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile - \
    heparin_converter.wsgi
