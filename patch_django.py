import os

settings_path = '/var/www/ecommarj/backend/ecommarj_backend/settings.py'
with open(settings_path, 'r') as f:
    config = f.read()

if 'APPEND_SLASH = False' not in config:
    config += '\nAPPEND_SLASH = False\n'
    with open(settings_path, 'w') as f:
        f.write(config)
    print('APPEND_SLASH = False added')
else:
    print('APPEND_SLASH already disabled')
