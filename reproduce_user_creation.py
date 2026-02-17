import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Prismid@2026"})
    if response.status_code == 200:
        return response.json()["access_token"]
    
    print(f"Login failed with Prismid@2026: {response.status_code} {response.text}")
    
    # Retry with old password
    response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "adminpassword"})
    if response.status_code == 200:
        print("Login succeeded with fallback password 'adminpassword'")
        return response.json()["access_token"]

    print(f"Login failed with adminpassword: {response.status_code} {response.text}")
    return None

def test_create_user(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Payload similar to what frontend likely sends for an Employee
    payload = {
        "name": "Test Employee",
        "email": "test.employee@example.com",
        "phone_number": "1234567890",
        "category": "EMPLOYEE",
        "date_of_joining": "2023-01-01",
        # "domain_id": undefined in frontend becomes missing here
        # "division_id": undefined in frontend becomes missing here
        "role_ids": []
    }
    
    print("\nTesting Payload 1 (Employee):")
    response = requests.post(f"{BASE_URL}/users", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    # Payload with empty strings (checking edge cases)
    payload_empty = {
        "name": "Test Employee 2",
        "email": "test.employee2@example.com",
        "phone_number": "",
        "category": "EMPLOYEE",
        "date_of_joining": "2023-01-01",
        "role_ids": []
    }
    
    print("\nTesting Payload 2 (Empty strings):")
    response = requests.post(f"{BASE_URL}/users", json=payload_empty, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    # Payload with empty date strings (Hypothesis for failure)
    payload_empty_dates = {
        "name": "Test Failure",
        "email": "test.failure@example.com",
        "category": "EMPLOYEE",
        "start_date": "",
        "end_date": "",
        "date_of_joining": "2023-01-01",
        "role_ids": []
    }

    print("\nTesting Payload 4 (Empty Date Strings):")
    response = requests.post(f"{BASE_URL}/users", json=payload_empty_dates, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    # Payload matching Intern
    payload_intern = {
        "name": "Test Intern",
        "email": "test.intern@example.com",
        "category": "INTERN",
        "start_date": "2023-01-01",
        "end_date": "2023-06-01",
        "role_ids": []
    }

    print("\nTesting Payload 3 (Intern):")
    response = requests.post(f"{BASE_URL}/users", json=payload_intern, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    token = login()
    if token:
        test_create_user(token)
