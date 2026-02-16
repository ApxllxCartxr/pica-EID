"""Tests for intern lifecycle: conversion and extension with ULID immutability."""

import pytest
from datetime import date, timedelta
from tests.conftest import auth_header


def _create_intern(client, superadmin_token, suffix=""):
    """Helper: create an intern and return the response JSON."""
    today = date.today()
    res = client.post("/api/users", json={
        "name": f"Test Intern{suffix}",
        "email": f"intern{suffix}@prismid.com",
        "category": "INTERN",
        "start_date": str(today),
        "end_date": str(today + timedelta(days=90)),
    }, headers=auth_header(superadmin_token))
    assert res.status_code == 201
    return res.json()


class TestConvertIntern:
    """Tests for intern → employee conversion with ULID immutability."""

    def test_convert_keeps_same_ulid(self, client, superadmin_token):
        """Critical: ULID must remain identical after conversion."""
        intern = _create_intern(client, superadmin_token, "_convert1")
        original_ulid = intern["ulid"]
        assert intern["display_id"].startswith("INT-")

        res = client.post(
            f"/api/users/{original_ulid}/convert",
            json={"migrate_roles": True},
            headers=auth_header(superadmin_token),
        )
        assert res.status_code == 200
        converted = res.json()

        # ULID is IMMUTABLE
        assert converted["ulid"] == original_ulid
        # Category changes
        assert converted["category"] == "EMPLOYEE"
        # Display prefix changes
        assert converted["display_id"].startswith("EMP-")
        # Status is active
        assert converted["status"] == "ACTIVE"

    def test_display_id_suffix_stable_across_conversion(self, client, superadmin_token):
        """The display ID suffix (XXXX-XXXX-XX) must be identical before and after conversion."""
        intern = _create_intern(client, superadmin_token, "_convert2")
        intern_suffix = intern["display_id"][4:]  # After "INT-"

        res = client.post(
            f"/api/users/{intern['ulid']}/convert",
            json={"migrate_roles": True},
            headers=auth_header(superadmin_token),
        )
        emp_suffix = res.json()["display_id"][4:]  # After "EMP-"
        assert intern_suffix == emp_suffix

    def test_cannot_convert_employee(self, client, superadmin_token):
        res = client.post("/api/users", json={
            "name": "Employee Test",
            "email": "employee_noconvert@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))
        ulid = res.json()["ulid"]

        res = client.post(
            f"/api/users/{ulid}/convert",
            json={"migrate_roles": True},
            headers=auth_header(superadmin_token),
        )
        assert res.status_code == 400

    def test_convert_requires_superadmin(self, client, superadmin_token, viewer_token):
        intern = _create_intern(client, superadmin_token, "_convert3")

        res = client.post(
            f"/api/users/{intern['ulid']}/convert",
            json={"migrate_roles": True},
            headers=auth_header(viewer_token),
        )
        assert res.status_code == 403


class TestExtendInternship:
    """Tests for intern extension."""

    def test_extend_internship(self, client, superadmin_token):
        intern = _create_intern(client, superadmin_token, "_extend1")
        original_end = intern["end_date"]
        new_end = str(date.fromisoformat(original_end) + timedelta(days=30))

        res = client.post(
            f"/api/users/{intern['ulid']}/extend",
            json={"new_end_date": new_end, "reason": "Extension for project completion"},
            headers=auth_header(superadmin_token),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["end_date"] == new_end
        # ULID unchanged
        assert data["ulid"] == intern["ulid"]

    def test_cannot_extend_employee(self, client, superadmin_token):
        res = client.post("/api/users", json={
            "name": "Not An Intern",
            "email": "notintern_extend@prismid.com",
            "category": "EMPLOYEE",
        }, headers=auth_header(superadmin_token))
        ulid = res.json()["ulid"]

        res = client.post(
            f"/api/users/{ulid}/extend",
            json={"new_end_date": "2026-12-31", "reason": "Should fail"},
            headers=auth_header(superadmin_token),
        )
        assert res.status_code == 400

    def test_extend_requires_superadmin(self, client, superadmin_token, viewer_token):
        intern = _create_intern(client, superadmin_token, "_extend2")
        new_end = str(date.fromisoformat(intern["end_date"]) + timedelta(days=30))

        res = client.post(
            f"/api/users/{intern['ulid']}/extend",
            json={"new_end_date": new_end, "reason": "Should be denied"},
            headers=auth_header(viewer_token),
        )
        assert res.status_code == 403
