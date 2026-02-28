import requests

seller_id = "856063"
api_key = "K89KKCv4COp7ZfMep0NV"
api_secret = "llDqplGqQPUBbFDXD5ul"

url = f"https://api.trendyol.com/sapigw/suppliers/{seller_id}/products?size=1"
headers = {
    "User-Agent": f"{seller_id} - SelfIntegration"
}

print(f"Requesting: {url}")
try:
    response = requests.get(url, auth=(api_key, api_secret), headers=headers)
    print(f"Status: {response.status_code}")
    print(response.text[:500])
except Exception as e:
    print(e)
