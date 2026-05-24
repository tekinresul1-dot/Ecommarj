import json
from collections import Counter, defaultdict
from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from core.models import MarketplaceAccount, Order, OrderItem
from core.views import (
    CANCEL_STATUSES,
    DASHBOARD_REVENUE_STATUSES,
    GROSS_SALES_STATUSES,
    RETURN_STATUSES,
)


ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")
Q2 = Decimal("0.01")


def q2(value):
    return (value or Decimal("0")).quantize(Q2, ROUND_HALF_UP)


def money(value):
    return str(q2(value))


def parse_local_date(value, *, is_end=False):
    date_value = datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.combine(date_value, time.max if is_end else time.min, tzinfo=ISTANBUL_TZ)


def effective_status(item):
    return item.status or item.order.status or ""


def status_bucket(status):
    if status in DASHBOARD_REVENUE_STATUSES:
        return "net"
    if status in CANCEL_STATUSES:
        return "cancelled"
    if status in RETURN_STATUSES:
        return "returned"
    if status in GROSS_SALES_STATUSES:
        return "gross_only"
    return "excluded"


class Command(BaseCommand):
    help = "Debug Trendyol revenue reconciliation for one seller/date range"

    def add_arguments(self, parser):
        parser.add_argument("--seller-email", required=True)
        parser.add_argument("--start", required=True, help="YYYY-MM-DD")
        parser.add_argument("--end", required=True, help="YYYY-MM-DD")
        parser.add_argument("--pretty", action="store_true")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["seller_email"]
        user = User.objects.filter(email=email).first() or User.objects.filter(username=email).first()
        if not user or not hasattr(user, "profile") or not user.profile.organization:
            raise CommandError(f"Kullanıcı/organizasyon bulunamadı: {email}")

        org = user.profile.organization
        account = MarketplaceAccount.objects.filter(organization=org, is_active=True).first()
        if not account:
            raise CommandError("Aktif Trendyol hesabı bulunamadı")

        start_local = parse_local_date(options["start"], is_end=False)
        end_local = parse_local_date(options["end"], is_end=True)

        orders_qs = Order.objects.filter(
            organization=org,
            marketplace_account=account,
            order_date__gte=start_local,
            order_date__lte=end_local,
        )
        items = list(
            OrderItem.objects.filter(order__in=orders_qs)
            .select_related("order", "product_variant")
            .order_by("order__order_date", "order__package_id", "marketplace_line_id")
        )

        status_rows = defaultdict(lambda: {
            "item_count": 0,
            "quantity": 0,
            "gross_total": Decimal("0"),
            "discount_total": Decimal("0"),
            "net_total": Decimal("0"),
        })
        bucket_counts = Counter()
        bucket_qty = Counter()
        created_by_rows = defaultdict(lambda: {"packages": 0, "gross_total": Decimal("0"), "discount_total": Decimal("0")})

        gross_total = Decimal("0")
        cancelled_total = Decimal("0")
        returned_total = Decimal("0")
        discount_total = Decimal("0")
        costed_net_total = Decimal("0")
        missing_cost_total = Decimal("0")
        excluded_total = Decimal("0")

        for item in items:
            status = effective_status(item)
            bucket = status_bucket(status)
            qty = item.quantity or 0
            row = status_rows[status]
            row["item_count"] += 1
            row["quantity"] += qty
            row["gross_total"] += item.sale_price_gross
            row["discount_total"] += item.discount
            row["net_total"] += item.sale_price_net
            bucket_counts[bucket] += 1
            bucket_qty[bucket] += qty

            if bucket != "excluded":
                gross_total += item.sale_price_gross
                discount_total += item.discount
            else:
                excluded_total += item.sale_price_net

            if bucket == "cancelled":
                cancelled_total += item.sale_price_net
            elif bucket == "returned":
                returned_total += item.sale_price_net
            elif bucket == "net":
                if item.product_variant and item.product_variant.cost_price and item.product_variant.cost_price > 0:
                    costed_net_total += item.sale_price_net
                else:
                    missing_cost_total += item.sale_price_net

        for order in orders_qs:
            created_by = order.created_by or "(empty)"
            created_by_rows[created_by]["packages"] += 1
            created_by_rows[created_by]["gross_total"] += order.package_gross_amount or Decimal("0")
            created_by_rows[created_by]["discount_total"] += order.package_total_discount or Decimal("0")

        order_numbers = [o.order_number for o in orders_qs if o.order_number]
        package_ids = [o.package_id for o in orders_qs if o.package_id]
        line_keys = [
            f"{item.order.package_id}:{item.marketplace_line_id}"
            for item in items
            if item.marketplace_line_id
        ]

        package_discount_total = sum((o.package_total_discount or Decimal("0")) for o in orders_qs)
        seller_discount_total = sum((o.package_seller_discount or Decimal("0")) for o in orders_qs)
        ty_discount_total = sum((o.package_ty_discount or Decimal("0")) for o in orders_qs)
        final_discount_used = package_discount_total if package_discount_total > Decimal("0") else discount_total
        final_discount_source = "package_total_discount" if package_discount_total > Decimal("0") else "line_discount_total"
        net_sales_total = gross_total - cancelled_total - returned_total - final_discount_used
        duplicate_order_numbers = sum(1 for _, count in Counter(order_numbers).items() if count > 1)
        duplicate_package_ids = sum(1 for _, count in Counter(package_ids).items() if count > 1)
        duplicate_line_ids = sum(1 for _, count in Counter(line_keys).items() if count > 1)

        response = {
            "seller_email": email,
            "seller_id": str(account.seller_id),
            "supplier_id": str(account.seller_id),
            "date_start_local": start_local.isoformat(),
            "date_end_local": end_local.isoformat(),
            "date_start_ms_gmt3": int(start_local.timestamp() * 1000),
            "date_end_ms_gmt3": int(end_local.timestamp() * 1000),
            "packages_count": orders_qs.count(),
            "lines_count": len(items),
            "gross_items_count": bucket_counts["net"] + bucket_counts["cancelled"] + bucket_counts["returned"],
            "cancelled_items_count": bucket_counts["cancelled"],
            "returned_items_count": bucket_counts["returned"],
            "net_items_count": bucket_counts["net"],
            "gross_quantity": bucket_qty["net"] + bucket_qty["cancelled"] + bucket_qty["returned"],
            "cancelled_quantity": bucket_qty["cancelled"],
            "returned_quantity": bucket_qty["returned"],
            "net_quantity": bucket_qty["net"],
            "included_package_count": orders_qs.filter(status__in=GROSS_SALES_STATUSES).count(),
            "total_pages_fetched": None,
            "failed_pages": None,
            "status_breakdown": {
                status: {
                    "item_count": row["item_count"],
                    "quantity": row["quantity"],
                    "gross_total": money(row["gross_total"]),
                    "discount_total": money(row["discount_total"]),
                    "net_total": money(row["net_total"]),
                }
                for status, row in sorted(status_rows.items())
            },
            "createdBy_breakdown": {
                key: {
                    "packages": row["packages"],
                    "package_gross_total": money(row["gross_total"]),
                    "package_discount_total": money(row["discount_total"]),
                }
                for key, row in sorted(created_by_rows.items())
            },
            "gross_sales_total": money(gross_total),
            "cancelled_total": money(cancelled_total),
            "returned_total": money(returned_total),
            "seller_discount_total": money(seller_discount_total),
            "ty_discount_total": money(ty_discount_total),
            "package_total_discount": money(package_discount_total),
            "line_discount_total": money(discount_total),
            "final_discount_used": money(final_discount_used),
            "final_discount_source": final_discount_source,
            "net_sales_total": money(net_sales_total),
            "costed_net_sales_total": money(costed_net_total),
            "missing_cost_sales_total": money(missing_cost_total),
            "duplicate_order_numbers_count": duplicate_order_numbers,
            "duplicate_package_ids_count": duplicate_package_ids,
            "duplicate_line_ids_count": duplicate_line_ids,
            "excluded_by_status_total": money(excluded_total),
            "excluded_by_date_total": None,
            "excluded_by_missing_cost_total": money(missing_cost_total),
            "computed_total_revenue": money(net_sales_total),
            "displayed_dashboard_total_revenue": money(net_sales_total),
            "references": {
                "trendyol_april_2026": {
                    "gross": "483000.00",
                    "cancelled": "10565.00",
                    "returned": "17985.00",
                    "discount": "30613.00",
                    "net": "423838.00",
                },
                "melontik_april_2026_total_revenue": "422295.73",
            },
        }

        self.stdout.write(json.dumps(response, ensure_ascii=False, indent=2 if options["pretty"] else None))
