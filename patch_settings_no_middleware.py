with open('/var/www/ecommarj/backend/ecommarj_backend/settings.py', 'r') as f:
    config = f.read()

# Temporarily comment out CommonMiddleware and SecurityMiddleware
config = config.replace('"django.middleware.security.SecurityMiddleware",', '# "django.middleware.security.SecurityMiddleware",')
config = config.replace('"django.middleware.common.CommonMiddleware",', '# "django.middleware.common.CommonMiddleware",')

with open('/var/www/ecommarj/backend/ecommarj_backend/settings.py', 'w') as f:
    f.write(config)
