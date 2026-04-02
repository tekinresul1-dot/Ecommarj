#!/bin/bash
# Deploy Return Loss feature to server
# Run with: bash deploy_return_loss.sh
set -e

SERVER="root@91.98.226.158"
REMOTE="/var/www/EcomMarj"

echo "=== Deploying Return Loss feature ==="

# 1. models.py
echo "[1/6] Uploading models.py..."
base64 -i /Users/candemir/Desktop/EcomPro/backend/core/models.py | ssh $SERVER \
  "base64 -d > $REMOTE/backend/core/models.py && echo 'models.py OK'"

# 2. claim_sync.py
echo "[2/6] Uploading claim_sync.py..."
base64 -i /Users/candemir/Desktop/EcomPro/backend/core/services/claim_sync.py | ssh $SERVER \
  "base64 -d > $REMOTE/backend/core/services/claim_sync.py && echo 'claim_sync.py OK'"

# 3. migration 0019
echo "[3/6] Uploading migration 0019..."
base64 -i /Users/candemir/Desktop/EcomPro/backend/core/migrations/0019_returnclaim_updates_returnclaimitem.py | ssh $SERVER \
  "base64 -d > $REMOTE/backend/core/migrations/0019_returnclaim_updates_returnclaimitem.py && echo 'migration OK'"

# 4. views.py
echo "[4/6] Uploading views.py..."
base64 -i /Users/candemir/Desktop/EcomPro/backend/core/views.py | ssh $SERVER \
  "base64 -d > $REMOTE/backend/core/views.py && echo 'views.py OK'"

# 5. urls.py
echo "[5/6] Uploading urls.py..."
base64 -i /Users/candemir/Desktop/EcomPro/backend/core/urls.py | ssh $SERVER \
  "base64 -d > $REMOTE/backend/core/urls.py && echo 'urls.py OK'"

# 6. frontend returns/page.tsx
echo "[6/6] Uploading returns/page.tsx..."
ssh $SERVER "mkdir -p $REMOTE/frontend/src/app/\(dashboard\)/reports/returns"
base64 -i /Users/candemir/Desktop/EcomPro/frontend/src/app/\(dashboard\)/reports/returns/page.tsx | ssh $SERVER \
  "base64 -d > $REMOTE/frontend/src/app/\(dashboard\)/reports/returns/page.tsx && echo 'returns/page.tsx OK'"

# 7. Apply migration + restart backend
echo "[7/8] Applying migration..."
ssh $SERVER "cd $REMOTE && docker compose exec -T backend python manage.py migrate core 0019 --no-input && echo 'Migration applied'"

# 8. Restart backend + Celery
echo "[8/8] Restarting services..."
ssh $SERVER "cd $REMOTE && docker compose restart backend celery_worker celery_beat && echo 'Backend/Celery restarted'"

# 9. Rebuild frontend
echo "[9/9] Rebuilding frontend..."
ssh $SERVER "cd $REMOTE && docker compose up -d --build frontend && echo 'Frontend rebuilt'"

echo ""
echo "=== Deploy complete! ==="
echo "Test: curl -s https://ecommarj.com/api/reports/return-loss/ -H 'Authorization: Bearer <token>'"
