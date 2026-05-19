"""
Symmetric encryption helpers for marketplace API credentials at rest.

Uses a dedicated ENCRYPTION_KEY (Fernet key) configured in settings — NOT
SECRET_KEY — so that rotating the JWT signing key never makes previously
stored credentials undecryptable.
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class DecryptionError(Exception):
    """Raised when a stored value cannot be decrypted with the active key."""


def get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode("utf-8")
    try:
        return Fernet(key)
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            "ENCRYPTION_KEY is not a valid 32-byte url-safe base64 Fernet key. "
            "Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        ) from exc


def encrypt_value(value: str) -> str:
    if not value:
        return ""
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return ""
    try:
        return get_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        # No fail-open: a value that cannot be decrypted is an error, never
        # silently treated as plaintext (which would leak ciphertext upstream).
        raise DecryptionError(
            "Stored credential could not be decrypted with the active ENCRYPTION_KEY. "
            "The credential must be re-saved after a key change."
        ) from exc
