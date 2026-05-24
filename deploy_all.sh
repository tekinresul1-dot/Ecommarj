#!/bin/bash
set -e

# Curated HSL colors for stunning terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================================${NC}"
echo -e "${PURPLE}🚀 EcomMarj Premium Tek Tıkla Canlıya Alma (Deploy) Otomasyonu 🚀${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# 1. Yerel Git Durumu Kontrolü
echo -e "${BLUE}[1/3] Yerel Git Durumu Kontrol Ediliyor...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Yerel dizinde commit edilmemiş değişiklikler var. Devam ediliyor...${NC}"
else
    echo -e "${GREEN}✅ Yerel çalışma dizini temiz.${NC}"
fi
echo ""

# 2. GitHub'a Push Yap
echo -e "${BLUE}[2/3] Değişiklikler GitHub'a Aktarılıyor (git push)...${NC}"
git -c credential.helper= push origin main
echo -e "${GREEN}✅ GitHub push başarıyla tamamlandı!${NC}"
echo ""

# 3. Canlı Sunucuya SSH ile Bağlan ve Deploy Komutlarını Çalıştır
SERVER="ecommarj-hetzner"
echo -e "${BLUE}[3/3] Canlı Sunucuya Bağlanılıyor (${SERVER}) ve Deploy Yapılıyor...${NC}"

ssh -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
    set -e
    
    # HSL Colors inside SSH
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    
    echo -e "${BLUE}⚡ Sunucu dizinine geçiliyor (/opt/ecommarj)...${NC}"
    cd /opt/ecommarj
    
    echo -e "${BLUE}📥 Yeni kodlar çekiliyor (git pull)...${NC}"
    git pull origin main
    
    echo -e "${BLUE}📊 Docker Konteyner durumları listeleniyor...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
    
    echo -e "${BLUE}🏗️  Docker imajları baştan derleniyor (no-cache)...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
    
    echo -e "${BLUE}🚀 Konteynerler başlatılıyor (up -d)...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    echo -e "${BLUE}🗄️  Django veritabanı migration'ları uygulanıyor...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py migrate
    
    echo -e "${BLUE}📁 Statik dosyalar toplanıyor (collectstatic)...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
    
    echo -e "${GREEN}✅ Sunucuda deploy adımları başarıyla tamamlandı!${NC}"
    echo ""
    echo -e "${BLUE}📜 Son 100 Backend Logu:${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=100 backend
EOF

echo ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}🎉 Tebrikler! EcomMarj Canlı Sunucu Deploy İşlemi Başarıyla Tamamlandı! 🎉${NC}"
echo -e "${CYAN}======================================================================${NC}"
