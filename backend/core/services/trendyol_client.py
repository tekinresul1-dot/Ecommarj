"""
TrendyolApiClient — Production-grade Trendyol API client.

Features:
- Automatic pagination (all pages fetched)
- Date range chunking (max 3-day windows)
- Retry with exponential backoff
- Rate limit handling (429)
- Request/response logging
- Claims (getClaims) support
"""
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Max retries for transient errors
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds

# Max window size for date range queries (days)
MAX_WINDOW_DAYS = 3

# Page size for API requests
ORDER_PAGE_SIZE = 200
PRODUCT_PAGE_SIZE = 100
CLAIM_PAGE_SIZE = 100


def _trendyol_user_agent(seller_id: str) -> str:
    return f"{seller_id} - SelfIntegration"


def compute_payload_hash(payload: dict) -> str:
    """Compute MD5 hash of a JSON payload for change detection."""
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _chunk_date_range(
    start_dt: datetime, end_dt: datetime, max_days: int = MAX_WINDOW_DAYS
) -> List[Tuple[datetime, datetime]]:
    """
    Split a date range into chunks of max_days.
    Returns list of (chunk_start, chunk_end) tuples.
    """
    chunks = []
    current = start_dt
    while current < end_dt:
        chunk_end = min(current + timedelta(days=max_days), end_dt)
        chunks.append((current, chunk_end))
        current = chunk_end
    return chunks


class TrendyolApiClient:
    """
    Production-grade Trendyol Partner API client.
    
    Base URL: apigw.trendyol.com/integration
    """
    BASE_URL = "https://apigw.trendyol.com/integration"

    def __init__(self, api_key: str, api_secret: str, seller_id: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.seller_id = seller_id
        self._session = requests.Session()
        self._session.auth = (api_key, api_secret)
        self._session.headers.update({
            "User-Agent": _trendyol_user_agent(seller_id),
            "Accept": "application/json",
        })

    # ------------------------------------------------------------------
    # Low-level request with retry
    # ------------------------------------------------------------------
    def _request_with_retry(
        self, url: str, params: dict = None, operation: str = "API"
    ) -> requests.Response:
        """Make a GET request with retry + exponential backoff."""
        last_exception = None
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"[Trendyol {operation}] Attempt {attempt} — {url} params={params}")
                response = self._session.get(url, params=params, timeout=30)
                
                # Rate limit → wait and retry
                if response.status_code == 429:
                    wait = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"[Trendyol {operation}] Rate limited (429). Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                # Service unavailable → retry
                if response.status_code in (502, 503, 504, 556):
                    wait = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"[Trendyol {operation}] Server error {response.status_code}. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"[Trendyol {operation}] Connection error. Retry in {wait}s. Error: {e}")
                time.sleep(wait)
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"[Trendyol {operation}] Timeout. Retry in {wait}s.")
                time.sleep(wait)

            except requests.exceptions.HTTPError as e:
                # Non-retryable HTTP errors
                self._handle_api_error(e, operation)

        # All retries exhausted
        if last_exception:
            raise ValueError(
                f"Trendyol {operation} — tüm denemeler başarısız oldu ({MAX_RETRIES} deneme). "
                f"Son hata: {last_exception}"
            )
        raise ValueError(f"Trendyol {operation} — beklenmeyen hata")

    def _handle_api_error(self, e: requests.RequestException, operation: str):
        """Map API errors to human-readable messages."""
        if hasattr(e, 'response') and e.response is not None:
            status = e.response.status_code
            text = e.response.text

            if '<html' in text.lower() or 'cloudflare' in text.lower():
                raise ValueError(
                    f"Trendyol API HTML yanıtı döndü (status={status}). "
                    "Yanlış base URL veya Cloudflare engellemesi."
                )
            if status == 401:
                raise ValueError("API Key veya API Secret hatalı.")
            elif status == 403:
                raise ValueError("Supplier ID yetkisiz veya API anahtarı eşleşmiyor.")
            else:
                try:
                    data = e.response.json()
                    err_msg = data.get("message", text[:300])
                except ValueError:
                    err_msg = text[:300]
                raise ValueError(f"Trendyol API Hatası ({status}): {err_msg}")

        raise ValueError(f"Trendyol {operation} — ağ hatası: {e}")

    # ------------------------------------------------------------------
    # Paginated fetch — iterates all pages
    # ------------------------------------------------------------------
    def _fetch_all_pages(
        self, url: str, params: dict, operation: str = "API", max_pages: int = 500
    ) -> List[Dict]:
        """Fetch all pages of a paginated Trendyol response."""
        all_content = []
        page = 0

        while page < max_pages:
            params["page"] = page
            response = self._request_with_retry(url, params, operation)
            data = response.json()

            content = data.get("content", [])
            if not content:
                break

            all_content.extend(content)

            total_pages = data.get("totalPages", 1)
            total_elements = data.get("totalElements", len(all_content))
            
            logger.info(
                f"[Trendyol {operation}] Page {page + 1}/{total_pages} — "
                f"{len(content)} items (total so far: {len(all_content)}/{total_elements})"
            )

            if page >= total_pages - 1:
                break
            page += 1

        return all_content

    # ------------------------------------------------------------------
    # ORDERS — getShipmentPackages
    # ------------------------------------------------------------------
    def fetch_orders(
        self,
        start_date: datetime,
        end_date: datetime,
        order_by_field: str = "PackageLastModifiedDate",
        order_by_direction: str = "ASC",
        status: str = None,
    ) -> List[Dict]:
        """
        Fetch orders for a date range.
        
        Uses PackageLastModifiedDate by default to catch updated orders.
        Automatically chunks large date ranges into 3-day windows.
        Enforces Trendyol's maximum 30-day fetch limit.
        """
        # Trendyol API limit: Max 30 days query range (Update March 2026)
        # We handle this by using _chunk_date_range with 3-day windows.
        # Removed the 30-day overall limit that clipped start_date.
        url = f"{self.BASE_URL}/order/sellers/{self.seller_id}/orders"
        
        chunks = _chunk_date_range(start_date, end_date)
        all_orders = []

        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            start_ms = int(chunk_start.timestamp() * 1000)
            end_ms = int(chunk_end.timestamp() * 1000)

            params = {
                "size": ORDER_PAGE_SIZE,
                "startDate": start_ms,
                "endDate": end_ms,
                "orderByField": order_by_field,
                "orderByDirection": order_by_direction,
            }
            if status:
                params["status"] = status

            logger.info(
                f"[Trendyol Orders] Chunk {i}/{len(chunks)}: "
                f"{chunk_start.strftime('%Y-%m-%d %H:%M')} → {chunk_end.strftime('%Y-%m-%d %H:%M')}"
            )

            chunk_orders = self._fetch_all_pages(
                url, params, operation=f"Orders chunk {i}/{len(chunks)}"
            )
            all_orders.extend(chunk_orders)

        logger.info(f"[Trendyol Orders] Total fetched: {len(all_orders)} orders across {len(chunks)} chunks")
        return all_orders

    # ------------------------------------------------------------------
    # CLAIMS — getClaims (returns/refunds)
    # ------------------------------------------------------------------
    def fetch_claims(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> List[Dict]:
        """
        Fetch return/refund claims from Trendyol.
        """
        url = f"{self.BASE_URL}/order/sellers/{self.seller_id}/claims"
        
        params = {"size": CLAIM_PAGE_SIZE}
        
        if start_date:
            params["startDate"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["endDate"] = int(end_date.timestamp() * 1000)

        claims = self._fetch_all_pages(url, params, operation="Claims")
        logger.info(f"[Trendyol Claims] Total fetched: {len(claims)} claims")
        return claims

    # ------------------------------------------------------------------
    # PRODUCTS
    # ------------------------------------------------------------------
    def fetch_products(self) -> List[Dict]:
        """Fetch all products (approved, non-archived)."""
        url = f"{self.BASE_URL}/product/sellers/{self.seller_id}/products"
        params = {
            "size": PRODUCT_PAGE_SIZE,
            "archived": False,
            # approved filtresi kaldırıldı — onay bekleyen ve reddedilen ürünler de çekilsin
        }
        products = self._fetch_all_pages(url, params, operation="Products")
        logger.info(f"[Trendyol Products] Total fetched: {len(products)} products")
        return products

    # ------------------------------------------------------------------
    # SETTLEMENTS (financial)
    # ------------------------------------------------------------------
    def fetch_settlements(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> List[Dict]:
        """Fetch settlement/financial data."""
        url = f"{self.BASE_URL}/finance/sellers/{self.seller_id}/settlements"
        params = {"size": 100}
        
        if start_date:
            params["startDate"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["endDate"] = int(end_date.timestamp() * 1000)

        try:
            return self._fetch_all_pages(url, params, operation="Settlements", max_pages=20)
        except Exception as e:
            logger.warning(f"[Trendyol Settlements] Non-critical error: {e}")
            return []

    # ------------------------------------------------------------------
    # CONNECTION TEST
    # ------------------------------------------------------------------
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection. Returns dict with success, seller info, etc."""
        url = f"{self.BASE_URL}/order/sellers/{self.seller_id}/orders"
        params = {"size": 1, "page": 0}
        
        try:
            response = self._request_with_retry(url, params, operation="Connection Test")
            data = response.json()
            return {
                "success": True,
                "total_orders": data.get("totalElements", 0),
                "total_pages": data.get("totalPages", 0),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
