import base64
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet() -> Fernet:
    """
    Derives a 32-byte url-safe base64 key from Django's SECRET_KEY.
    """
    key = settings.SECRET_KEY.encode('utf-8')[:32].ljust(32, b'0')
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)

def encrypt_value(value: str) -> str:
    if not value:
        return ""
    f = get_fernet()
    return f.encrypt(value.encode('utf-8')).decode('utf-8')

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(encrypted_value.encode('utf-8')).decode('utf-8')
    except Exception:
        # Fallback for plain-text legacy values during transition
        return encrypted_value
