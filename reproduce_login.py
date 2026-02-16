
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    print(f"Testing login at {BASE_URL}...")
    
    # 1. Login
    login_data = {
        "username": "admin",
        "password": "Prismid@2026"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login Status Code: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code != 200:
            print("Login failed!")
            return
            
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        
        print(f"Access Token: {access_token[:20]}...")
        
        # 2. Test accessing a protected endpoint
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        print("\nTesting protected endpoint (get divisions)...")
        resp_div = requests.get(f"{BASE_URL}/api/divisions", headers=headers)
        print(f"Divisions Status Code: {resp_div.status_code}")
        print(f"Divisions Response: {resp_div.text[:200]}...")
        
        if resp_div.status_code == 401:
            print("Protected endpoint failed with 401!")
            
        # 3. Test refresh
        print("\nTesting token refresh...")
        refresh_data = {"refresh_token": refresh_token}
        resp_refresh = requests.post(f"{BASE_URL}/api/auth/refresh", json=refresh_data)
        print(f"Refresh Status Code: {resp_refresh.status_code}")
        print(f"Refresh Response: {resp_refresh.text[:200]}...")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_login()
