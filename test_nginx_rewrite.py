import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

api_block_new = """
    # Handle API requests directly to Django to ensure Next.js does not get them
    location ^~ /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""

config = re.sub(r'location /api \{[\s\S]*?\}', '', config)
config = re.sub(r'location /api/ \{[\s\S]*?\}', '', config)

config = config.replace(
    "location / {",
    f"{api_block_new}\n    location / {{"
)

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
