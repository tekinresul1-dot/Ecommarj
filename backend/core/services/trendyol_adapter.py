class TrendyolAdapter:
    """
    Trendyol API Stub/Mock Bağdaştırıcısı.
    Gerçek entegrasyon yapılana kadar servis motoruna mimari hazırlar.
    """

    def __init__(self, api_key: str, api_secret: str, seller_id: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.seller_id = seller_id

    def fetch_orders(self, start_date=None, end_date=None):
        """Trendyol'dan sipariş listesini çeker."""
        return []

    def fetch_financials(self, start_date=None, end_date=None):
        """Cari / Hakediş finansal verilerini çeker."""
        return []

    def fetch_products(self):
        """Ürün katalogunu çeker."""
        return []
