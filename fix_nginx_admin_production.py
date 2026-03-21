import re
import os

config_path = '/etc/nginx/sites-available/ecommarj'

if not os.path.exists(config_path):
    print(f"❌ Hata: {config_path} bulunamadı. Lütfen dosya yolunu kontrol edin.")
    exit(1)

with open(config_path, 'r') as f:
    config = f.read()

# Mevcut admin veya static bloklarını temizleyelim (çakışma olmaması için)
config = re.sub(r'\n\s*location\s+\^~?\s*/admin/?\s*\{[\s\S]*?\}', '', config)
config = re.sub(r'\n\s*location\s+/static/?\s*\{[\s\S]*?\}', '', config)

admin_blocks = """
    # Django Admin Paneli
    location ^~ /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Statik Dosyaları
    location /static/ {
        alias /home/candemir/EcomPro/backend/staticfiles/;
    }
"""

if "location / {" in config:
    print("✅ Konfigürasyon güncelleniyor...")
    config = config.replace("location / {", f"{admin_blocks}\n    location / {{")
    
    with open(config_path, 'w') as f:
        f.write(config)
    
    print("🚀 Nginx konfigürasyonu güncellendi. Lütfen 'sudo nginx -t && sudo systemctl reload nginx' komutunu çalıştırın.")
else:
    print("❌ Hata: 'location / {' bloğu bulunamadı. Manuel müdahale gerekebilir.")
