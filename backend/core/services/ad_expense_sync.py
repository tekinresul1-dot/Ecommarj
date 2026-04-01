"""
TrendyolAdExpenseSyncService — Trendyol finance/transactions API'den
reklam giderlerini çekip AdExpense tablosuna kaydeder.
"""
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.utils import timezone

from core.models import MarketplaceAccount, AdExpense, SyncAuditLog
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# Trendyol transactionType → expense_type eşlemesi
ADVERTISING_TYPES = {
    "AdvertisingInvoice",
    "CampaignBudget",
    "PromotionBudget",
    "SponsoredProduct",
    "SponsoredBrand",
    "advertisement",
    "AD_CAMPAIGN",
    "ADVERTISING",
}

INFLUENCER_TYPES = {
    "InfluencerFee",
    "influencer",
    "INFLUENCER",
}

# Trendyol finance API endpoint (CHE = Cari Hesap Ekstresi)
FINANCE_TRANSACTION_URL = (
    "https://apigw.trendyol.com/integration/finance/che/sellers/{seller_id}/transactions"
)
FINANCE_SETTLEMENT_URL = (
    "https://apigw.trendyol.com/integration/finance/sellers/{seller_id}/settlements"
)


class TrendyolAdExpenseSyncService:
    """Trendyol'dan reklam giderlerini senkronize eder."""

    def __init__(self, account: MarketplaceAccount):
        self.account = account
        self.organization = account.organization
        self.api_key = decrypt_value(account.api_key)
        self.api_secret = decrypt_value(account.api_secret)
        self.seller_id = account.seller_id
        self._inserted = 0
        self._updated = 0
        self._skipped = 0

    def _get_headers(self) -> dict:
        import base64
        credentials = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode()
        ).decode()
        return {
            "Authorization": f"Basic {credentials}",
            "User-Agent": f"{self.seller_id} - SelfIntegration",
        }

    def _fetch_transactions(self, start_ms: int, end_ms: int, transaction_type: str = "") -> list:
        """Trendyol CHE transactions API'sinden veri çeker."""
        import requests
        headers = self._get_headers()
        url = FINANCE_TRANSACTION_URL.format(seller_id=self.seller_id)
        params = {
            "startDate": start_ms,
            "endDate": end_ms,
            "page": 0,
            "size": 200,
        }
        if transaction_type:
            params["transactionType"] = transaction_type

        all_items = []
        page = 0
        while True:
            params["page"] = page
            try:
                r = requests.get(url, headers=headers, params=params, timeout=30)
                if r.status_code == 404:
                    logger.info(f"[AdExpenseSync] CHE transactions endpoint 404 — skipping.")
                    break
                if not r.ok:
                    logger.warning(f"[AdExpenseSync] CHE transactions returned {r.status_code}: {r.text[:200]}")
                    break
                data = r.json()
                content = data.get("content", []) or data.get("transactions", []) or []
                all_items.extend(content)
                total_pages = data.get("totalPages", 1)
                if page >= total_pages - 1 or not content:
                    break
                page += 1
            except Exception as e:
                logger.warning(f"[AdExpenseSync] fetch error: {e}")
                break

        return all_items

    def _fetch_settlements(self, start_ms: int, end_ms: int) -> list:
        """Fallback: settlement endpoint'inden reklam giderlerini bul."""
        import requests
        headers = self._get_headers()
        url = FINANCE_SETTLEMENT_URL.format(seller_id=self.seller_id)
        params = {"startDate": start_ms, "endDate": end_ms, "page": 0, "size": 200}
        all_items = []
        page = 0
        while True:
            params["page"] = page
            try:
                r = requests.get(url, headers=headers, params=params, timeout=30)
                if not r.ok:
                    break
                data = r.json()
                content = data.get("content", []) or []
                all_items.extend(content)
                if page >= data.get("totalPages", 1) - 1 or not content:
                    break
                page += 1
            except Exception as e:
                logger.warning(f"[AdExpenseSync] settlement fetch error: {e}")
                break
        return all_items

    def _determine_expense_type(self, transaction_type: str) -> str:
        t = transaction_type or ""
        if any(k.lower() in t.lower() for k in INFLUENCER_TYPES):
            return AdExpense.ExpenseType.INFLUENCER
        if any(k.lower() in t.lower() for k in ADVERTISING_TYPES):
            return AdExpense.ExpenseType.ADVERTISING
        return AdExpense.ExpenseType.OTHER

    def _upsert_expense(self, transaction_date, transaction_type: str,
                        amount: Decimal, description: str,
                        external_id: str, raw_payload: dict):
        expense_type = self._determine_expense_type(transaction_type)

        if external_id:
            obj, created = AdExpense.objects.update_or_create(
                organization=self.organization,
                external_id=external_id,
                defaults={
                    "marketplace_account": self.account,
                    "transaction_date": transaction_date,
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "description": description,
                    "expense_type": expense_type,
                    "raw_payload": raw_payload,
                },
            )
            if created:
                self._inserted += 1
            else:
                self._updated += 1
        else:
            AdExpense.objects.create(
                organization=self.organization,
                marketplace_account=self.account,
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                expense_type=expense_type,
                raw_payload=raw_payload,
            )
            self._inserted += 1

    def sync(self, days_back: int = 30) -> dict:
        """Senkronizasyonu çalıştırır ve istatistik döner."""
        self._inserted = 0
        self._updated = 0
        self._skipped = 0

        now = datetime.now(dt_timezone.utc)
        start = now - timedelta(days=days_back)
        start_ms = int(start.timestamp() * 1000)
        end_ms   = int(now.timestamp() * 1000)

        # Her iki reklam tipi için dene
        transactions = []
        for ad_type in ("AdvertisingInvoice", ""):
            batch = self._fetch_transactions(start_ms, end_ms, ad_type)
            transactions.extend(batch)
            if batch and not ad_type:
                break

        # Filtreleme: sadece reklam/influencer tiplerini al
        ad_transactions = []
        for txn in transactions:
            t_type = (
                txn.get("transactionType") or
                txn.get("type") or ""
            )
            et = self._determine_expense_type(t_type)
            if et != AdExpense.ExpenseType.OTHER:
                ad_transactions.append((txn, t_type, et))

        for txn, t_type, _ in ad_transactions:
            try:
                amount_raw = txn.get("amount") or txn.get("totalAmount") or 0
                amount = abs(Decimal(str(amount_raw)))
                if amount == Decimal("0"):
                    continue

                ts = txn.get("transactionDate") or txn.get("date") or 0
                if ts:
                    dt = datetime.fromtimestamp(ts / 1000.0, tz=dt_timezone.utc).date()
                else:
                    dt = now.date()

                ext_id = str(txn.get("id") or txn.get("transactionId") or "")
                desc = txn.get("description") or txn.get("note") or t_type

                self._upsert_expense(dt, t_type, amount, desc, ext_id, txn)
            except Exception as e:
                logger.warning(f"[AdExpenseSync] upsert error: {e}")

        logger.info(
            f"[AdExpenseSync] Done: inserted={self._inserted} "
            f"updated={self._updated} skipped={self._skipped}"
        )
        return {
            "inserted": self._inserted,
            "updated": self._updated,
            "skipped": self._skipped,
            "total_fetched": len(transactions),
        }
