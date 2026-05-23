#!/bin/bash
# ======================================================================
# EcomMarj Canlı Sunucu Teşhis ve Otomatik İyileştirme (Heal) Scripti
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
REMOTE_PATH="/opt/ecommarj"

echo -e "${CYAN}======================================================================${NC}"
echo -e "${PURPLE}🛠️  EcomMarj Canlı Sunucu Teşhis ve İyileştirme Süreci Başlıyor... 🛠️${NC}"
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
    
    echo -e "\n${BLUE}1. Mevcut Konteyner Durumları (docker compose ps):${NC}"
    docker compose ps
    
    echo -e "\n${BLUE}2. Durdurulmuş veya Hatalı Konteyner Kontrolü & Log Analizi...${NC}"
    containers=$(docker compose ps --format json | grep -v '"State":"running"' || true)
    
    if [ -n "$containers" ]; then
        echo -e "${YELLOW}⚠️  Bazı konteynerler çalışmıyor veya sağlıksız! Loglar inceleniyor...${NC}"
        # Tüm konteynerlerin durumlarını tek tek gez ve çalışmayanların logunu dök
        docker compose ps --format "{{.Name}} - {{.State}} - {{.Status}}"
        
        echo -e "${YELLOW}📝 Hata tespiti için tüm konteyner logları taranıyor...${NC}"
        docker compose logs --tail=50 || true
    else
        echo -e "${GREEN}✅ Tüm temel servisler aktif görünüyor.${NC}"
    fi

    # 3. İzin Sorunlarının Kalıcı Olarak Çözülmesi
    echo -e "\n${BLUE}3. İzin Ayarları Düzeltiliyor (Kalıcı Çözüm)...${NC}"
    # Nginx ve Backend için klasör izinlerini düzenle
    chmod 644 .env || true
    mkdir -p backend/staticfiles
    chmod -R 775 backend/staticfiles || true
    chmod -R 775 backend/core/migrations || true
    
    # 4. Veritabanı ve Migration Durumu
    echo -e "\n${BLUE}4. Migration Kontrolleri ve Veritabanı Güncellemesi...${NC}"
    # Eğer migration uyarısı varsa çalıştır
    docker compose exec -T backend python manage.py migrate --noinput || echo -e "${RED}⚠️ Migration hatası oluştu!${NC}"
    docker compose exec -T backend python manage.py collectstatic --noinput || echo -e "${RED}⚠️ Collectstatic hatası oluştu!${NC}"

    # 5. Servislerin Yeniden Başlatılması (Restart)
    echo -e "\n${BLUE}5. Servisler Yeniden Başlatılıyor (backend, celery, nginx)...${NC}"
    docker compose restart backend celery_worker celery_beat nginx
    
    echo -e "\n${BLUE}6. Güncel Konteyner Durumları:${NC}"
    docker compose ps
    
    echo -e "\n${GREEN}🎉 Sunucu içi iyileştirme adımları tamamlandı!${NC}"
EOF

echo ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}🎉 Otomatik Teşhis ve İyileştirme Scripti Başarıyla Tamamlandı! 🎉${NC}"
echo -e "${CYAN}======================================================================${NC}"
