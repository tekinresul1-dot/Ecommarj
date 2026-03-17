import logging
from decimal import Decimal
from datetime import datetime, timezone as dt_timezone, timedelta
from django.utils import timezone
from django.db.models import Q
from core.models import (
    Organization, MarketplaceAccount, Product, Order, OrderItem,
    FinancialTransaction, FinancialTransactionType, ProductVariant
)
from core.services.trendyol_adapter import TrendyolAdapter
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# Trendyol status -> EcomMarj status mapping
STATUS_MAP = {
    "Created": Order.Status.CREATED,
    "Picking": Order.Status.PICKING,
    "Shipped": Order.Status.SHIPPED,
    "Delivered": Order.Status.DELIVERED,
    "Cancelled": Order.Status.CANCELLED,
    "Returned": Order.Status.RETURNED,
    "UnSupplied": Order.Status.CANCELLED,
}


class TrendyolSyncService:
    """
    TrendyolAdapter kullanarak API'den çekilen verileri 
    EcomMarj veritabanı tablolarına dönüştürür ve kaydeder.
    """
    def __init__(self, account: MarketplaceAccount):
        self.account = account
        self.organization = account.organization
        self.adapter = TrendyolAdapter(
            api_key=account.api_key,
            api_secret=decrypt_value(account.api_secret),
            seller_id=account.seller_id
        )

    def sync_all(self):
        """Ürünleri, siparişleri ve hakedişleri senkronize eder."""
        logger.info(f"Syncing all for account {self.account}")
        self.sync_products()
        self.sync_orders()
        self.sync_settlements()
        self.sync_cargo_invoices()
        
        self.account.last_sync_at = timezone.now()
        self.account.save()
        logger.info("Sync completed.")

    # ------------------------------------------------------------------
    # PRODUCTS
    # ------------------------------------------------------------------
    def sync_products(self):
        logger.info("Fetching products...")
        products_data = self.adapter.fetch_products()
        for p_data in products_data:
            barcode = p_data.get("barcode")
            if not barcode:
                continue

            # Sadece kilitli veya kara listedeki ürünleri filtrele; reddedilen ve satışa kapalı ürünler de çekilsin
            is_locked = p_data.get("locked", False)
            is_blacklisted = p_data.get("blacklisted", False)
            stock_quantity = int(p_data.get("quantity", 0))

            if is_locked or is_blacklisted:
                continue
                
            vat_rate = Decimal(str(p_data.get("vatRate", "0")))
            sale_price = Decimal(str(p_data.get("salePrice", "0")))
            brand = p_data.get("brand", "")
            category_name = p_data.get("categoryName", "")
            product_main_id = p_data.get("productMainId", "")
            
            # Images
            image_url = ""
            images = p_data.get("images")
            if images and len(images) > 0:
                image_url = images[0].get("url", "")
            
            product, created = Product.objects.update_or_create(
                organization=self.organization,
                marketplace_account=self.account,
                barcode=barcode,
                defaults={
                    "title": p_data.get("title", "")[:500],
                    "category_name": category_name,
                    "image_url": image_url,
                    "sale_price": sale_price,
                    "vat_rate": vat_rate,
                    "marketplace_sku": product_main_id,
                    "current_stock": stock_quantity,
                    "brand": brand,
                }
            )
            
            if created:
                product.initial_stock = stock_quantity
                product.save(update_fields=["initial_stock"])
                
            create_ts = p_data.get("createDateTime")
            if create_ts:
                try:
                    dt = datetime.fromtimestamp(create_ts / 1000.0, tz=dt_timezone.utc)
                    Product.objects.filter(pk=product.pk).update(trendyol_created_at=dt)
                except Exception:
                    pass
            
            stock_code = p_data.get("stockCode") or p_data.get("productCode") or ""
            
            # Auto-create a default ProductVariant for easy order matching
            ProductVariant.objects.update_or_create(
                product=product,
                barcode=barcode,
                defaults={
                    "marketplace_sku": str(stock_code).strip(),
                    "title": p_data.get("title", "")[:500],
                }
            )
        
        logger.info(f"Products sync complete. {len(products_data)} items processed.")

    # ------------------------------------------------------------------
    # ORDERS — Tüm durumlar çekilir (kayan pencereli çekim)
    # ------------------------------------------------------------------
    def sync_orders(self):
        """
        Trendyol API farklı tarih aralıkları için farklı sipariş alt kümeleri döner.
        Tek bir geniş aralık veya aylık parçalar bazı siparişleri kaçırır.
        Çözüm: 15 günlük kayan pencereler + 7 gün adım ile tüm geçmişi kapla.
        Dedup shipmentPackageId ile. unique_together constraint DB'de garantiler.
        """
        logger.info("Fetching orders (sliding window, 365 days)...")
        
        now = datetime.now(dt_timezone.utc)
        total_days = 365  # 1 yıl geriye git — tüm geçmiş
        window_size = 15  # gün
        step_size = 7     # gün (8 gün çakışma)
        
        all_orders_data = []
        
        day = 0
        while day < total_days:
            window_start = now - timedelta(days=total_days - day)
            window_end = now - timedelta(days=max(0, total_days - day - window_size))
            
            start_ms = int(window_start.timestamp() * 1000)
            end_ms = int(window_end.timestamp() * 1000)
            
            chunk_orders = self.adapter.fetch_orders(
                start_date_ms=start_ms,
                end_date_ms=end_ms
            )
            all_orders_data.extend(chunk_orders)
            
            day += step_size
        
        # Tekrarlananları shipmentPackageId ile filtrele
        seen_packages = set()
        orders_data = []
        for o_data in all_orders_data:
            pkg_id = str(o_data.get("shipmentPackageId") or o_data.get("id") or "")
            if pkg_id and pkg_id not in seen_packages:
                seen_packages.add(pkg_id)
                orders_data.append(o_data)
        
        logger.info(f"Total unique orders to process: {len(orders_data)}")
        
        for o_data in orders_data:
            order_number = o_data.get("orderNumber")
            # Trendyol her paketi ayrı bir kayıt olarak döner.
            # shipmentPackageId her paket için benzersizdir — aynı orderNumber birden fazla pakete sahip olabilir.
            shipment_package_id = str(o_data.get("shipmentPackageId") or o_data.get("id") or order_number)
            if not order_number:
                continue

            order_date_ts = o_data.get("orderDate", 0)
            order_date = datetime.fromtimestamp(order_date_ts / 1000.0, tz=dt_timezone.utc)
            
            # Status mapping
            raw_status = o_data.get("status", "Created")
            mapped_status = STATUS_MAP.get(raw_status, Order.Status.CREATED)
            
            # micro export flag
            is_micro = o_data.get("micro", False)
            
            # Cargo details
            cargo_provider = o_data.get("cargoProviderName", "")
            cargo_tracking = o_data.get("cargoTrackingNumber", "")
            cargo_detail = o_data.get("cargoDetail") or {}
            if cargo_detail:
                if cargo_detail.get("cargoProviderName"):
                    cargo_provider = cargo_detail.get("cargoProviderName")
                if cargo_detail.get("trackingNumber"):
                    cargo_tracking = cargo_detail.get("trackingNumber")
            
            # Country code
            country_code = "TR"
            ship_addr = o_data.get("shipmentAddress") or {}
            if ship_addr.get("countryCode"):
                country_code = ship_addr["countryCode"]
            elif is_micro:
                country_code = ship_addr.get("countryCode", "XX")
            
            order, _ = Order.objects.update_or_create(
                organization=self.organization,
                package_id=shipment_package_id,            # Match unique_together exactly
                defaults={
                    "marketplace_account": self.account,
                    "marketplace_order_id": shipment_package_id, # Moved from lookup to defaults
                    "order_number": order_number,
                    "order_date": order_date,
                    "status": mapped_status,
                    "channel": Order.Channel.MICRO_EXPORT if is_micro else Order.Channel.TRENDYOL,
                    "country_code": country_code,
                    "cargo_provider_name": cargo_provider,
                    "cargo_tracking_number": cargo_tracking,
                }
            )

            # Sipariş satırları
            for line in o_data.get("lines", []):
                barcode = line.get("barcode", "")
                line_id = str(line.get("id", ""))
                
                # Find matching variant by barcode
                variant = None
                if barcode:
                    variant = ProductVariant.objects.filter(
                        product__organization=self.organization,
                        barcode=barcode
                    ).select_related("product").first()
                
                price = Decimal(str(line.get("amount", line.get("price", "0"))))
                discount = Decimal(str(line.get("discount", "0")))
                quantity = int(line.get("quantity", 1))
                commission_rate_raw = line.get("commission")  # Trendyol API: 'commission' alanı (oran %)
                vat_rate_raw = line.get("vatRate")
                
                item_status = line.get("orderLineItemStatusName", raw_status)
                
                item_defaults = {
                    "product_variant": variant,
                    "sku": line.get("merchantSku", barcode),
                    "quantity": quantity,
                    "sale_price_gross": price,
                    "sale_price_net": price - discount,
                    "discount": discount,
                    "status": item_status,
                }
                if commission_rate_raw is not None:
                    item_defaults["applied_commission_rate"] = Decimal(str(commission_rate_raw))
                if vat_rate_raw is not None:
                    item_defaults["applied_vat_rate"] = Decimal(str(vat_rate_raw))

                order_item, item_created = OrderItem.objects.update_or_create(
                    order=order,
                    marketplace_line_id=line_id,
                    defaults=item_defaults,
                )
                
                # Eğer variant varsa Product'ın commission_rate'ini güncelle (fallback verisi)
                if variant and variant.product:
                    if commission_rate_raw is not None:
                        variant.product.commission_rate = Decimal(str(commission_rate_raw))
                        variant.product.save(update_fields=["commission_rate"])

        logger.info(f"Orders sync complete. {len(orders_data)} orders processed.")

    # ------------------------------------------------------------------
    # SETTLEMENTS — Gerçek finansal veriler (komisyon, kargo, hizmet bedeli)
    # ------------------------------------------------------------------
    def sync_settlements(self):
        """
        Trendyol Settlements API'den hakediş/finansal verileri çeker.
        Her settlement satırı bir FinancialTransaction'a dönüştürülür.
        """
        logger.info("Fetching settlements...")
        try:
            settlements_data = self.adapter.fetch_financials()
        except Exception as e:
            logger.warning(f"Settlements fetch failed (non-critical): {e}")
            return
        
        if not settlements_data:
            logger.info("No settlements data returned.")
            return
        
        for s_data in settlements_data:
            # Typical settlement item has: orderNumber, transactionType, amount, commissionAmount, etc.
            order_number = s_data.get("orderNumber") or s_data.get("shipmentPackageId")
            if not order_number:
                continue
            
            # Find matching order
            order = Order.objects.filter(
                organization=self.organization
            ).filter(
                Q(order_number=str(order_number)) | Q(marketplace_order_id=str(order_number))
            ).first()
            
            if not order:
                continue
            
            occurred_at_ts = s_data.get("transactionDate", 0)
            if occurred_at_ts:
                occurred_at = datetime.fromtimestamp(occurred_at_ts / 1000.0, tz=dt_timezone.utc)
            else:
                occurred_at = order.order_date or timezone.now()
            
            # Find the first order_item for this order to link transactions
            first_item = order.items.first()
            if not first_item:
                continue
            
            # Commission
            commission_amount = s_data.get("commissionAmount") or s_data.get("commission")
            if commission_amount:
                FinancialTransaction.objects.update_or_create(
                    organization=self.organization,
                    order_item_ref=first_item,
                    transaction_type=FinancialTransactionType.COMMISSION,
                    defaults={
                        "amount": abs(Decimal(str(commission_amount))),
                        "occurred_at": occurred_at,
                        "raw_payload": s_data,
                    }
                )
            
            # Cargo / Shipping Fee
            cargo_amount = s_data.get("cargoAmount") or s_data.get("shipmentFee")
            if cargo_amount:
                FinancialTransaction.objects.update_or_create(
                    organization=self.organization,
                    order_item_ref=first_item,
                    transaction_type=FinancialTransactionType.SHIPPING_FEE,
                    defaults={
                        "amount": abs(Decimal(str(cargo_amount))),
                        "occurred_at": occurred_at,
                        "raw_payload": s_data,
                    }
                )
            
            # Service Fee
            service_fee = s_data.get("serviceFee") or s_data.get("trendyolCut")
            if service_fee:
                FinancialTransaction.objects.update_or_create(
                    organization=self.organization,
                    order_item_ref=first_item,
                    transaction_type=FinancialTransactionType.SERVICE_FEE,
                    defaults={
                        "amount": abs(Decimal(str(service_fee))),
                        "occurred_at": occurred_at,
                        "raw_payload": s_data,
                    }
                )
        
        logger.info(f"Settlements sync complete. {len(settlements_data)} items processed.")

    # ------------------------------------------------------------------
    # CARGO INVOICES — Detaylı kargo kesinti faturaları
    # ------------------------------------------------------------------
    def sync_cargo_invoices(self):
        """
        OtherFinancials API üzerinden DeductionInvoices çekilir, 
        daha sonra Cargo Invoice API üzerinden sipariş bazlı kargo kesintileri işlenir.
        """
        logger.info("Fetching cargo invoices...")
        try:
            # Sadece son 30 günü çek, Trendyol OtherFinancials 30 günden eskisini kilitler
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            start_ms = int(start_date.timestamp() * 1000)
            end_ms = int(end_date.timestamp() * 1000)
            
            financials_data = self.adapter.fetch_other_financials(start_ms, end_ms)
        except Exception as e:
            logger.warning(f"Cargo Invoices fetch failed (non-critical): {e}")
            return

        if not financials_data:
            logger.info("No OtherFinancials data returned.")
            return

        invoice_ids = set()
        for f_data in financials_data:
            # Kargo Faturası kesintilerini filtrele
            if f_data.get("transactionType") in ["DeductionInvoices", "Kargo Faturası", "Kargo Fatura"]:
                invoice_id = f_data.get("id") or f_data.get("invoiceSerialNumber") or f_data.get("invoiceId")
                if invoice_id:
                    invoice_ids.add(str(invoice_id))

        if not invoice_ids:
            logger.info("No cargo invoices found in the recent period.")
            return

        processed_count = 0
        for inv_id in invoice_ids:
            try:
                cargo_items = self.adapter.fetch_cargo_invoice_items(inv_id)
                if not cargo_items:
                    continue
                
                for item in cargo_items:
                    order_number = item.get("orderNumber")
                    if not order_number:
                        continue

                    order = Order.objects.filter(
                        organization=self.organization
                    ).filter(
                        Q(order_number=str(order_number)) | Q(marketplace_order_id=str(order_number))
                    ).first()

                    if not order:
                        # logger.debug(f"Order {order_number} not found, skipping cargo item.")
                        continue

                    cargo_amount = Decimal(str(item.get("amount", "0")))
                    if cargo_amount > 0:
                        first_item = order.items.first()
                        if first_item:
                            # Use invoice date if available, else order date
                            invoice_date_str = item.get("invoiceDate")
                            if invoice_date_str:
                                try:
                                    occurred_at = timezone.make_aware(datetime.fromisoformat(invoice_date_str.replace("Z", "+00:00")))
                                except Exception:
                                    occurred_at = order.order_date or timezone.now()
                            else:
                                occurred_at = order.order_date or timezone.now()

                            FinancialTransaction.objects.update_or_create(
                                organization=self.organization,
                                order_item_ref=first_item,
                                transaction_type=FinancialTransactionType.SHIPPING_FEE,
                                defaults={
                                    "amount": cargo_amount,
                                    "occurred_at": occurred_at,
                                    "raw_payload": item,
                                }
                            )
                            processed_count += 1
            except Exception as e:
                logger.warning(f"Failed to process cargo invoice {inv_id}: {e}")

        logger.info(f"Cargo Invoices sync complete. Processed {processed_count} items from {len(invoice_ids)} invoices.")
