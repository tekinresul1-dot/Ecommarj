#!/bin/bash
# ======================================================================
# EcomMarj Canlı Sunucu Prod Modu Kurtarma (Restore) Scripti
# ======================================================================

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVER="root@178.105.146.178"

echo -e "${CYAN}======================================================================${NC}"
echo -e "${PURPLE}🚀 EcomMarj Canlı Sunucu Nginx SSL & Prod Kurtarma Başlıyor... 🚀${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

echo -e "${BLUE}📡 Canlı Sunucuya Bağlanılıyor (${SERVER})...${NC}"

ssh -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
    set -e
    
    # Sunucu içi renkler
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    
    cd /opt/ecommarj
    
    echo -e "\n${BLUE}🔄 En güncel prod konfigürasyonları çekiliyor...${NC}"
    git pull origin main || echo "⚠️ Git pull atlandı."
    
    echo -e "\n${BLUE}🛑 Mevcut (hatalı/yarım) konteynerler durduruluyor...${NC}"
    docker compose down || true
    docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true
    
    echo -e "\n${BLUE}🏗️  Production modunda (SSL/443 aktif) servisler ayağa kaldırılıyor...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    
    echo -e "\n${BLUE}🗄️  Django veritabanı migration'ları ve statik dosyalar derleniyor...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput
    
    echo -e "\n${BLUE}🔄 Servisler son kontroller için restart ediliyor...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend celery_worker celery_beat nginx
    
    echo -e "\n${GREEN}📊 Konteyner Durumları (docker compose ps):${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
    
    echo -e "\n${BLUE}📜 Backend Logları:${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=50 backend
    
    echo -e "\n${GREEN}✅ Sunucu kurtarma ve production deploy başarıyla tamamlandı!${NC}"
EOF

echo ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}🎉 Production Kurtarma Scripti Başarıyla Tamamlandı! 🎉${NC}"
echo -e "${CYAN}======================================================================${NC}"
