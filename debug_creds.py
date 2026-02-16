
import os
import sys
import json
from google.oauth2 import service_account
from google.auth import jwt

# Path to credentials
param_file = "/app/credentials_user/service_account.json"

print(f"Checking file: {param_file}")
if not os.path.exists(param_file):
    print("File not found!")
    sys.exit(1)

try:
    with open(param_file, 'r') as f:
        data = json.load(f)
        private_key = data.get('private_key')
        print(f"Private Key length: {len(private_key)}")
        print(f"Private Key starts with: {private_key[:35]}")
        if "\\n" in private_key:
             print("WARNING: Literal \\n found in private key!")
        if "\n" in private_key:
             print("INFO: Newline found in private key.")
        else:
             print("WARNING: No newline found in private key!")

    creds = service_account.Credentials.from_service_account_file(
        param_file,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    print("Credentials loaded successfully.")
    
    # Try to sign a JWT
    print("Attempting to sign JWT...")
    # This uses the same logic as google-auth to sign
    # We can just try to refresh the token which forces a signature
    import google.auth.transport.requests
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    print("Token refresh successful!")
    print(f"Token: {creds.token[:10]}...")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
