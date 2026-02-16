"""
Permission decorators and access level enforcement.
"""

from functools import wraps
from fastapi import HTTPException, status
from app.models.admin import AccessLevel


# Access level hierarchy (higher value = more privileges)
ACCESS_HIERARCHY = {
    AccessLevel.VIEWER: 1,
    AccessLevel.ADMIN: 2,
    AccessLevel.SUPERADMIN: 3,
}


def check_access_level(required: AccessLevel, current: AccessLevel) -> bool:
    """Check if current access level meets the required level."""
    return ACCESS_HIERARCHY.get(current, 0) >= ACCESS_HIERARCHY.get(required, 99)


def require_level(required_level: AccessLevel):
    """
    Decorator for API endpoint permission checking.
    Must be used on functions that receive `current_admin` parameter.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_admin = kwargs.get("current_admin")
            if current_admin is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            if not check_access_level(required_level, current_admin.access_level):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_level.value} access or higher",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
