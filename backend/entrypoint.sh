#!/bin/bash
set -e

# Production-ready entrypoint script for Django

echo "⏳ PostgreSQL bekleniyor..."
# Wait robustly using python socket
while ! python -c "
import socket, os, sys
try:
    s = socket.create_connection((os.environ.get('POSTGRES_HOST','postgres'), int(os.environ.get('POSTGRES_PORT','5432'))), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
    echo "PostgreSQL'e bağlanılamadı, bekleniyor..."
    sleep 2
done
echo "✅ PostgreSQL hazır!"

# If a custom command was passed (e.g. celery worker), skip web-server setup and run it directly.
# This allows celery_worker and celery_beat to share the same image without a separate Dockerfile.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

echo "📦 Statik dosyalar toplanıyor (collectstatic)..."
python manage.py collectstatic --noinput

echo "📦 Migration'lar uygulanıyor..."
python manage.py migrate --noinput

echo "👤 Superuser kontrol ediliyor..."
# Idempotent superuser creation
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@ecommarj.local')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'✅ Superuser ({username}) tazeleyici olarak oluşturuldu!')
else:
    print(f'ℹ️  Superuser ({username}) zaten mevcut.')
"

echo "🚀 Web Sunucusu Başlatılıyor..."
if [ "$DJANGO_DEBUG" = "False" ] || [ "$DJANGO_DEBUG" = "false" ]; then
    echo "Running production server via Gunicorn..."
    exec gunicorn ecommarj_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
else
    echo "Running development server via Django runserver..."
    exec python manage.py runserver 0.0.0.0:8000
fi
