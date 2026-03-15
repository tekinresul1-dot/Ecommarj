import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

# Remove any existing location blocks for /api to start fresh
config = re.sub(r'\n\s*location\s+\^~?\s*/api/?\s*\{[\s\S]*?\}', '', config)
config = re.sub(r'\n\s*location\s*=\s*/api/auth/send-otp\s*\{[\s\S]*?\}', '', config)

# Modern, clean API block for Django
api_block = """
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Ensure we don't have redirect loops from Django
        proxy_redirect off;
    }
"""

# Insert before the catch-all location / {
if "location / {" in config:
    config = config.replace("location / {", f"{api_block}\n    location / {{")

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
