import requests
import json
import random
import time

BASE_URL = "http://localhost:8000/api"

def test_auth_flow():
    email = f"test_{random.randint(1000, 9999)}@example.com"
    password = "password123"
    
    print(f"\n--- Testing Signup for {email} ---")
    
    try:
        # 1. Register
        reg_resp = requests.post(f"{BASE_URL}/auth/register/", json={
            "name": "Test User",
            "email": email,
            "password": password,
            "password_confirm": password,
            "company": "Test Co"
        })
        
        if reg_resp.status_code != 201:
            print(f"FAILED: Signup returned {reg_resp.status_code}")
            print(reg_resp.json())
            return
        
        print("SUCCESS: Signup completed. User is created (inactive).")
        
        # 2. Verify (using master OTP '000000' for testing)
        print(f"\n--- Testing Verification for {email} ---")
        verify_resp = requests.post(f"{BASE_URL}/auth/register/verify/", json={
            "email": email,
            "otp": "000000"
        })
        
        if verify_resp.status_code != 200:
            print(f"FAILED: Verification returned {verify_resp.status_code}")
            print(verify_resp.json())
            return
            
        data = verify_resp.json()
        print("SUCCESS: User verified and logged in.")
        print(f"Tokens received: {list(data['tokens'].keys())}")
        
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        print("Note: This script assumes the backend is running at http://localhost:8000")

if __name__ == "__main__":
    test_auth_flow()
