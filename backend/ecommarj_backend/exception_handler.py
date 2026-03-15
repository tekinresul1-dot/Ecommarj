"""
Custom DRF exception handler — normalises all error responses to a consistent JSON shape.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {"error": "Sunucu hatası oluştu.", "detail": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalise to {"error": ..., "detail": ...}
    if isinstance(response.data, dict):
        if "detail" in response.data and len(response.data) == 1:
            response.data = {"error": str(response.data["detail"])}
    elif isinstance(response.data, list):
        response.data = {"error": response.data}

    return response
