import re

with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

config = re.sub(r'\n\s*location \^~ /api \{[\s\S]*?\}', '', config)

api_block_new = """
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location = /api/auth/send-otp {
        return 308 /api/auth/send-otp/;
    }
"""

config = config.replace(
    "\n    location / {",
    f"\n{api_block_new}\n    location / {{"
)

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
