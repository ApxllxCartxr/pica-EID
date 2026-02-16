"""Tests for user API endpoints with ULID-based identification."""

import pytest
from tests.conftest import auth_header


class TestCreateUser:
    """Test user creation with ULID generation."""

    def test_create_employee(self, client, superadmin_token):
        res = client.post("/api/users", json={
            "name": "Alice Johnson",
            "email": "alice@prismid.com",
            "category": "EMPLOYEE",
            "date_of_joining": "2025-01-15",
        }, headers=auth_header(superadmin_token))

        assert res.status_code == 201
        data = res.json()

        # ULID fields
        assert "ulid" in data
        assert len(data["ulid"]) == 26
        assert "display_id" in data
        assert data["display_id"].startswith("EMP-")

        # Display ID format: EMP-XXXX-XXXX-XX
        parts = data["display_id"].split("-")
        assert len(parts) == 4
        assert parts[0] == "EMP"
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 2

        # Other fields
        assert data["name"] == "Alice Johnson"
        assert data["category"] == "EMPLOYEE"
        assert data["status"] == "ACTIVE"

    def test_create_intern(self, client, superadmin_token):
        res = client.post("/api/users", json={
            "name": "Bob Intern",
            "email": "bob.intern@prismid.com",
            "category": "INTERN",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
        }, headers=auth_header(superadmin_token))

        assert res.status_code == 201
        data = res.json()
        assert data["display_id"].startswith("INT-")
        assert data["category"] == "INTERN"
        assert data["start_date"] == "2025-01-01"
        assert data["end_date"] == "2025-06-30"

    def test_intern_requires_dates(self, client, superadmin_token):
        res = client.post("/api/users", json={
            "name": "No Dates",
            "email": "nodates@prismid.com",
            "category": "INTERN",
        }, headers=auth_header(superadmin_token))
        assert res.status_code == 400

    def test_duplicate_email_rejected(self, client, superadmin_token):
        client.post("/api/users", json={
            "name": "First User",
            "email": "dupe@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))

        res = client.post("/api/users", json={
            "name": "Duplicate User",
            "email": "dupe@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))
        assert res.status_code == 409


class TestSearchUsers:
    """Test user search with ULID and display ID."""

    def test_search_by_name(self, client, superadmin_token, viewer_token):
        # Create user first
        client.post("/api/users", json={
            "name": "Searchable User",
            "email": "searchable@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))

        # Search as viewer
        res = client.get("/api/users?q=Searchable", headers=auth_header(viewer_token))
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert any(u["name"] == "Searchable User" for u in data["users"])

    def test_search_response_contains_ulid_and_display_id(self, client, superadmin_token, viewer_token):
        create_res = client.post("/api/users", json={
            "name": "ULID Check User",
            "email": "ulidcheck@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))
        ulid = create_res.json()["ulid"]

        res = client.get(f"/api/users?ulid={ulid}", headers=auth_header(viewer_token))
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        user = data["users"][0]
        assert user["ulid"] == ulid
        assert "display_id" in user
        assert user["display_id"].startswith("EMP-")


class TestGetUser:
    """Test user retrieval by ULID."""

    def test_get_by_ulid(self, client, superadmin_token, viewer_token):
        create_res = client.post("/api/users", json={
            "name": "Get Me User",
            "email": "getme@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))
        ulid = create_res.json()["ulid"]

        res = client.get(f"/api/users/{ulid}", headers=auth_header(viewer_token))
        assert res.status_code == 200
        data = res.json()
        assert data["ulid"] == ulid
        assert data["name"] == "Get Me User"
        assert data["display_id"].startswith("EMP-")

    def test_get_nonexistent(self, client, viewer_token):
        res = client.get("/api/users/01NONEXISTENT00000000000000", headers=auth_header(viewer_token))
        assert res.status_code == 404


class TestUpdateUser:
    """Test user update by ULID."""

    def test_update_name(self, client, superadmin_token):
        create_res = client.post("/api/users", json={
            "name": "Old Name",
            "email": "update@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))
        ulid = create_res.json()["ulid"]

        res = client.put(f"/api/users/{ulid}", json={
            "name": "New Name",
        }, headers=auth_header(superadmin_token))

        assert res.status_code == 200
        assert res.json()["name"] == "New Name"
        # ULID must not change
        assert res.json()["ulid"] == ulid
