"""Tests for ULID generation and display ID derivation."""

import pytest
from unittest.mock import MagicMock, patch

from app.core.id_generator import (
    generate_ulid,
    validate_ulid,
    ulid_to_display_id,
    display_id_to_ulid_suffix,
    is_display_id_format,
    CROCKFORD_BASE32,
)


class TestGenerateUlid:
    """Tests for ULID generation."""

    def test_generates_26_char_string(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        ulid_value = generate_ulid(mock_db)
        assert len(ulid_value) == 26

    def test_uppercase_crockford_base32(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        ulid_value = generate_ulid(mock_db)
        assert all(c in CROCKFORD_BASE32 for c in ulid_value)

    def test_unique_across_generations(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        ulids = set()
        for _ in range(1000):
            ulid_value = generate_ulid(mock_db)
            assert ulid_value not in ulids, f"Collision: {ulid_value}"
            ulids.add(ulid_value)

    def test_checks_db_uniqueness(self):
        mock_db = MagicMock()
        # First call returns existing (collision), second returns None (unique)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(),  # Exists
            None,         # Unique
        ]

        ulid_value = generate_ulid(mock_db)
        assert len(ulid_value) == 26
        assert mock_db.query.return_value.filter.return_value.first.call_count == 2

    def test_raises_after_max_attempts(self):
        mock_db = MagicMock()
        # Always return existing
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with pytest.raises(RuntimeError, match="Failed to generate unique ULID"):
            generate_ulid(mock_db)


class TestValidateUlid:
    """Tests for ULID validation."""

    def test_valid_ulid(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        ulid_value = generate_ulid(mock_db)
        assert validate_ulid(ulid_value) is True

    def test_invalid_length(self):
        assert validate_ulid("ABC") is False
        assert validate_ulid("") is False
        assert validate_ulid("A" * 25) is False
        assert validate_ulid("A" * 27) is False

    def test_invalid_characters(self):
        # Crockford Base32 excludes I, L, O, U
        assert validate_ulid("01234567890123456789ABCDI0") is False  # I is invalid
        assert validate_ulid("01234567890123456789ABCDL0") is False  # L is invalid
        assert validate_ulid("01234567890123456789ABCDO0") is False  # O is invalid
        assert validate_ulid("01234567890123456789ABCDU0") is False  # U is invalid

    def test_none_input(self):
        assert validate_ulid(None) is False


class TestDisplayId:
    """Tests for display ID generation."""

    def test_format_without_prefix(self):
        ulid_str = "01J7K3M9R8X2T6V4B1C9D0EFGH"
        display = ulid_to_display_id(ulid_str)
        # Last 10: T6V4B1C9D0 → T6V4-B1C9-D0 (but depends on last 10 chars)
        # Actually last 10 of "01J7K3M9R8X2T6V4B1C9D0EFGH" = "C9D0EFGH" — wait, 26 chars
        # Let me count: 01J7K3M9R8X2T6V4B1C9D0EFGH
        # Last 10: 1C9D0EFGH... let me recount
        assert len(display.replace("-", "")) == 10
        assert display.count("-") == 2
        # Format: XXXX-XXXX-XX
        parts = display.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4
        assert len(parts[1]) == 4
        assert len(parts[2]) == 2

    def test_intern_prefix(self):
        ulid_str = "01J7K3M9R8X2T6V4B1C9D0EFGH"
        display = ulid_to_display_id(ulid_str, "INTERN")
        assert display.startswith("INT-")
        parts = display.split("-")
        assert len(parts) == 4  # INT-XXXX-XXXX-XX

    def test_employee_prefix(self):
        ulid_str = "01J7K3M9R8X2T6V4B1C9D0EFGH"
        display = ulid_to_display_id(ulid_str, "EMPLOYEE")
        assert display.startswith("EMP-")

    def test_deterministic(self):
        ulid_str = "01J7K3M9R8X2T6V4B1C9D0EFGH"
        d1 = ulid_to_display_id(ulid_str, "INTERN")
        d2 = ulid_to_display_id(ulid_str, "INTERN")
        assert d1 == d2

    def test_prefix_changes_on_promotion(self):
        ulid_str = "01J7K3M9R8X2T6V4B1C9D0EFGH"
        intern_display = ulid_to_display_id(ulid_str, "INTERN")
        emp_display = ulid_to_display_id(ulid_str, "EMPLOYEE")

        # Suffix portion should be identical
        intern_suffix = intern_display[4:]  # After INT-
        emp_suffix = emp_display[4:]        # After EMP-
        assert intern_suffix == emp_suffix


class TestDisplayIdResolution:
    """Tests for display ID ↔ ULID suffix round-trip."""

    def test_round_trip(self):
        ulid_str = "01J7K3M9R8X2T6V4B1C9D0EFGH"
        display = ulid_to_display_id(ulid_str, "INTERN")
        suffix = display_id_to_ulid_suffix(display)

        assert len(suffix) == 10
        assert suffix == ulid_str[-10:].upper()

    def test_strip_role_prefix(self):
        suffix_from_intern = display_id_to_ulid_suffix("INT-ABCD-EFGH-12")
        suffix_from_emp = display_id_to_ulid_suffix("EMP-ABCD-EFGH-12")
        suffix_no_prefix = display_id_to_ulid_suffix("ABCD-EFGH-12")

        assert suffix_from_intern == suffix_from_emp == suffix_no_prefix == "ABCDEFGH12"

    def test_invalid_display_id(self):
        with pytest.raises(ValueError, match="Invalid display ID format"):
            display_id_to_ulid_suffix("TOO-SHORT")


class TestIsDisplayIdFormat:
    """Tests for display ID format detection."""

    def test_valid_formats(self):
        assert is_display_id_format("ABCD-EFGH-12") is True
        assert is_display_id_format("INT-ABCD-EFGH-12") is True
        assert is_display_id_format("EMP-ABCD-EFGH-12") is True
        assert is_display_id_format("int-abcd-efgh-12") is True  # Case insensitive

    def test_invalid_formats(self):
        assert is_display_id_format("01J7K3M9R8X2T6V4B1C9D0EFGH") is False  # Full ULID
        assert is_display_id_format("random-string") is False
        assert is_display_id_format("") is False

    def test_does_not_encode_role(self):
        """ULID itself does not encode role/department info."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        ulid_value = generate_ulid(mock_db)
        # Must not start with INT or EMP
        assert not ulid_value.startswith("INT")
        assert not ulid_value.startswith("EMP")
