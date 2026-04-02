"""
TrendyolFinancialSyncService — Trendyol CHE (Cari Hesap Ekstresi) API'den
settlements ve otherfinancials verilerini çekip CheTransaction tablosuna kaydeder.
"""
import logging
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from core.models import MarketplaceAccount, CheTransaction
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# CHE API requires size=500 or size=1000
CHE_PAGE_SIZE = 500

SETTLEMENTS_URL = "https://apigw.trendyol.com/integration/finance/che/sellers/{seller_id}/settlements"
OTHER_FINANCIALS_URL = "https://apigw.trendyol.com/integration/finance/che/sellers/{seller_id}/otherfinancials"

SETTLEMENT_TYPES = ["Sale", "Return", "Discount", "Coupon"]
OTHER_FINANCIAL_TYPES = ["DeductionInvoices", "PaymentOrder", "Stoppage"]


def _get_headers(account: MarketplaceAccount) -> dict:
    import base64
    api_key = decrypt_value(account.api_key)
    api_secret = decrypt_value(account.api_secret)
    credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "User-Agent": f"{account.seller_id} - SelfIntegration",
    }


def _ms_to_datetime(ms: int):
    """Millisecond timestamp'i UTC datetime'e çevirir."""
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=dt_timezone.utc)


def _fetch_all_pages(url: str, headers: dict, params: dict) -> list:
    """Tüm sayfaları paginate ederek çeker."""
    import requests
    all_items = []
    page = 0
    while True:
        params["page"] = page
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            if r.status_code == 404:
                logger.info(f"[FinancialSync] 404 — endpoint not available: {url}")
                break
            if not r.ok:
                logger.warning(f"[FinancialSync] HTTP {r.status_code} for {url}: {r.text[:300]}")
                break
            data = r.json()
            content = data.get("content", []) or []
            all_items.extend(content)
            total_pages = data.get("totalPages", 1)
            logger.debug(f"[FinancialSync] page {page}/{total_pages} — {len(content)} items")
            if page >= total_pages - 1 or not content:
                break
            page += 1
            time.sleep(0.3)  # Rate limit koruması
        except Exception as e:
            logger.warning(f"[FinancialSync] fetch error at page {page}: {e}")
            break
    return all_items


def _upsert_transaction(account: MarketplaceAccount, item: dict, source: str) -> str:
    """API'den gelen bir kaydı CheTransaction olarak upsert eder. 'created' veya 'updated' döner."""
    transaction_id = str(item.get("id") or "")
    if not transaction_id:
        return "skipped"

    t_date_ms = item.get("transactionDate")
    p_date_ms = item.get("paymentDate")

    debt_raw = item.get("debt") or 0
    credit_raw = item.get("credit") or 0
    comm_rate = item.get("commissionRate")
    comm_amt = item.get("commissionAmount")
    seller_rev = item.get("sellerRevenue")

    defaults = {
        "transaction_date": _ms_to_datetime(t_date_ms) or datetime.now(tz=dt_timezone.utc),
        "barcode": item.get("barcode"),
        "transaction_type": item.get("transactionType") or "",
        "source": source,
        "receipt_id": item.get("receiptId"),
        "description": item.get("description"),
        "debt": Decimal(str(debt_raw)),
        "credit": Decimal(str(credit_raw)),
        "commission_rate": Decimal(str(comm_rate)) if comm_rate is not None else None,
        "commission_amount": Decimal(str(comm_amt)) if comm_amt is not None else None,
        "seller_revenue": Decimal(str(seller_rev)) if seller_rev is not None else None,
        "order_number": item.get("orderNumber"),
        "payment_order_id": item.get("paymentOrderId"),
        "payment_date": _ms_to_datetime(p_date_ms),
        "organization": account.organization,
        "account": account,
    }

    _, created = CheTransaction.objects.update_or_create(
        transaction_id=transaction_id,
        defaults=defaults,
    )
    return "created" if created else "updated"


def sync_settlements(account: MarketplaceAccount, start_ms: int, end_ms: int) -> dict:
    """Settlement tiplerini (Sale, Return, Discount, Coupon) çekip kaydeder."""
    headers = _get_headers(account)
    url = SETTLEMENTS_URL.format(seller_id=account.seller_id)
    inserted = updated = 0

    for t_type in SETTLEMENT_TYPES:
        params = {
            "startDate": start_ms,
            "endDate": end_ms,
            "transactionType": t_type,
            "size": CHE_PAGE_SIZE,
        }
        items = _fetch_all_pages(url, headers, params)
        logger.info(f"[FinancialSync] settlements/{t_type}: {len(items)} items for account {account.seller_id}")
        for item in items:
            result = _upsert_transaction(account, item, CheTransaction.SOURCE_SETTLEMENTS)
            if result == "created":
                inserted += 1
            elif result == "updated":
                updated += 1

    return {"inserted": inserted, "updated": updated}


def sync_other_financials(account: MarketplaceAccount, start_ms: int, end_ms: int) -> dict:
    """OtherFinancials tiplerini (DeductionInvoices, PaymentOrder, Stoppage) çekip kaydeder."""
    headers = _get_headers(account)
    url = OTHER_FINANCIALS_URL.format(seller_id=account.seller_id)
    inserted = updated = 0

    for t_type in OTHER_FINANCIAL_TYPES:
        params = {
            "startDate": start_ms,
            "endDate": end_ms,
            "transactionType": t_type,
            "size": CHE_PAGE_SIZE,
        }
        items = _fetch_all_pages(url, headers, params)
        logger.info(f"[FinancialSync] otherfinancials/{t_type}: {len(items)} items for account {account.seller_id}")
        for item in items:
            result = _upsert_transaction(account, item, CheTransaction.SOURCE_OTHER)
            if result == "created":
                inserted += 1
            elif result == "updated":
                updated += 1

    return {"inserted": inserted, "updated": updated}


def sync_financials_for_account(account: MarketplaceAccount, days_back: int = 15) -> dict:
    """
    Hesap için finansal verileri senkronize eder.
    CHE API 15 günden fazla aralık desteklemeyebileceğinden 15'er günlük parçalara böler.
    """
    now_ms = int(datetime.now(dt_timezone.utc).timestamp() * 1000)
    total_inserted = total_updated = 0

    chunk_days = 15
    chunks = []
    remaining = days_back
    end_ms = now_ms
    while remaining > 0:
        chunk = min(remaining, chunk_days)
        start_ms = end_ms - int(chunk * 24 * 60 * 60 * 1000)
        chunks.append((start_ms, end_ms))
        end_ms = start_ms
        remaining -= chunk

    for start_ms, end_ms in chunks:
        s_result = sync_settlements(account, start_ms, end_ms)
        o_result = sync_other_financials(account, start_ms, end_ms)
        total_inserted += s_result["inserted"] + o_result["inserted"]
        total_updated += s_result["updated"] + o_result["updated"]
        time.sleep(0.5)

    logger.info(
        f"[FinancialSync] Account {account.seller_id} done: "
        f"inserted={total_inserted} updated={total_updated}"
    )
    return {"inserted": total_inserted, "updated": total_updated}
