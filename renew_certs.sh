#!/bin/bash
#
# Let's Encrypt sertifikalarını otomatik yeniler ve nginx konteynerini reload eder.
# Nginx bir konteynerde çalıştığı için "nginx -s reload" host'ta değil,
# konteyner içinde tetiklenir (deploy-hook).
#
# Kurulum (sunucuda, root):
#   sudo cp renew_certs.sh /opt/renew_certs.sh && sudo chmod +x /opt/renew_certs.sh
#   sudo mkdir -p /var/www/certbot
#   crontab -e  →  0 0 1 * * /opt/renew_certs.sh >> /var/log/ecommarj-certbot.log 2>&1
#
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
COMPOSE="docker compose -f $PROJECT_DIR/docker-compose.yml -f $PROJECT_DIR/docker-compose.prod.yml"

echo "[certbot] $(date) — yenileme denemesi"

certbot renew --quiet \
  --webroot -w /var/www/certbot \
  --deploy-hook "$COMPOSE exec -T nginx nginx -s reload"

echo "[certbot] $(date) — tamamlandı"
