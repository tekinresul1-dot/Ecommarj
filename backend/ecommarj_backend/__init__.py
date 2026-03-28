"""
ecommarj_backend Django project package.
"""
# Celery app'i Django başladığında yükle — @shared_task'ların doğru app'e bağlanması için
from .celery import app as celery_app

__all__ = ("celery_app",)
