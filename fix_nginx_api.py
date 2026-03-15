with open('/etc/nginx/sites-available/ecommarj', 'r') as f:
    config = f.read()

# Replace the api_block with one that explicitly rewrites to trailing slash if needed, 
# or just strips it so Django gets exactly what it expects.
api_block_new = """
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Force trailing slashes for Django API if missing, or 
    # disable Next.js doing the 308. If Next.js does 308, it means Nginx didn't catch /api.
    # We must ensure /api catches everything.
"""

if "location /api { " not in config:
    config = config.replace("location /api/ {", "location /api {")

with open('/etc/nginx/sites-available/ecommarj', 'w') as f:
    f.write(config)
