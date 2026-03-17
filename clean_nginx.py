import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

# 1. Remove all location /api blocks (with various formats)
# We hit all variants: location /api, location /api/, location ^~ /api, location = /api...
config = re.sub(r'\n\s*location\s+[\^~=]*\s*/api/?\s*\{[\s\S]*?\}', '', config)

# 2. Re-insert ONE clean block into the ecommarj.com 443 block
api_block = """
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
"""

# Find the main server block { ... location / { ... } ... listen 443 ssl; ... }
# We'll insert it before location / {
if "location / {" in config:
    config = config.replace("location / {", f"{api_block}\n    location / {{")

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
print("Nginx cleaned.")
