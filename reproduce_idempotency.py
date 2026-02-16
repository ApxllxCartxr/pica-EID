
import requests
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_login_with_idempotency():
    print(f"Testing login with Idempotency-Key at {BASE_URL}...")
    
    login_data = {
        "username": "admin",
        "password": "Prismid@2026"
    }
    
    headers = {
        "Idempotency-Key": str(uuid.uuid4())
    }
    
    try:
        # First attempt
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
        print(f"Login 1 Status: {response.status_code}")
        print(f"Login 1 Body len: {len(response.text)}")
        if response.status_code == 200:
             print("Login 1 Success")
        else:
             print(f"Login 1 Failed: {response.text}")

        # Second attempt (same key) - should be cached
        response2 = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
        print(f"Login 2 Status: {response2.status_code}")
        print(f"Login 2 Body len: {len(response2.text)}")
        if response2.headers.get("X-Idempotent-Replay"):
            print("Idempotent Replay Header Present")
        else:
            print("Idempotent Replay Header MISSING")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_login_with_idempotency()
