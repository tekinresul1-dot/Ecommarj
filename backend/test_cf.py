import cloudscraper
import requests

# Set credentials
seller_id = "856063"
api_key = "K89KKCv4COp7ZfMep0NV"
api_secret = "llDqplGqQPUBbFDXD5ul"

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
