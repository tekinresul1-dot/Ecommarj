import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

# Replace all location /api blocks with a single clean one
config = re.sub(r'\n\s*location /api/? \{[\s\S]*?\}', '', config)
config = re.sub(r'\n\s*location /api \{[\s\S]*?\}', '', config)
config = re.sub(r'\n\s*location \^~ /api \{[\s\S]*?\}', '', config)

api_block_new = """
    # Handle both with and without trailing slash explicitly for Django
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""

config = config.replace(
    "\n    location / {",
    f"{api_block_new}\n    location / {{"
)

# Remove any duplicates just in case
config = re.sub(r'location /api \{\s*proxy_pass http://127.0.0.1:8000;\s*proxy_set_header Host \$host;\s*proxy_set_header X-Real-IP \$remote_addr;\s*proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\s*proxy_set_header X-Forwarded-Proto \$scheme;\s*\}\s*location /api \{', 'location /api {', config)

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
