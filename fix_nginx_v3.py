import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

# Clear out any /api blocks
config = re.sub(r'\n\s*location\s+\^~?\s*/api/?\s*\{[\s\S]*?\}', '', config)

# Use a very standard API block
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
    config = config.replace("location / {", f"{api_block}\n    location / {{")

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
