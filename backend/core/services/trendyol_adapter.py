import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TrendyolAdapter:
    """
    Trendyol API Bağdaştırıcısı.
    Siparişleri, ürünleri (KDV, satış fiyatı, görsel) ve cari/komisyon hesaplarını (Settlements) çeker.
    """
    BASE_URL = "https://api.trendyol.com/sapigw/suppliers"

    def __init__(self, api_key: str, api_secret: str, seller_id: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.seller_id = seller_id

    @property
    def _auth(self):
        return (self.api_key, self.api_secret)

    @property
    def _headers(self):
        return {"User-Agent": f"{self.seller_id} - EcomPro"}

    def fetch_orders(self, start_date_ms: int = None, end_date_ms: int = None, status: str = None) -> List[Dict[Any, Any]]:
        """
        Trendyol'dan sipariş listesini çeker. 
        Mili-saniye cinsinden tarih aralığı alabilir.
        """
        url = f"{self.BASE_URL}/{self.seller_id}/orders"
        
        params = {
            "size": 100,
        }
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
                response = requests.get(url, auth=self._auth, headers=self._headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                content = data.get("content", [])
                if not content:
                    break
                    
                all_content.extend(content)
                
                if page >= data.get("totalPages", 0) - 1:
                    break
                page += 1
                
            return all_content
            
        except requests.RequestException as e:
            logger.error(f"Trendyol Orders fetch error: {e}")
            return []

    def fetch_products(self, barcode: str = None) -> List[Dict[Any, Any]]:
        """
        Ürün katalogunu çeker. Trendyol product API üzerinden
        ürünün kdv, barkod, isim, fotoğraf ve satış fiyatı alınır.
        """
        url = f"{self.BASE_URL}/{self.seller_id}/products"
        params = {
            "size": 100,
        }
        if barcode:
            params["barcode"] = barcode
            
        all_content = []
        page = 0
        
        try:
            while True:
                params["page"] = page
                response = requests.get(url, auth=self._auth, headers=self._headers, params=params, timeout=30)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                content = data.get("content", [])
                
                if not content:
                    break
                    
                all_content.extend(content)
                
                if page >= data.get("totalPages", 1) - 1:
                    break
                page += 1
                
            return all_content
            
        except requests.RequestException as e:
            logger.error(f"Trendyol Products fetch error: {e}")
            return []

    def fetch_financials(self, start_date_ms: int = None, end_date_ms: int = None) -> List[Dict[Any, Any]]:
        """
        Cari / Hakediş (Settlements) finansal verilerini çeker.
        Siparişlerdeki net komisyon tutarlarını ve kargo kesintilerini görmek için.
        """
        url = f"{self.BASE_URL}/{self.seller_id}/settlements"
        params = {
            "size": 100,
            "transactionType": "Sale" # Refund, Deduction vs filtrenebilir
        }
        
        if start_date_ms:
            params["startDate"] = start_date_ms
        if end_date_ms:
            params["endDate"] = end_date_ms
            
        all_content = []
        page = 0
        try:
            while page < 5: # Limit imposed to avoid heavy load, remove or adapt for full sync
                params["page"] = page
                response = requests.get(url, auth=self._auth, headers=self._headers, params=params, timeout=30)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                content = data.get("content", [])
                
                if not content:
                    break
                    
                all_content.extend(content)
                page += 1
            return all_content
            
        except requests.RequestException as e:
            logger.error(f"Trendyol Settlements fetch error: {e}")
            return []
