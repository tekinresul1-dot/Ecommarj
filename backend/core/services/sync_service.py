import logging
from decimal import Decimal
from datetime import datetime, timezone as dt_timezone, timedelta
from django.utils import timezone
from django.db.models import Q
from core.models import (
    Organization, MarketplaceAccount, Product, Order, OrderItem,
    FinancialTransaction, FinancialTransactionType, ProductVariant, CargoInvoice
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
            api_key=decrypt_value(account.api_key),
            api_secret=decrypt_value(account.api_secret),
            seller_id=account.seller_id
        )

    def sync_all(self):
        """Ürünleri, siparişleri ve hakedişleri senkronize eder."""
        logger.info(f"Syncing all for account {self.account}")
        self.sync_products()
        self.sync_orders()
        self.sync_seller_invoices_settlement()  # Gerçek kargo/komisyon tutarları
        self.sync_settlements()       # Fallback: eski settlement API
        self.sync_cargo_invoices()    # Fallback: cargo invoice API

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
            trendyol_content_id = str(p_data.get("productContentId", "") or "")
            currency = str(p_data.get("currencyType", "") or "TRY").upper() or "TRY"

            # Images
            image_url = ""
            images = p_data.get("images")
            if images and len(images) > 0:
                image_url = images[0].get("url", "")

            # Attributes: extract color and size
            attributes = p_data.get("attributes", []) or []
            color = ""
            size = ""
            size_attr_names = {"beden", "numara", "ebat", "boy"}
            for attr in attributes:
                attr_name = (attr.get("attributeName") or "").lower()
                attr_value = (attr.get("attributeValue") or "").strip()
                if attr_name == "renk" and not color:
                    color = attr_value
                elif attr_name in size_attr_names and not size:
                    size = attr_value

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
                    "trendyol_content_id": trendyol_content_id,
                    "currency": currency,
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
                    "color": color,
                    "size": size,
                    "stock": stock_quantity,
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

            # cargoDeci — Trendyol'un ölçtüğü gerçek desi değeri
            raw_deci = (
                o_data.get("cargoDeci") or
                o_data.get("cargoDetail", {}).get("deci") or
                o_data.get("cargoDetail", {}).get("cargoDeci") or
                o_data.get("desi") or
                o_data.get("totalDesi")
            )
            try:
                cargo_deci = Decimal(str(raw_deci)) if raw_deci is not None else None
            except Exception:
                cargo_deci = None
            
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
                    "cargo_deci": cargo_deci,
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

            # Sipariş yanıtındaki kargo tutarını kaydet (finance API'den daha güvenilir)
            # Trendyol order response: deliveryCost veya cargoAmount alanlarından birini kullan
            raw_cargo = (
                o_data.get("deliveryCost") or
                o_data.get("cargoAmount") or
                o_data.get("totalShipmentFee") or
                o_data.get("shipmentFee")
            )
            if raw_cargo:
                try:
                    cargo_amount = Decimal(str(raw_cargo))
                    if cargo_amount > Decimal("0"):
                        first_item = order.items.first()
                        if first_item:
                            FinancialTransaction.objects.update_or_create(
                                organization=self.organization,
                                order_item_ref=first_item,
                                transaction_type=FinancialTransactionType.SHIPPING_FEE,
                                defaults={
                                    "amount": cargo_amount,
                                    "occurred_at": order_date,
                                    "raw_payload": {"source": "order_response", "field": "deliveryCost", "value": str(raw_cargo)},
                                }
                            )
                except Exception as e:
                    logger.warning(f"[SyncOrders] Kargo tutarı kaydedilemedi (order {order_number}): {e}")

        logger.info(f"Orders sync complete. {len(orders_data)} orders processed.")

    # ------------------------------------------------------------------
    # SELLER INVOICE SETTLEMENTS — Per-order gerçek kargo tutarları (CHE API)
    # ------------------------------------------------------------------
    def sync_seller_invoices_settlement(self):
        """
        CHE Seller Invoice Settlement API'den sipariş bazlı gerçek kargo,
        komisyon ve hizmet bedeli tutarlarını çeker ve FinancialTransaction olarak kaydeder.
        sync_orders()'dan sonra çalıştırılır; order_response'taki kargo tutarını override eder.
        """
        logger.info("Fetching seller invoice settlements (CHE API)...")
        from datetime import timedelta
        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        try:
            records = self.adapter.fetch_seller_invoices_settlement(start_ms, end_ms)
        except Exception as e:
            logger.warning(f"SellerInvoiceSettlement fetch failed (non-critical): {e}")
            return

        if not records:
            logger.info("No seller invoice settlement data returned.")
            return

        processed = 0
        for record in records:
            # Alan adı çeşitleri: orderNumber, shipmentPackageId, packageId
            order_number = (
                record.get("orderNumber") or
                record.get("shipmentPackageId") or
                record.get("packageId")
            )
            if not order_number:
                continue

            order = Order.objects.filter(organization=self.organization).filter(
                Q(order_number=str(order_number)) | Q(marketplace_order_id=str(order_number))
            ).first()
            if not order:
                continue

            first_item = order.items.first()
            if not first_item:
                continue

            occurred_at_ts = record.get("transactionDate") or record.get("settlementDate")
            if occurred_at_ts:
                occurred_at = datetime.fromtimestamp(occurred_at_ts / 1000.0, tz=dt_timezone.utc)
            else:
                occurred_at = order.order_date or timezone.now()

            # Kargo tutarı
            cargo_raw = (
                record.get("cargoAmount") or
                record.get("shipmentFee") or
                record.get("deliveryCost") or
                record.get("totalShipmentFee")
            )
            if cargo_raw:
                try:
                    cargo_amount = abs(Decimal(str(cargo_raw)))
                    if cargo_amount > Decimal("0"):
                        FinancialTransaction.objects.update_or_create(
                            organization=self.organization,
                            order_item_ref=first_item,
                            transaction_type=FinancialTransactionType.SHIPPING_FEE,
                            defaults={
                                "amount": cargo_amount,
                                "occurred_at": occurred_at,
                                "raw_payload": record,
                            }
                        )
                        processed += 1
                except Exception as e:
                    logger.warning(f"[SellerInvoiceSettlement] Kargo TX hatası (order {order_number}): {e}")

            # Komisyon tutarı
            commission_raw = record.get("commissionAmount") or record.get("commission")
            if commission_raw:
                try:
                    comm_amount = abs(Decimal(str(commission_raw)))
                    if comm_amount > Decimal("0"):
                        FinancialTransaction.objects.update_or_create(
                            organization=self.organization,
                            order_item_ref=first_item,
                            transaction_type=FinancialTransactionType.COMMISSION,
                            defaults={
                                "amount": comm_amount,
                                "occurred_at": occurred_at,
                                "raw_payload": record,
                            }
                        )
                except Exception:
                    pass

            # Hizmet bedeli
            service_raw = record.get("serviceFee") or record.get("trendyolCut") or record.get("platformFee")
            if service_raw:
                try:
                    svc_amount = abs(Decimal(str(service_raw)))
                    if svc_amount > Decimal("0"):
                        FinancialTransaction.objects.update_or_create(
                            organization=self.organization,
                            order_item_ref=first_item,
                            transaction_type=FinancialTransactionType.SERVICE_FEE,
                            defaults={
                                "amount": svc_amount,
                                "occurred_at": occurred_at,
                                "raw_payload": record,
                            }
                        )
                except Exception:
                    pass

        logger.info(f"SellerInvoiceSettlement sync complete. {processed} cargo records processed from {len(records)} records.")

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
    def _extract_cargo_invoice_ids(self, records: list) -> set:
        """Verilen kayıt listesinden Kargo Faturası invoice ID'lerini çıkar."""
        CARGO_TYPES = {
            "DeductionInvoices", "Kargo Faturası", "Kargo Fatura",
            "kargo faturası", "kargo fatura", "DEDUCTION_INVOICES",
        }
        ids = set()
        for rec in records:
            tx_type = rec.get("transactionType", "")
            # Kargo Faturası tipi veya içinde "kargo" geçen tipler
            if tx_type in CARGO_TYPES or "kargo" in tx_type.lower():
                inv_id = (rec.get("id") or rec.get("invoiceSerialNumber")
                          or rec.get("invoiceId") or rec.get("serialNumber"))
                if inv_id:
                    ids.add(str(inv_id))
        return ids

    def sync_cargo_invoices(self):
        """
        Kargo Faturası invoice ID'lerini birden fazla kaynaktan toplar:
        1. OtherFinancials (CHE) API — ana kaynak
        2. Settlements API — fallback
        Ardından Cargo Invoice Items API ile sipariş bazlı gerçek tutarları kaydeder.
        """
        logger.info("Fetching cargo invoices...")
        end_date   = timezone.now()
        start_date = end_date - timedelta(days=30)
        start_ms   = int(start_date.timestamp() * 1000)
        end_ms     = int(end_date.timestamp() * 1000)

        invoice_ids = set()

        # ── Kaynak 1: OtherFinancials (CHE) ──
        try:
            of_data = self.adapter.fetch_other_financials(start_ms, end_ms)
            if of_data:
                ids = self._extract_cargo_invoice_ids(of_data)
                logger.info(f"OtherFinancials: {len(of_data)} records, {len(ids)} cargo invoice IDs")
                invoice_ids |= ids
        except Exception as e:
            logger.warning(f"OtherFinancials fetch error (non-critical): {e}")

        # ── Kaynak 2: Settlements API (fallback) ──
        if not invoice_ids:
            try:
                settle_data = self.adapter.fetch_financials(start_ms, end_ms)
                if settle_data:
                    ids = self._extract_cargo_invoice_ids(settle_data)
                    logger.info(f"Settlements: {len(settle_data)} records, {len(ids)} cargo invoice IDs")
                    invoice_ids |= ids
            except Exception as e:
                logger.warning(f"Settlements fetch error (non-critical): {e}")

        if not invoice_ids:
            logger.info("No cargo invoice IDs found from any source.")
            return

        processed_count = 0
        for inv_id in invoice_ids:
            try:
                cargo_items = self.adapter.fetch_cargo_invoice_items(inv_id)
                if not cargo_items:
                    continue
                
                for item in cargo_items:
                    order_number = (item.get("orderNumber") or item.get("order_number")
                                    or item.get("orderNo") or item.get("orderId"))
                    if not order_number:
                        continue

                    cargo_amount = Decimal(str(item.get("amount", "0")))
                    if cargo_amount <= 0:
                        continue

                    pkg_type = (item.get("shipmentPackageType") or item.get("shipmentType")
                                or item.get("packageType") or "")

                    # Her zaman CargoInvoice'a kaydet (order DB'de olmasa bile)
                    CargoInvoice.objects.update_or_create(
                        organization=self.organization,
                        order_number=str(order_number),
                        invoice_serial_number=str(inv_id),
                        defaults={
                            "amount": cargo_amount,
                            "desi": item.get("desi"),
                            "shipment_package_type": pkg_type,
                            "raw_payload": item,
                        }
                    )

                    # FinancialTransaction'a da kaydet (order bulunabilirse)
                    order = Order.objects.filter(
                        organization=self.organization
                    ).filter(
                        Q(order_number=str(order_number)) | Q(marketplace_order_id=str(order_number))
                    ).first()

                    if order:
                        first_item = order.items.first()
                        if first_item:
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
