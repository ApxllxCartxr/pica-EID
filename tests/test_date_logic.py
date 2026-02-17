
import pytest
from datetime import date, timedelta
from app.models.user import UserCategory, UserStatus
from app.core.id_generator import generate_ulid

import time

def test_create_employee_date_logic(client, superadmin_token):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    payload = {
        "name": "Date Logic Employee",
        "email": f"employee_{int(time.time())}@example.com",
        "category": "EMPLOYEE",
        "date_of_joining": str(date.today()),
        "role_ids": []
    }
    response = client.post("/api/v1/users", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["date_of_joining"] == str(date.today())
    assert data["start_date"] is None
    assert data["end_date"] is None

def test_create_intern_date_logic(client, superadmin_token):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    today = date.today()
    end_date = today + timedelta(days=180)
    
    payload = {
        "name": "Date Logic Intern",
        "email": f"intern_{int(time.time())}@example.com",
        "category": "INTERN",
        "date_of_joining": str(today),
        "end_date": str(end_date),
        "role_ids": []
    }
    response = client.post("/api/v1/users", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["date_of_joining"] == str(today)
    assert data["start_date"] == str(today) # Auto-populated
    assert data["end_date"] == str(end_date) # Scheduled end date

def test_retire_employee_sets_end_date(client, superadmin_token, db):
    # Create employee
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    payload = {
        "name": "Retiree",
        "email": f"retire_{int(time.time())}@example.com",
        "category": "EMPLOYEE",
        "date_of_joining": str(date.today()),
    }
    create_res = client.post("/api/v1/users", json=payload, headers=headers)
    user_id = create_res.json()["ulid"]
    
    # Retire
    response = client.post(f"/api/v1/users/{user_id}/retire", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INACTIVE"
    assert data["end_date"] == str(date.today())

def test_end_internship_sets_end_date(client, superadmin_token):
    # Create intern
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    today = date.today()
    future_end = today + timedelta(days=100)
    payload = {
        "name": "Intern Ended",
        "email": f"intern_end_{int(time.time())}@example.com",
        "category": "INTERN",
        "date_of_joining": str(today),
        "end_date": str(future_end),
    }
    create_res = client.post("/api/v1/users", json=payload, headers=headers)
    user_id = create_res.json()["ulid"]
    
    # End Internship
    response = client.post(f"/api/v1/users/{user_id}/end-internship", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "EXPIRED"
    assert data["end_date"] == str(today) # Should be today, not future_end
