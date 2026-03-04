import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def _trendyol_user_agent(seller_id: str) -> str:
    """Trendyol requires User-Agent in format: {sellerId} - SelfIntegration"""
    return f"{seller_id} - SelfIntegration"


class TrendyolAdapter:
    """
    Trendyol Partner API Bağdaştırıcısı.
    
    CRITICAL: Doğru base URL: apigw.trendyol.com/integration/
    api.trendyol.com/sapigw/ => Cloudflare WAF tarafından engelleniyor.
    
    Official docs: https://developers.trendyol.com/docs/2-authorization
    """
    # Correct base URL per official Trendyol docs
    BASE_URL = "https://apigw.trendyol.com/integration"

    def __init__(self, api_key: str, api_secret: str, seller_id: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.seller_id = seller_id

    @property
    def _auth(self):
        return (self.api_key, self.api_secret)

    @property
    def _headers(self):
        return {
            "User-Agent": _trendyol_user_agent(self.seller_id),
            "Accept": "application/json",
        }

    def _make_request(self, url: str, params: dict = None, operation: str = "API") -> requests.Response:
        """Centralized request method with debug logging."""
        safe_headers = {k: v for k, v in self._headers.items()}
        logger.info(f"[Trendyol {operation}] URL: {url}")
        logger.info(f"[Trendyol {operation}] Params: {params}")
        logger.info(f"[Trendyol {operation}] Headers: {safe_headers}")
        logger.info(f"[Trendyol {operation}] Auth: ({self.api_key[:4]}...***)")

        response = requests.get(
            url,
            auth=self._auth,
            headers=self._headers,
            params=params,
            timeout=30,
        )

        logger.info(f"[Trendyol {operation}] Status: {response.status_code}")
        
        # Log response body snippet (first 200 chars, redacted)
        body_preview = response.text[:200].replace(self.api_secret, "***SECRET***")
        logger.info(f"[Trendyol {operation}] Body preview: {body_preview}")

        return response

    def _handle_api_error(self, e: requests.RequestException, operation: str):
        """Standardized error mapping logic."""
        error_details = str(e)
        if hasattr(e, 'response') and e.response is not None:
            status = e.response.status_code
            text = e.response.text

            if '<html' in text.lower() or 'cloudflare' in text.lower():
                raise ValueError(
                    f"Trendyol API HTML yanıtı döndü (status={status}). "
                    "Olası nedenler: Yanlış base URL (apigw.trendyol.com kullanın), "
                    "IP whitelist sorunu veya geçici kesinti."
                )

            if status == 401:
                raise ValueError("API Key veya API Secret hatalı. Lütfen kontrol edin.")
            elif status == 403:
                raise ValueError("Supplier ID yetkisiz veya API anahtarı bu satıcıya ait değil.")
            elif status == 429:
                raise ValueError("Çok fazla istek gönderildi. Lütfen biraz bekleyip tekrar deneyin.")
            elif status == 556:
                raise ValueError(f"Trendyol {operation} servisi şu an kullanılamıyor (556). Daha sonra tekrar deneyin.")
            else:
                try:
                    data = e.response.json()
                    err_msg = data.get("message", text[:300])
                except ValueError:
                    err_msg = text[:300]
                raise ValueError(f"Trendyol API Hatası ({status}): {err_msg}")

        raise ValueError(f"Trendyol {operation} - ağ hatası: {error_details}")

    # ------------------------------------------------------------------
    # ORDERS — apigw.trendyol.com/integration/order/sellers/{id}/orders
    # ------------------------------------------------------------------
    def fetch_orders(self, start_date_ms: int = None, end_date_ms: int = None, status: str = None) -> List[Dict[Any, Any]]:
        """Trendyol'dan sipariş listesini çeker."""
        url = f"{self.BASE_URL}/order/sellers/{self.seller_id}/orders"

        params = {"size": 200}
        if start_date_ms:
            params["startDate"] = start_date_ms
        if end_date_ms:
            params["endDate"] = end_date_ms
        if status:
            params["status"] = status

        all_content = []
        page = 0

        try:
            while True:
                params["page"] = page
                response = self._make_request(url, params, operation="Orders")
                response.raise_for_status()
                data = response.json()

                content = data.get("content", [])
                if not content:
                    break

                all_content.extend(content)

                total_pages = data.get("totalPages", 1)
                if page >= total_pages - 1:
                    break
                page += 1

            logger.info(f"[Trendyol Orders] Fetched {len(all_content)} orders across {page + 1} pages")
            return all_content

        except requests.RequestException as e:
            logger.error(f"Trendyol Orders fetch error for seller {self.seller_id}: {e}")
            self._handle_api_error(e, "siparişleri çekme")

    # ------------------------------------------------------------------
    # PRODUCTS — apigw.trendyol.com/integration/product/sellers/{id}/products
    # ------------------------------------------------------------------
    def fetch_products(self, barcode: str = None) -> List[Dict[Any, Any]]:
        """Ürün katalogunu çeker. Arşivlenmiş ürünler hariç tutulur."""
        url = f"{self.BASE_URL}/product/sellers/{self.seller_id}/products"
        params = {
            "size": 100,
            "archived": False,   # Arşivlenmiş ürünleri getirme
            "approved": True,    # Sadece onaylanmış (satıştaki) ürünler
        }

        all_content = []
        page = 0

        try:
            while True:
                params["page"] = page
                response = self._make_request(url, params, operation="Products")
                response.raise_for_status()

                data = response.json()
                content = data.get("content", [])

                if not content:
                    break

                all_content.extend(content)

                total_pages = data.get("totalPages", 1)
                if page >= total_pages - 1:
                    break
                page += 1

            logger.info(f"[Trendyol Products] Fetched {len(all_content)} products across {page + 1} pages")
            return all_content

        except requests.RequestException as e:
            logger.error(f"Trendyol Products fetch error for seller {self.seller_id}: {e}")
            self._handle_api_error(e, "ürünleri çekme")

    # ------------------------------------------------------------------
    # SETTLEMENTS — Financial data
    # ------------------------------------------------------------------
    def fetch_financials(self, start_date_ms: int = None, end_date_ms: int = None) -> List[Dict[Any, Any]]:
        """Cari / Hakediş (Settlements) finansal verilerini çeker."""
        url = f"{self.BASE_URL}/finance/sellers/{self.seller_id}/settlements"
        params = {"size": 100}

        if start_date_ms:
            params["startDate"] = start_date_ms
        if end_date_ms:
            params["endDate"] = end_date_ms

        all_content = []
        page = 0
        try:
            while page < 5:
                params["page"] = page
                response = self._make_request(url, params, operation="Settlements")
                
                # Settlements API might not be available (556)
                if response.status_code == 556:
                    logger.warning("[Trendyol Settlements] Service unavailable (556). Skipping.")
                    return []
                
                response.raise_for_status()
                data = response.json()
                content = data.get("content", [])

                if not content:
                    break

                all_content.extend(content)
                page += 1
            
            logger.info(f"[Trendyol Settlements] Fetched {len(all_content)} items")
            return all_content

        except requests.RequestException as e:
            logger.warning(f"Trendyol Settlements fetch error (non-critical): {e}")
            return []  # Non-critical — don't break sync for financial data
