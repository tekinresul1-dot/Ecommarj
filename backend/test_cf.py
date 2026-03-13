import cloudscraper
import requests

# Set credentials (load from environment variables)
import os
seller_id = os.environ.get("TRENDYOL_SELLER_ID", "")
api_key = os.environ.get("TRENDYOL_API_KEY", "")
api_secret = os.environ.get("TRENDYOL_API_SECRET", "")

url = f"https://api.trendyol.com/sapigw/suppliers/{seller_id}/products?size=1"
headers = {
    "User-Agent": f"{seller_id} - SelfIntegration"
}

scraper = cloudscraper.create_scraper()
try:
    print(f"Requesting via cloudscraper: {url}")
    response = scraper.get(url, auth=(api_key, api_secret), headers=headers)
    print(f"Status: {response.status_code}")
    print(response.text[:300])
except Exception as e:
    print("Cloudscraper error:", e)
