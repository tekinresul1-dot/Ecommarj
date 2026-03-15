import re

urls_path = '/var/www/ecommarj/backend/core/urls.py'
with open(urls_path, 'r') as f:
    urls_content = f.read()

# Add imports if missing
if 'SendOTPView' not in urls_content:
    urls_content = "from .auth_views import SendOTPView, VerifyOTPView\n" + urls_content

# Add paths if missing
if 'auth/send-otp/' not in urls_content:
    urls_content = urls_content.replace('urlpatterns = [', 'urlpatterns = [\n    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),\n    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),')

with open(urls_path, 'w') as f:
    f.write(urls_content)

settings_path = '/var/www/ecommarj_backend/settings.py'
# Wait, settings path is /var/www/ecommarj/backend/ecommarj_backend/settings.py
settings_path = '/var/www/ecommarj/backend/ecommarj_backend/settings.py'

with open(settings_path, 'r') as f:
    settings_content = f.read()

# Restore APPEND_SLASH
if 'APPEND_SLASH = False' in settings_content:
    settings_content = settings_content.replace('APPEND_SLASH = False', 'APPEND_SLASH = True')

# Ensure DEBUG=False
# Handled via .env

with open(settings_path, 'w') as f:
    f.write(settings_content)

print("Django final fix applied.")
