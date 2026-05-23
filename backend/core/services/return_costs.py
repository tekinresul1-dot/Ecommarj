from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.db.models import Sum

from core.models import CargoInvoice, CheTransaction, Order, OrderItem, ReturnClaim
from core.services.profit_calculator import _get_carrier_flat_rate, _normalize_carrier


Q2 = Decimal("0.01")
RETURN_STATUSES = {"Returned", "UnDelivered"}
RETURN_TYPE_CODES = {"Return"}
RETURN_LABELS = {"iade", "return"}


def q2(value: Decimal) -> Decimal:
    return value.quantize(Q2, rounding=ROUND_HALF_UP)


def get_return_transactions(order: Order) -> list[CheTransaction]:
    cached = getattr(order, "_return_che_transactions_memo", None)
    if cached is not None:
        return cached

    order_num = str(order.order_number or order.marketplace_order_id or "")
    if not order_num:
        order._return_che_transactions_memo = []
        return []

    qs = CheTransaction.objects.filter(
        account=order.marketplace_account,
        source=CheTransaction.SOURCE_SETTLEMENTS,
        order_number=order_num,
    ).filter(transaction_type_code__in=RETURN_TYPE_CODES)
    order._return_che_transactions_memo = list(qs)
    return order._return_che_transactions_memo


def get_claim_item_barcodes(order: Order) -> set[str]:
    cached = getattr(order, "_return_claim_barcodes_memo", None)
    if cached is not None:
        return cached

    order_num = str(order.order_number or order.marketplace_order_id or "")
    if not order_num:
        order._return_claim_barcodes_memo = set()
        return set()

    barcodes = set(
        ReturnClaim.objects.filter(
            organization=order.organization,
            order_number=order_num,
        ).values_list("claim_items__barcode", flat=True)
    )
    order._return_claim_barcodes_memo = {str(b) for b in barcodes if b}
    return order._return_claim_barcodes_memo


def _item_barcodes(item: OrderItem) -> set[str]:
    keys = {str(item.sku or "")}
    if item.product_variant:
        keys.add(str(item.product_variant.barcode or ""))
        keys.add(str(item.product_variant.marketplace_sku or ""))
    return {k for k in keys if k}


def get_returned_barcodes(order: Order) -> set[str]:
    barcodes = {str(tx.barcode) for tx in get_return_transactions(order) if tx.barcode}
    barcodes |= get_claim_item_barcodes(order)
    return barcodes


def is_order_item_returned(item: OrderItem) -> bool:
    order = item.order
    if order.status in RETURN_STATUSES:
        return True

    returned_barcodes = get_returned_barcodes(order)
    if not returned_barcodes:
        return False

    return bool(_item_barcodes(item) & returned_barcodes)


def order_has_return_activity(order: Order) -> bool:
    if order.status in RETURN_STATUSES:
        return True
    return bool(get_return_transactions(order) or get_claim_item_barcodes(order))


def _qty(items: Iterable[OrderItem]) -> int:
    return sum(max(int(item.quantity or 0), 0) for item in items)


def get_returned_quantity(order: Order, item: OrderItem | None = None) -> int:
    if item is not None:
        return max(int(item.quantity or 0), 1) if is_order_item_returned(item) else 0

    items = list(order.items.all())
    if order.status in RETURN_STATUSES:
        return max(_qty(items), 1)

    return max(_qty(item for item in items if is_order_item_returned(item)), 0)


def get_total_quantity(order: Order) -> int:
    return max(_qty(order.items.all()), 1)


def is_full_return(order: Order) -> bool:
    if order.status in RETURN_STATUSES:
        return True
    return get_returned_quantity(order) >= get_total_quantity(order)


def estimate_outgoing_cargo(order: Order) -> Decimal:
    carrier = _normalize_carrier(order.cargo_provider_name or "")
    return q2(_get_carrier_flat_rate(carrier))


def _invoice_total(order: Order, keywords: tuple[str, ...]) -> Decimal:
    order_num = str(order.order_number or order.marketplace_order_id or "")
    if not order_num:
        return Decimal("0.00")

    qs = CargoInvoice.objects.filter(
        organization=order.organization,
        order_number=order_num,
    )
    if keywords:
        keyword_qs = qs.none()
        for keyword in keywords:
            keyword_qs = keyword_qs | qs.filter(shipment_package_type__icontains=keyword)
        qs = keyword_qs

    total = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return q2(total)


def get_outgoing_cargo(order: Order) -> tuple[Decimal, str]:
    invoice_total = _invoice_total(order, ("Gönderi", "Gonderi"))
    if invoice_total > Decimal("0.00"):
        return invoice_total, "invoice"

    any_invoice_total = _invoice_total(order, tuple())
    if any_invoice_total > Decimal("0.00"):
        return any_invoice_total, "invoice"

    return estimate_outgoing_cargo(order), "estimated"


def get_incoming_cargo(order: Order, outgoing_cargo: Decimal) -> tuple[Decimal, str]:
    invoice_total = _invoice_total(order, ("İade", "Iade", "Geri", "Teslim"))
    if invoice_total > Decimal("0.00"):
        return invoice_total, "invoice"
    return outgoing_cargo, "estimated"


def get_return_cargo_breakdown(order: Order, item: OrderItem | None = None) -> dict:
    returned_qty = get_returned_quantity(order, item=item)
    if returned_qty <= 0:
        return {
            "outgoing_cargo": Decimal("0.00"),
            "incoming_cargo": Decimal("0.00"),
            "total_cargo_loss": Decimal("0.00"),
            "source": "none",
            "is_full_return": False,
            "returned_quantity": 0,
        }

    total_qty = get_total_quantity(order)
    ratio = Decimal(returned_qty) / Decimal(total_qty)
    full_return = is_full_return(order)

    outgoing_total, outgoing_source = get_outgoing_cargo(order)
    incoming_total, incoming_source = get_incoming_cargo(order, outgoing_total)

    outgoing_loss = outgoing_total if full_return else Decimal("0.00")
    incoming_loss = incoming_total if full_return else incoming_total * ratio

    source = "invoice" if "invoice" in {outgoing_source, incoming_source} else "estimated"
    total = q2(outgoing_loss + incoming_loss)

    return {
        "outgoing_cargo": q2(outgoing_loss),
        "incoming_cargo": q2(incoming_loss),
        "total_cargo_loss": total,
        "source": source,
        "is_full_return": full_return,
        "returned_quantity": returned_qty,
    }
