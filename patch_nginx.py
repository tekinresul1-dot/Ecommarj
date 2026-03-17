import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

api_block = """
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""

# Find the server block for ecommarj.com (443 ssl)
# It has "server_name ecommarj.com www.ecommarj.com;" and "listen 443 ssl;"
# We will insert the block right before "location / {"

if "location /api/" not in config:
    # Basic insertion
    config = config.replace(
        "location / {",
        f"{api_block}\n    location / {{"
    )
    with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
        f.write(config)
    print("Patched.")
else:
    print("Already patched.")

