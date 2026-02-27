"""
Celery application for ecompro_backend.
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecompro_backend.settings")

app = Celery("ecompro_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
