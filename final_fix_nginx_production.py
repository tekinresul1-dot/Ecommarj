import pexpect
import sys

IP = "91.98.226.158"
PASSWORD = "UUXp7dgud7UF"
NGINX_CONF_PATH = "/etc/nginx/sites-available/ecommarj"
STATIC_PATH = "/var/www/EcomMarj/backend/staticfiles"

NEW_CONFIG = f"""
server {{
    server_name ecommarj.com www.ecommarj.com;
    
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/ecommarj.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ecommarj.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

    # Django Admin (Path based)
    location ^~ /admin/ {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # API
    location /api/ {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Static Files
    location /static/ {{
        alias {STATIC_PATH}/;
    }}

    # Frontend
    location / {{
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }}
}}

server {{
    server_name api.ecommarj.com;
    
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/ecommarj.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ecommarj.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }}
}}

server {{
    server_name admin.ecommarj.com;
    
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/ecommarj.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ecommarj.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

    location /static/ {{
        alias {STATIC_PATH}/;
    }}

    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }}
}}

# Redirect HTTP to HTTPS
server {{
    listen 80;
    server_name ecommarj.com www.ecommarj.com api.ecommarj.com admin.ecommarj.com;
    absolute_redirect off;
    port_in_redirect off;
    return 301 https://$host$request_uri;
}}
"""

# Escaping single quotes for bash
escaped_config = NEW_CONFIG.replace("'", "'\\''")

COMMAND = f"echo '{escaped_config}' > {NGINX_CONF_PATH} && nginx -t && systemctl reload nginx"

print(f"Connecting to {IP} to apply final Nginx fix...")
child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no root@{IP} "{COMMAND}"', encoding='utf-8')
child.logfile = sys.stdout

try:
    i = child.expect(['assword:', pexpect.EOF, pexpect.TIMEOUT], timeout=15)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(pexpect.EOF, timeout=30)
    elif i == 1:
        print("Done without password prompt.")
except Exception as e:
    print(f"Error: {e}")

child.close()
print(f"Deployment finished with status: {child.exitstatus}")
