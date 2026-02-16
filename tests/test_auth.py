"""Tests for authentication endpoints."""

import pytest
from tests.conftest import auth_header


class TestLogin:
    def test_login_success(self, client, superadmin):
        response = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "TestPass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_level"] == "SUPERADMIN"
        assert data["username"] == "testadmin"

    def test_login_wrong_password(self, client, superadmin):
        response = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "WrongPassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "TestPass123",
        })
        assert response.status_code == 401


class TestTokenRefresh:
    def test_refresh_token_success(self, client, superadmin):
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "TestPass123",
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_with_invalid_token(self, client):
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert response.status_code == 401


class TestAdminRegistration:
    def test_superadmin_can_register(self, client, superadmin_token):
        response = client.post("/api/auth/register",
            json={"username": "newadmin", "password": "NewAdmin123", "access_level": "ADMIN"},
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 201

    def test_viewer_cannot_register(self, client, viewer_token):
        response = client.post("/api/auth/register",
            json={"username": "blocked", "password": "Blocked123", "access_level": "VIEWER"},
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403

    def test_duplicate_username_rejected(self, client, superadmin_token, superadmin):
        response = client.post("/api/auth/register",
            json={"username": "testadmin", "password": "Duplicate123"},
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 409
