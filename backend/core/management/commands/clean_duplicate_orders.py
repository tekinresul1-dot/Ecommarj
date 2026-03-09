"""
Management command to clean duplicate orders and prepare DB for re-sync.
"""
import logging
from collections import defaultdict

from django.core.management.base import BaseCommand
from core.models import Order, OrderItem

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean duplicate orders (same org + package_id) keeping only the latest one"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be deleted, don't actually delete",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        
        # Group orders by (org_id, package_id)
        all_orders = Order.objects.all().order_by("id")
        groups = defaultdict(list)
        for o in all_orders:
            key = (o.organization_id, o.package_id)
            groups[key].append(o)

        total_dups = 0
        dup_ids_to_delete = []
        
        for key, orders in groups.items():
            if len(orders) > 1:
                total_dups += len(orders) - 1
                # Keep the one with highest ID (newest), delete older ones
                orders_sorted = sorted(orders, key=lambda x: x.id)
                for dup in orders_sorted[:-1]:
                    dup_ids_to_delete.append(dup.id)
                    if dry_run:
                        self.stdout.write(
                            f"  WOULD DELETE: Order ID={dup.id} "
                            f"oid={dup.marketplace_order_id} pkg={dup.package_id}"
                        )

        self.stdout.write(f"\nTotal orders: {all_orders.count()}")
        self.stdout.write(f"Unique (org, package_id) groups: {len(groups)}")
        self.stdout.write(f"Duplicate orders found: {total_dups}")

        if not dup_ids_to_delete:
            self.stdout.write(self.style.SUCCESS("No duplicates found!"))
            return

        if dry_run:
            items_count = OrderItem.objects.filter(order_id__in=dup_ids_to_delete).count()
            self.stdout.write(f"Would delete {total_dups} orders + {items_count} items")
            self.stdout.write(self.style.WARNING("DRY RUN — no changes made"))
            return

        # Actually delete
        items_deleted = OrderItem.objects.filter(order_id__in=dup_ids_to_delete).delete()
        orders_deleted = Order.objects.filter(id__in=dup_ids_to_delete).delete()
        
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {total_dups} duplicate orders and their items. "
            f"Remaining: {Order.objects.count()} orders"
        ))
