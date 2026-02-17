"""
PRISMID ULID Generation Engine

Generates ULID-based identifiers for users.

- ULID is the single source of truth identifier (26 characters, Crockford Base32).
- ULID is role-agnostic — intern vs employee is a separate attribute.
- ULID is immutable — never changes, even on promotion.
- Display ID is derived deterministically from the ULID for human readability.
"""

import re
from ulid import ULID
from sqlalchemy.orm import Session


# Crockford Base32 alphabet used by ULID
CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_ulid(db: Session) -> str:
    """
    Generate a unique ULID.

    Returns:
        26-character uppercase Crockford Base32 string.
    """
    from app.models.user import User  # Lazy import to avoid circular

    max_attempts = 100
    for attempt in range(max_attempts):
        ulid_value = str(ULID()).upper()

        # Validate uniqueness
        existing = db.query(User.id).filter(User.ulid == ulid_value).first()
        if not existing:
            return ulid_value

    raise RuntimeError("Failed to generate unique ULID after 100 attempts")


def validate_ulid(ulid_str: str) -> bool:
    """Validate that a string is a well-formed 26-character ULID."""
    if not ulid_str or len(ulid_str) != 26:
        return False
    return all(c in CROCKFORD_BASE32 for c in ulid_str.upper())


def ulid_to_display_id(ulid_str: str, category: str | None = None) -> str:
    """
    Derive a human-friendly display ID from a ULID.

    Takes the last 10 characters and formats as XXXX-XXXX-XX.
    Optionally prefixes with role indicator:
        INTERN   → INT-XXXX-XXXX-XX
        EMPLOYEE → EMP-XXXX-XXXX-XX

    Args:
        ulid_str: The full 26-character ULID.
        category: Optional 'INTERN' or 'EMPLOYEE' for display prefix.

    Returns:
        Formatted display ID string.
    """
    suffix = ulid_str[-10:].upper()
    formatted = f"{suffix[:4]}-{suffix[4:8]}-{suffix[8:10]}"

    if category and category.upper() == "INTERN":
        return f"INT-{formatted}"

    return formatted


def display_id_to_ulid_suffix(display_id: str) -> str:
    """
    Extract the 10-character ULID suffix from a display ID.

    Strips 'INT-' prefix and dashes.
    """
    # Strip role prefix if present
    cleaned = display_id.upper().strip()
    if cleaned.startswith("INT-"):
        cleaned = cleaned[4:]
    # Also handle legacy EMP- if present, just in case
    elif cleaned.startswith("EMP-"):
        cleaned = cleaned[4:]

    # Remove dashes
    cleaned = cleaned.replace("-", "")

    if len(cleaned) != 10:
        raise ValueError(f"Invalid display ID format: '{display_id}' (extracted '{cleaned}', expected 10 chars)")

    return cleaned


def is_display_id_format(value: str) -> bool:
    """
    Check if a string looks like a display ID (with or without prefix).

    Patterns matched:
        XXXX-XXXX-XX
        INT-XXXX-XXXX-XX
        (Legacy EMP- supported for robustness)
    """
    pattern = r'^(?:(?:INT|EMP)-)?\w{4}-\w{4}-\w{2}$'
    return bool(re.match(pattern, value.upper().strip()))


def generate_batch_ulids(db: Session, count: int) -> list[str]:
    """Generate multiple unique ULIDs in one call."""
    return [generate_ulid(db) for _ in range(count)]
