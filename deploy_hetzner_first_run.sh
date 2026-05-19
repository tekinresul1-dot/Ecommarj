#!/bin/bash
set -euo pipefail

DOMAIN="${DOMAIN:-ecommarj.com}"
EMAIL="${LETSENCRYPT_EMAIL:-info@ecommarj.com}"

echo "EcomMarj Hetzner ilk kurulum basliyor..."

if [ "$(id -u)" -ne 0 ]; then
  echo "Bu script root olarak calismali. Ornek: sudo DOMAIN=ecommarj.com LETSENCRYPT_EMAIL=info@ecommarj.com ./deploy_hetzner_first_run.sh"
  exit 1
fi

echo "Sistem paketleri guncelleniyor..."
apt-get update
apt-get install -y ca-certificates curl git ufw certbot

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker kuruluyor..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

echo "Firewall ayarlaniyor..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "Let's Encrypt sertifikasi kontrol ediliyor..."
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  systemctl stop nginx >/dev/null 2>&1 || true
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down >/dev/null 2>&1 || true
  certbot certonly --standalone --non-interactive --agree-tos --email "${EMAIL}" \
    -d "${DOMAIN}" -d "www.${DOMAIN}"
fi

echo "Uygulama baslatiliyor..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Durum:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo "Backend loglari:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend --tail=80

echo "Kurulum tamamlandi: https://${DOMAIN}"
