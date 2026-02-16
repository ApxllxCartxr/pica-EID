import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin"
ADMIN_PASSWORD = "Prismid@2026"

def login():
    print("Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        print("Login successful")
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        exit(1)

def create_user(token, name, email, category="EMPLOYEE"):
    print(f"Creating user {name} ({category})...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": name,
        "email": email,
        "category": category,
        "role_ids": [], # Optional
        "domain_id": None,
        "division_id": None
    }
    response = requests.post(f"{BASE_URL}/users", json=data, headers=headers)
    if response.status_code == 200:
        print(f"User created: {response.json()['id']}")
        return response.json()
    else:
        print(f"Create user failed: {response.text}")
        return None

def check_user_active(token, user_id):
    print(f"Checking if user {user_id} is active...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/{user_id}", headers=headers)
    if response.status_code == 200:
        print("User found (Active)")
        return True
    elif response.status_code == 404:
        print("User not found (Active)")
        return False
    else:
        print(f"Check user failed: {response.text}")
        return False

def soft_delete_user(token, user_id):
    print(f"Soft deleting user {user_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/users/{user_id}", headers=headers)
    if response.status_code == 200:
        print("User soft deleted")
    else:
        print(f"Soft delete failed: {response.text}")

def restore_user(token, user_id):
    print(f"Restoring user {user_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/users/{user_id}/restore", headers=headers)
    if response.status_code == 200:
        print("User restored")
    else:
        print(f"Restore failed: {response.text}")

def hard_delete_user(token, user_id):
    print(f"Permanently deleting user {user_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/users/{user_id}/permanent", headers=headers)
    if response.status_code == 200:
        print("User permanently deleted")
    else:
        print(f"Permanent delete failed: {response.text}")

def main():
    token = login()
    
    # 1. Create User
    user = create_user(token, "Verify User", "verify@example.com")
    if not user:
        return

    user_id = user["id"]

    # 2. Check Active
    if not check_user_active(token, user_id):
        print("Error: User should be active")
        return

    # 3. Soft Delete
    soft_delete_user(token, user_id)

    # 4. Check Active (Should be missing or 404 in standard get)
    # The API /users/{id} might return 404 if soft deleted, depending on implementation.
    # My implementation: `get_user` filters out deleted unless `include_deleted=True`.
    if check_user_active(token, user_id):
        print("Error: User should NOT be active (soft deleted)")
        # Continue anyway
    
    # 5. Restore
    restore_user(token, user_id)

    # 6. Check Active
    if not check_user_active(token, user_id):
        print("Error: User should be active after restore")
        return

    # 7. Soft Delete Again (to prepare for hard delete)
    soft_delete_user(token, user_id)

    # 8. Hard Delete
    hard_delete_user(token, user_id)

    # 9. Restore (Should Fail)
    print("Attempting to restore permanently deleted user...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/users/{user_id}/restore", headers=headers)
    if response.status_code == 404:
        print("Restore failed as expected (404)")
    else:
        print(f"Error: Restore gave {response.status_code}")

    print("\nVerification Complete!")

if __name__ == "__main__":
    main()
