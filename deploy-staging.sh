#!/bin/bash
set -e

# ==========================================
# EcomMarj Staging Deployment
# ==========================================
echo "🚀 EcomMarj Staging Deploy Başlatılıyor..."

# Pull latest staging branch
echo "📥 Git Pull (staging)..."
git pull origin staging || echo "⚠️ Git pull başarısız, devam ediliyor..."

# Stop existing staging containers
echo "🛑 Staging konteynerler durduruluyor..."
docker compose -f docker-compose.staging.yml down

# Build and start staging stack
echo "🏗️  Staging Docker Compose build ve up..."
docker compose -f docker-compose.staging.yml up -d --build

# Show status
echo "📊 Staging Konteyner Durumları:"
docker compose -f docker-compose.staging.yml ps

# Show backend logs
echo "📜 Staging Backend Logları (Son 50 satır):"
docker compose -f docker-compose.staging.yml logs backend --tail=50

echo "✅ Staging deploy tamamlandı! https://staging.ecommarj.com adresinden erişebilirsiniz."
