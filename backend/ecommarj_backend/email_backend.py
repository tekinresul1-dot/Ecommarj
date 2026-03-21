"""
Custom SMTP email backend that uses certifi CA bundle.
macOS Python 3.14 does not ship with system CA certificates,
so we load them from the certifi package.
"""

import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend


class CertifiEmailBackend(DjangoEmailBackend):
    """EmailBackend that builds the SSL context from certifi's CA bundle."""

    def open(self):
        if self.connection:
            return False
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_context = ssl.create_default_context()

        self.connection = smtplib.SMTP(
            self.host, self.port, timeout=self.timeout
        )
        self.connection.ehlo()
        if self.use_tls:
            self.connection.starttls(context=ssl_context)
            self.connection.ehlo()
        if self.username and self.password:
            self.connection.login(self.username, self.password)
        return True
