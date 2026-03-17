settings_path = '/var/www/ecommarj/backend/ecommarj_backend/settings.py'
with open(settings_path, 'r') as f:
    config = f.read()

config = config.replace('# "django.middleware.security.SecurityMiddleware",', '"django.middleware.security.SecurityMiddleware",')
config = config.replace('# "django.middleware.common.CommonMiddleware",', '"django.middleware.common.CommonMiddleware",')
# We handled DEBUG via .env, we can keep it as True for a second while testing, 
# but let's restore it in .env soon.

with open(settings_path, 'w') as f:
    f.write(config)

view_path = '/var/www/ecommarj/backend/core/auth_views.py'
with open(view_path, 'r') as f:
    content = f.read()

import re
content = re.sub(r'\n\s*def dispatch\(self, request, \*args, \*\*kwargs\):[\s\S]*?return super\(\)\.dispatch\(request, \*args, \*\*kwargs\)', '', content)

with open(view_path, 'w') as f:
    f.write(content)
print("Django restored.")
