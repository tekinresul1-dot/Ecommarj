"""
TrendyolFinancialSyncService — Trendyol CHE (Cari Hesap Ekstresi) API'den
settlements ve otherfinancials verilerini çekip CheTransaction tablosuna kaydeder.
"""
import logging
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from core.models import (
    MarketplaceAccount, CheTransaction, CargoInvoice, Order,
    FinancialTransaction, FinancialTransactionType,
)
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# CHE API requires size=500 or size=1000
CHE_PAGE_SIZE = 1000
CHE_CHUNK_DAYS = 15

SETTLEMENTS_URL = "https://apigw.trendyol.com/integration/finance/che/sellers/{seller_id}/settlements"
OTHER_FINANCIALS_URL = "https://apigw.trendyol.com/integration/finance/che/sellers/{seller_id}/otherfinancials"

SETTLEMENT_TYPES = [
    "Sale",
    "Return",
    "Discount",
    "DiscountCancel",
    "Coupon",
    "CouponCancel",
    "ProvisionPositive",
    "ProvisionNegative",
    "SellerRevenuePositive",
    "SellerRevenueNegative",
    "CommissionPositive",
    "CommissionNegative",
    "SellerRevenuePositiveCancel",
    "SellerRevenueNegativeCancel",
    "CommissionPositiveCancel",
    "CommissionNegativeCancel",
]

OTHER_FINANCIAL_TYPES = [
    "Stoppage",
    "CashAdvance",
    "WireTransfer",
    "IncomingTransfer",
    "ReturnInvoice",
    "CommissionAgreementInvoice",
    "PaymentOrder",
    "DeductionInvoices",
    "FinancialItem",
]

OTHER_FINANCIAL_SUBTYPE_QUERIES = [
    ("DeductionInvoices", "PlatformServiceFee"),
]


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


def _to_decimal(value):
    if value is None:
        return None
    return Decimal(str(value))


def _to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fetch_all_pages(url: str, headers: dict, params: dict) -> list:
    """Tüm sayfaları paginate ederek çeker."""
    import requests
    all_items = []
    page = 0
    params = dict(params)
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


def _fetch_cargo_invoice_items(account: MarketplaceAccount, invoice_serial_number: str) -> list:
    """Kargo faturasının sipariş bazlı kalemlerini çeker."""
    headers = _get_headers(account)
    url = (
        "https://apigw.trendyol.com/integration/finance/che/sellers/"
        f"{account.seller_id}/cargo-invoice/{invoice_serial_number}/items"
    )
    return _fetch_all_pages(url, headers, {"size": 500})


def _is_cargo_invoice_transaction(tx: CheTransaction) -> bool:
    text = " ".join([
        str(tx.transaction_type or ""),
        str(tx.description or ""),
        str(tx.raw_payload.get("description") if tx.raw_payload else ""),
    ]).lower()
    return "kargo" in text or "cargo" in text


def sync_cargo_invoice_items(account: MarketplaceAccount, start_ms: int, end_ms: int) -> dict:
    """
    CHE DeductionInvoices içindeki Kargo Fatura kayıtlarını sipariş bazına indirger.
    Bu olmadan gerçek kargo faturası sadece genel borç olarak kalır, sipariş kârlılığına
    dağıtılamaz.
    """
    start_dt = _ms_to_datetime(start_ms)
    end_dt = _ms_to_datetime(end_ms)
    invoice_qs = CheTransaction.objects.filter(
        account=account,
        source=CheTransaction.SOURCE_OTHER,
        transaction_type_code="DeductionInvoices",
        transaction_date__gte=start_dt,
        transaction_date__lte=end_dt,
    )

    invoice_ids = []
    for tx in invoice_qs:
        if not _is_cargo_invoice_transaction(tx):
            continue
        inv_id = tx.commission_invoice_serial_number or tx.transaction_id
        if inv_id:
            invoice_ids.append(str(inv_id))

    inserted = updated = skipped = 0
    seen_invoice_ids = sorted(set(invoice_ids))

    for invoice_id in seen_invoice_ids:
        items = _fetch_cargo_invoice_items(account, invoice_id)
        logger.info(
            f"[FinancialSync] cargo-invoice/{invoice_id}: {len(items)} items "
            f"for account {account.seller_id}"
        )
        for item in items:
            order_number = (
                item.get("orderNumber") or item.get("order_number") or
                item.get("orderNo") or item.get("orderId")
            )
            if not order_number:
                skipped += 1
                continue

            amount = _to_decimal(item.get("amount") or 0) or Decimal("0.00")
            if amount <= Decimal("0.00"):
                skipped += 1
                continue

            parcel_id = str(
                item.get("parcelUniqueId") or item.get("shipmentPackageId") or
                item.get("packageId") or item.get("id") or ""
            )
            shipment_type = (
                item.get("shipmentPackageType") or item.get("shipmentType") or
                item.get("packageType") or ""
            )

            _, created = CargoInvoice.objects.update_or_create(
                organization=account.organization,
                order_number=str(order_number),
                invoice_serial_number=invoice_id,
                parcel_unique_id=parcel_id,
                defaults={
                    "amount": amount,
                    "desi": _to_decimal(item.get("desi")),
                    "shipment_package_type": shipment_type,
                    "raw_payload": item,
                },
            )
            inserted += 1 if created else 0
            updated += 0 if created else 1

            order = Order.objects.filter(
                organization=account.organization,
                order_number=str(order_number),
            ).first()
            if not order:
                continue
            first_item = order.items.first()
            if not first_item:
                continue

            FinancialTransaction.objects.update_or_create(
                organization=account.organization,
                order_item_ref=first_item,
                transaction_type=FinancialTransactionType.SHIPPING_FEE.value,
                defaults={
                    "amount": amount,
                    "occurred_at": order.order_date,
                    "raw_payload": {**item, "invoiceSerialNumber": invoice_id},
                },
            )

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "invoice_count": len(seen_invoice_ids),
    }


def _upsert_transaction(
    account: MarketplaceAccount,
    item: dict,
    source: str,
    requested_type: str | None = None,
    requested_sub_type: str | None = None,
) -> str:
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
        "transaction_type_code": requested_type or item.get("transactionTypeCode") or item.get("type"),
        "transaction_sub_type": requested_sub_type or item.get("transactionSubType"),
        "source": source,
        "receipt_id": item.get("receiptId"),
        "description": item.get("description"),
        "debt": Decimal(str(debt_raw)),
        "credit": Decimal(str(credit_raw)),
        "commission_rate": _to_decimal(comm_rate),
        "commission_amount": _to_decimal(comm_amt),
        "seller_revenue": _to_decimal(seller_rev),
        "order_number": item.get("orderNumber"),
        "shipment_package_id": _to_int(item.get("shipmentPackageId")),
        "payment_order_id": item.get("paymentOrderId"),
        "payment_period": _to_int(item.get("paymentPeriod")),
        "payment_date": _ms_to_datetime(p_date_ms),
        "commission_invoice_serial_number": item.get("commissionInvoiceSerialNumber"),
        "seller_id": _to_int(item.get("sellerId")),
        "store_id": _to_int(item.get("storeId")),
        "store_name": item.get("storeName"),
        "store_address": item.get("storeAddress"),
        "country": item.get("country"),
        "affiliate": item.get("affiliate"),
        "order_date": _ms_to_datetime(item.get("orderDate")),
        "raw_payload": item,
        "organization": account.organization,
        "account": account,
    }

    _, created = CheTransaction.objects.update_or_create(
        account=account,
        source=source,
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
            result = _upsert_transaction(
                account,
                item,
                CheTransaction.SOURCE_SETTLEMENTS,
                requested_type=t_type,
            )
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
            result = _upsert_transaction(
                account,
                item,
                CheTransaction.SOURCE_OTHER,
                requested_type=t_type,
            )
            if result == "created":
                inserted += 1
            elif result == "updated":
                updated += 1

    for t_type, sub_type in OTHER_FINANCIAL_SUBTYPE_QUERIES:
        params = {
            "startDate": start_ms,
            "endDate": end_ms,
            "transactionType": t_type,
            "transactionSubType": sub_type,
            "size": CHE_PAGE_SIZE,
        }
        items = _fetch_all_pages(url, headers, params)
        logger.info(
            f"[FinancialSync] otherfinancials/{t_type}/{sub_type}: "
            f"{len(items)} items for account {account.seller_id}"
        )
        for item in items:
            result = _upsert_transaction(
                account,
                item,
                CheTransaction.SOURCE_OTHER,
                requested_type=t_type,
                requested_sub_type=sub_type,
            )
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

    chunks = []
    remaining = days_back
    end_ms = now_ms
    while remaining > 0:
        chunk = min(remaining, CHE_CHUNK_DAYS)
        start_ms = end_ms - int(chunk * 24 * 60 * 60 * 1000)
        chunks.append((start_ms, end_ms))
        end_ms = start_ms
        remaining -= chunk

    for start_ms, end_ms in chunks:
        s_result = sync_settlements(account, start_ms, end_ms)
        o_result = sync_other_financials(account, start_ms, end_ms)
        c_result = sync_cargo_invoice_items(account, start_ms, end_ms)
        total_inserted += s_result["inserted"] + o_result["inserted"]
        total_updated += s_result["updated"] + o_result["updated"]
        total_inserted += c_result["inserted"]
        total_updated += c_result["updated"]
        time.sleep(0.5)

    logger.info(
        f"[FinancialSync] Account {account.seller_id} done: "
        f"inserted={total_inserted} updated={total_updated}"
    )
    return {"inserted": total_inserted, "updated": total_updated}
