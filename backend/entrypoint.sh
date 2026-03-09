#!/bin/bash
set -e

echo "⏳ PostgreSQL bekleniyor..."
while ! python -c "
import socket, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((os.environ.get('POSTGRES_HOST','postgres'), int(os.environ.get('POSTGRES_PORT','5432'))))
    s.close()
    exit(0)
except Exception as e:
    import sys
    print(e, file=sys.stderr)
    exit(1)
" || true; do
    sleep 2
done
echo "✅ PostgreSQL hazır!"

echo "📦 Migration'lar uygulanıyor..."
python manage.py migrate --noinput

echo "👤 Superuser kontrol ediliyor..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME:-admin}').exists():
    User.objects.create_superuser(
        username='${DJANGO_SUPERUSER_USERNAME:-admin}',
        email='${DJANGO_SUPERUSER_EMAIL:-admin@ecommarj.local}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin123}'
    )
    print('✅ Superuser oluşturuldu!')
else:
    print('ℹ️  Superuser zaten mevcut.')
"

echo "🚀 Sunucu başlatılıyor..."
if [ "$DJANGO_DEBUG" = "False" ] || [ "$DJANGO_DEBUG" = "false" ]; then
    echo "Using Gunicorn for production"
    exec gunicorn ecommarj_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3
else
    echo "Using Django runserver for development"
    exec python manage.py runserver 0.0.0.0:8000
fi
