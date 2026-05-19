"""
Scoped rate throttles for sensitive auth endpoints.

Rates are configured in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
Both key by client IP (these endpoints are unauthenticated / AllowAny).
"""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class OTPRateThrottle(AnonRateThrottle):
    scope = "otp"
