"""SQLAlchemy model for API keys — external application authentication."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)                       # Human label, e.g. "Finance Dashboard"
    key_prefix = Column(String(12), nullable=False, index=True)      # First 8 chars for display / lookup
    key_hash = Column(String(255), nullable=False, unique=True)      # SHA-256 hash of the full key
    scopes = Column(Text, nullable=False, default="*")               # Comma-separated, e.g. "users:read,roles:read"
    owner_id = Column(Integer, ForeignKey("admin_accounts.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)                     # None = never expires
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("AdminAccount", backref="api_keys", lazy="joined")

    @property
    def scopes_list(self) -> list[str]:
        """Return scopes as a list."""
        if not self.scopes or self.scopes == "*":
            return ["*"]
        return [s.strip() for s in self.scopes.split(",") if s.strip()]

    def has_scope(self, required_scope: str) -> bool:
        """Check if this key has the required scope (supports wildcard)."""
        scopes = self.scopes_list
        if "*" in scopes:
            return True
        # Support wildcard within resource, e.g. "users:*"
        resource = required_scope.split(":")[0]
        return required_scope in scopes or f"{resource}:*" in scopes
