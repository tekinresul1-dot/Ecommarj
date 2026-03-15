import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

# Remove ALL location /api blocks
# This regex is very greedy but specifically targets blocks starting with location /api
# We use a non-greedy match for the contents to avoid eating too much.
pattern = r'\n\s*location\s+[\^~=]*\s*/api/?\s*\{[\s\S]*?\}'
while re.search(pattern, config):
    config = re.sub(pattern, '', config)

# Remove the comments I added too
config = config.replace('# Handle API requests directly to Django to ensure Next.js does not get them', '')
config = config.replace('# Handle both with and without trailing slash explicitly for Django', '')

# Re-insert ONE clean block
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

if "location / {" in config:
    # Use one replacement at the first occurrence
    config = config.replace("location / {", f"{api_block}\n    location / {{", 1)

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
print("Nginx deduped.")
