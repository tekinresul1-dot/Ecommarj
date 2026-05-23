from decimal import Decimal
from typing import Optional

from core.models import CheTransaction, OrderItem


SALE_TYPE_CODES = {"Sale"}
SALE_TYPE_LABELS = {"satış", "satis", "sale"}


def get_order_che_settlements(order) -> list[CheTransaction]:
    """Bir siparişin CHE settlement kayıtlarını request/process içinde memoize ederek döndürür."""
    cached = getattr(order, "_che_settlements_memo", None)
    if cached is not None:
        return cached

    order_num = str(order.order_number or order.marketplace_order_id or "")
    if not order_num:
        order._che_settlements_memo = []
        return []

    qs = CheTransaction.objects.filter(
        account=order.marketplace_account,
        source=CheTransaction.SOURCE_SETTLEMENTS,
        order_number=order_num,
    )
    order._che_settlements_memo = list(qs)
    return order._che_settlements_memo


def is_sale_transaction(tx: CheTransaction) -> bool:
    code = tx.transaction_type_code or ""
    label = (tx.transaction_type or "").strip().lower()
    return code in SALE_TYPE_CODES or label in SALE_TYPE_LABELS


def find_sale_transaction_for_item(order_item: OrderItem) -> Optional[CheTransaction]:
    """orderNumber + barcode/SKU ile sipariş satırının satış CHE kaydını bulur."""
    order = order_item.order
    barcode = order_item.sku or ""
    che_list = get_order_che_settlements(order)

    if barcode:
        matched = next(
            (tx for tx in che_list if tx.barcode == barcode and is_sale_transaction(tx)),
            None,
        )
        if matched:
            return matched

    return next((tx for tx in che_list if is_sale_transaction(tx)), None)


def get_real_commission_amount(order_item: OrderItem) -> Optional[Decimal]:
    tx = find_sale_transaction_for_item(order_item)
    if tx and tx.commission_amount and tx.commission_amount > Decimal("0"):
        return abs(tx.commission_amount)
    return None
