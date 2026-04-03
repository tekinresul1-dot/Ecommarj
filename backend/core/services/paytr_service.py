"""
PayTR sanal pos entegrasyon servisi.
"""
import hashlib
import hmac
import base64
import json
import time
import random
import requests
from django.conf import settings


class PayTRService:
    PAYTR_URL = "https://www.paytr.com/odeme/api/get-token"

    def create_payment_token(self, payment, user, user_ip, callback_url, success_url, fail_url):
        merchant_oid = f"ECOMMARJ_{user.id}_{int(time.time())}_{random.randint(1000, 9999)}"

        user_basket = base64.b64encode(
            json.dumps([[payment.plan.name, str(payment.amount), 1]]).encode()
        ).decode()

        test_mode = "1" if getattr(settings, "PAYTR_TEST_MODE", True) else "0"
        amount_kurus = str(int(payment.amount * 100))

        hash_str = (
            settings.PAYTR_MERCHANT_ID
            + user_ip
            + merchant_oid
            + amount_kurus
            + "TL"
            + "tr"
            + test_mode
            + settings.PAYTR_MERCHANT_SALT
        )

        paytr_token = base64.b64encode(
            hmac.new(
                settings.PAYTR_MERCHANT_KEY.encode(),
                hash_str.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()

        data = {
            "merchant_id": settings.PAYTR_MERCHANT_ID,
            "user_ip": user_ip,
            "merchant_oid": merchant_oid,
            "email": user.email,
            "payment_amount": int(payment.amount * 100),
            "paytr_token": paytr_token,
            "user_basket": user_basket,
            "debug_on": 1 if getattr(settings, "PAYTR_TEST_MODE", True) else 0,
            "no_installment": 0,
            "max_installment": 0,
            "user_name": user.get_full_name() or user.email,
            "user_address": "Türkiye",
            "user_phone": "05000000000",
            "merchant_ok_url": success_url,
            "merchant_fail_url": fail_url,
            "timeout_limit": 30,
            "currency": "TL",
            "test_mode": 1 if getattr(settings, "PAYTR_TEST_MODE", True) else 0,
            "lang": "tr",
        }

        response = requests.post(self.PAYTR_URL, data=data, timeout=30)
        result = response.json()

        if result.get("status") == "success":
            return merchant_oid, result["token"]
        else:
            raise Exception(f"PayTR token hatası: {result.get('reason', 'Bilinmeyen hata')}")

    def verify_callback(self, post_data):
        """PayTR callback hash doğrulaması."""
        merchant_oid = post_data.get("merchant_oid", "")
        status = post_data.get("status", "")
        total_amount = post_data.get("total_amount", "")

        hash_str = merchant_oid + settings.PAYTR_MERCHANT_SALT + status + str(total_amount)

        expected_hash = base64.b64encode(
            hmac.new(
                settings.PAYTR_MERCHANT_KEY.encode(),
                hash_str.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()

        return expected_hash == post_data.get("hash", "")
