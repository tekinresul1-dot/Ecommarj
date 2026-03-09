"""
Celery application for ecommarj_backend.
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommarj_backend.settings")

app = Celery("ecommarj_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
