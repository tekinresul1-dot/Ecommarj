import os

view_path = '/var/www/ecommarj/backend/core/auth_views.py'
with open(view_path, 'r') as f:
    content = f.read()

# Add a dispatch method to SendOTPView for debugging
dispatch_method = """
    def dispatch(self, request, *args, **kwargs):
        print(f"DEBUG: Request Path: {request.path}")
        print(f"DEBUG: Request Method: {request.method}")
        print(f"DEBUG: Request Secure: {request.is_secure()}")
        print(f"DEBUG: Request Headers: {dict(request.headers)}")
        return super().dispatch(request, *args, **kwargs)
"""

if 'def dispatch(self, request' not in content:
    content = content.replace('class SendOTPView(APIView):', 'class SendOTPView(APIView):' + dispatch_method)
    with open(view_path, 'w') as f:
        f.write(content)
    print('Debug logging added to SendOTPView')

