#!/bin/bash
#
# Günlük PostgreSQL yedeği — gzip'lenmiş pg_dump + 7 gün lokal retention.
#
# Kurulum (sunucuda):
#   sudo cp backup.sh /opt/backup.sh && sudo chmod +x /opt/backup.sh
#   sudo mkdir -p /backups
#   crontab -e  →  0 2 * * * /opt/backup.sh >> /var/log/ecommarj-backup.log 2>&1
#
set -euo pipefail

# Repo kökü (compose dosyalarının bulunduğu dizin) — gerekirse override edin.
PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/backend/.env}"

# DB kimlik bilgilerini backend/.env'den oku (varsa)
if [ -f "$ENV_FILE" ]; then
  POSTGRES_USER="$(grep -E '^POSTGRES_USER=' "$ENV_FILE" | tail -1 | cut -d= -f2-)"
  POSTGRES_DB="$(grep -E '^POSTGRES_DB=' "$ENV_FILE" | tail -1 | cut -d= -f2-)"
fi
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-postgres}"

mkdir -p "$BACKUP_DIR"
DATE="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/db_${DATE}.sql.gz"

echo "[backup] $(date) — ${POSTGRES_DB} yedekleniyor → ${OUT}"

# postgres servisi compose ile çalışıyor; -T => TTY yok (cron uyumlu)
docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT"

# Boş/başarısız dump'ı bırakma
if [ ! -s "$OUT" ]; then
  echo "[backup] HATA: yedek dosyası boş, siliniyor." >&2
  rm -f "$OUT"
  exit 1
fi

# Retention: N günden eski yedekleri sil
find "$BACKUP_DIR" -name 'db_*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete

echo "[backup] $(date) — tamamlandı ($(du -h "$OUT" | cut -f1))"
