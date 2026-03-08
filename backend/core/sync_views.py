"""
Sync API Views — REST endpoints for triggering and monitoring Trendyol sync operations.
"""
import logging
from datetime import datetime, timezone as dt_timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import MarketplaceAccount, SyncAuditLog, SyncCheckpoint

logger = logging.getLogger(__name__)


def _get_account(user):
    """Get the user's active MarketplaceAccount."""
    profile = getattr(user, "profile", None)
    if not profile or not profile.organization:
        return None
    return MarketplaceAccount.objects.filter(
        organization=profile.organization,
        is_active=True,
    ).first()


class TrendyolFullSyncView(APIView):
    """POST /api/sync/trendyol/orders/full/ — Trigger full order sync."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account = _get_account(request.user)
        if not account:
            return Response({"error": "Aktif Trendyol hesabı bulunamadı"}, status=400)

        days = int(request.data.get("days", 365))

        try:
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(account)
            audit = service.full_sync(days=days)
            return Response({
                "status": "success",
                "total_fetched": audit.total_fetched,
                "inserted": audit.inserted,
                "updated": audit.updated,
                "skipped": audit.skipped,
                "failed": audit.failed,
                "duration_seconds": audit.duration_seconds,
            })
        except Exception as e:
            logger.error(f"Full sync failed: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)


class TrendyolIncrementalSyncView(APIView):
    """POST /api/sync/trendyol/orders/incremental/ — Trigger incremental order sync."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account = _get_account(request.user)
        if not account:
            return Response({"error": "Aktif Trendyol hesabı bulunamadı"}, status=400)

        try:
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(account)
            audit = service.incremental_sync()
            return Response({
                "status": "success",
                "total_fetched": audit.total_fetched,
                "inserted": audit.inserted,
                "updated": audit.updated,
                "skipped": audit.skipped,
                "failed": audit.failed,
                "duration_seconds": audit.duration_seconds,
            })
        except Exception as e:
            logger.error(f"Incremental sync failed: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)


class TrendyolBackfillSyncView(APIView):
    """POST /api/sync/trendyol/orders/backfill/ — Backfill a specific date range."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account = _get_account(request.user)
        if not account:
            return Response({"error": "Aktif Trendyol hesabı bulunamadı"}, status=400)

        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")
        if not start_date_str or not end_date_str:
            return Response({"error": "start_date ve end_date zorunlu"}, status=400)

        try:
            start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=dt_timezone.utc)
            end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=dt_timezone.utc)
        except ValueError:
            return Response({"error": "Tarih formatı: YYYY-MM-DD"}, status=400)

        try:
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(account)
            audit = service.backfill_sync(start_date=start_date, end_date=end_date)
            return Response({
                "status": "success",
                "total_fetched": audit.total_fetched,
                "inserted": audit.inserted,
                "updated": audit.updated,
                "skipped": audit.skipped,
                "failed": audit.failed,
                "duration_seconds": audit.duration_seconds,
            })
        except Exception as e:
            logger.error(f"Backfill sync failed: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)


class TrendyolClaimsSyncView(APIView):
    """POST /api/sync/trendyol/claims/ — Sync return/refund claims."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account = _get_account(request.user)
        if not account:
            return Response({"error": "Aktif Trendyol hesabı bulunamadı"}, status=400)

        days_back = int(request.data.get("days_back", 30))

        try:
            from core.services.claim_sync import TrendyolClaimSyncService
            service = TrendyolClaimSyncService(account)
            audit = service.sync_claims(days_back=days_back)
            return Response({
                "status": "success",
                "total_fetched": audit.total_fetched,
                "inserted": audit.inserted,
                "updated": audit.updated,
                "skipped": audit.skipped,
                "failed": audit.failed,
                "duration_seconds": audit.duration_seconds,
            })
        except Exception as e:
            logger.error(f"Claims sync failed: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)


class TrendyolWebhookView(APIView):
    """POST /api/integrations/trendyol/webhook/ — Process Trendyol webhook events."""
    permission_classes = []  # Webhook — no auth (Trendyol sends events)

    def post(self, request):
        event_type = request.data.get("eventType") or request.data.get("type", "")
        logger.info(f"[Webhook] Received event: {event_type}")

        # Store raw event for debugging
        try:
            order_number = request.data.get("orderNumber") or request.data.get("shipmentPackageId")
            if not order_number:
                return Response({"status": "ignored"})

            # Find account from data
            seller_id = request.data.get("sellerId") or request.data.get("supplierId", "")
            account = MarketplaceAccount.objects.filter(
                seller_id=str(seller_id), is_active=True
            ).first()

            if not account:
                logger.warning(f"[Webhook] No account for seller_id={seller_id}")
                return Response({"status": "ignored"})

            # Trigger incremental sync for this account
            from core.tasks import trendyol_incremental_sync
            trendyol_incremental_sync.delay(account.id)

            return Response({"status": "accepted"})

        except Exception as e:
            logger.error(f"[Webhook] Error processing event: {e}", exc_info=True)
            return Response({"status": "error"}, status=500)


class SyncStatusView(APIView):
    """GET /api/dashboard/sync-status/ — Check sync health."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = _get_account(request.user)
        if not account:
            return Response({"error": "Hesap bulunamadı"}, status=400)

        # Last sync info
        checkpoints = {}
        for cp in SyncCheckpoint.objects.filter(marketplace_account=account):
            checkpoints[cp.sync_type] = {
                "last_sync": cp.last_successful_sync_at.isoformat(),
                "last_modified_date": cp.last_fetched_modified_date.isoformat() if cp.last_fetched_modified_date else None,
            }

        # Recent audit logs
        recent_logs = SyncAuditLog.objects.filter(
            marketplace_account=account
        ).order_by("-started_at")[:10]

        logs = [{
            "id": log.id,
            "sync_type": log.sync_type,
            "sync_mode": log.sync_mode,
            "started_at": log.started_at.isoformat(),
            "success": log.success,
            "total_fetched": log.total_fetched,
            "inserted": log.inserted,
            "updated": log.updated,
            "skipped": log.skipped,
            "failed": log.failed,
            "duration_seconds": log.duration_seconds,
            "error_message": log.error_message,
        } for log in recent_logs]

        # Overall status
        last_order_sync = SyncAuditLog.objects.filter(
            marketplace_account=account,
            sync_type="orders",
            success=True,
        ).order_by("-finished_at").first()

        sync_status = "ready"
        if not last_order_sync:
            sync_status = "never_synced"
        elif not last_order_sync.success:
            sync_status = "failed"

        return Response({
            "sync_status": sync_status,
            "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
            "checkpoints": checkpoints,
            "recent_logs": logs,
        })
