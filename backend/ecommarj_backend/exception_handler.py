"""
Custom DRF exception handler — ensures ALL errors return JSON, never HTML.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default handler and catches any unhandled exceptions
    so the API never returns HTML error pages.
    """
    # Let DRF handle known exceptions first (400, 401, 403, 404, etc.)
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Unhandled exception — log it and return a clean JSON 500
    view = context.get("view", None)
    view_name = view.__class__.__name__ if view else "unknown"
    logger.exception(
        f"[500] Unhandled exception in {view_name}: {exc}",
        exc_info=exc,
    )

    return Response(
        {
            "error": "Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.",
            "detail": str(exc),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
