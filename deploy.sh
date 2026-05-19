#!/bin/bash
set -e

# ==========================================
# EcomMarj Production Deployment Automation
# ==========================================
echo "🚀 EcomMarj Deploy Süreci Başlatılıyor..."

# 1. En güncel kodları Github'dan çek (İsteğe bağlı, git kullanılmıyorsa atlanabilir)
echo "📥 Git Pull çalıştırılıyor..."
git pull origin main || echo "⚠️ Git pull başarısız veya repository değil, devam ediliyor..."

# 2. Var olan konteynerleri güvenli şekilde durdur
echo "🛑 Konteynerler durduruluyor..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 3. İmajları baştan derle ve daemon(arka plan) olarak başlat
echo "🏗️  Docker Compose build ve up ediliyor..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 4. Genel durumu ekrana yazdır
echo "📊 Konteyner Durumları:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 5. Başarıyla başlatılıp başlatılamadığını görmek için backend loglarını göster
echo "📜 Çalışan Backend Logları (Son 50 satır):"
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend --tail=50

echo "✅ Canlıya alma işlemi tamamlandı! Sisteme tarayıcıdan (IP veya Domain) erişebilirsiniz."
