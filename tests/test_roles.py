"""Tests for role management endpoints."""

import pytest
from tests.conftest import auth_header


class TestRoleCreation:
    def test_superadmin_can_create_role(self, client, superadmin_token):
        response = client.post("/api/roles",
            json={"name": "Test Role", "description": "A test role", "clearance_level": 5},
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Role"
        assert data["clearance_level"] == 5

    def test_viewer_cannot_create_role(self, client, viewer_token):
        response = client.post("/api/roles",
            json={"name": "Blocked Role", "clearance_level": 1},
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403

    def test_duplicate_role_name_rejected(self, client, superadmin_token):
        client.post("/api/roles",
            json={"name": "Unique Role", "clearance_level": 3},
            headers=auth_header(superadmin_token),
        )
        response = client.post("/api/roles",
            json={"name": "Unique Role", "clearance_level": 3},
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 409

    def test_duplicate_role_name_allowed_if_soft_deleted(self, client, superadmin_token):
        # Create Role A
        resp1 = client.post("/api/roles",
            json={"name": "Reuse Role", "clearance_level": 3},
            headers=auth_header(superadmin_token),
        )
        role_id = resp1.json()["id"]

        # Soft delete Role A
        client.delete(f"/api/roles/{role_id}", headers=auth_header(superadmin_token))

        # Create Role A again
        resp2 = client.post("/api/roles",
            json={"name": "Reuse Role", "clearance_level": 3},
            headers=auth_header(superadmin_token),
        )
        assert resp2.status_code == 201
        assert resp2.json()["name"] == "Reuse Role"
        assert resp2.json()["id"] != role_id


class TestRoleUpdate:
    def test_update_role(self, client, superadmin_token):
        create = client.post("/api/roles",
            json={"name": "Editable", "clearance_level": 4},
            headers=auth_header(superadmin_token),
        )
        role_id = create.json()["id"]

        response = client.put(f"/api/roles/{role_id}",
            json={"name": "Edited Role", "clearance_level": 7},
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Edited Role"
        assert response.json()["clearance_level"] == 7


class TestRoleDeletion:
    def test_soft_delete_unassigned_role(self, client, superadmin_token):
        create = client.post("/api/roles",
            json={"name": "Deletable", "clearance_level": 2},
            headers=auth_header(superadmin_token),
        )
        role_id = create.json()["id"]

        response = client.delete(f"/api/roles/{role_id}",
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 200

    def test_cannot_delete_assigned_role(self, client, superadmin_token):
        # Create role
        role_resp = client.post("/api/roles",
            json={"name": "Assigned Role", "clearance_level": 5},
            headers=auth_header(superadmin_token),
        )
        role_id = role_resp.json()["id"]

        # Create user
        user_resp = client.post("/api/users",
            json={"name": "Role User", "email": "roleuser@test.com", "category": "EMPLOYEE"},
            headers=auth_header(superadmin_token),
        )
        uid = user_resp.json()["ulid"]

        # Assign role
        client.post(f"/api/users/{uid}/roles?role_id={role_id}",
            headers=auth_header(superadmin_token),
        )

        # Try to delete — should fail
        response = client.delete(f"/api/roles/{role_id}",
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 400
        assert response.status_code == 400
        assert "active user" in response.json()["detail"].lower()

    def test_can_delete_role_assigned_to_soft_deleted_user(self, client, superadmin_token):
        # Create role
        role_resp = client.post("/api/roles",
            json={"name": "Ghost Role", "clearance_level": 1},
            headers=auth_header(superadmin_token),
        )
        role_id = role_resp.json()["id"]

        # Create user
        user_resp = client.post("/api/users",
            json={"name": "Ghost User", "email": "ghost@test.com", "category": "EMPLOYEE"},
            headers=auth_header(superadmin_token),
        )
        uid = user_resp.json()["ulid"]

        # Assign role
        client.post(f"/api/users/{uid}/roles?role_id={role_id}",
            headers=auth_header(superadmin_token),
        )

        # Soft delete user
        client.delete(f"/api/users/{uid}", headers=auth_header(superadmin_token))

        # Try to delete role - SHOULD SUCCEED
        response = client.delete(f"/api/roles/{role_id}",
            headers=auth_header(superadmin_token),
        )
        assert response.status_code == 200


class TestRoleListing:
    def test_viewer_can_list_roles(self, client, superadmin_token, viewer_token):
        # Create a role
        client.post("/api/roles",
            json={"name": "Listable", "clearance_level": 3},
            headers=auth_header(superadmin_token),
        )
        # Viewer lists
        response = client.get("/api/roles", headers=auth_header(viewer_token))
        assert response.status_code == 200
        assert response.json()["total"] >= 1
