"""SQLAlchemy models for users and internship tracking."""

import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, Date,
    ForeignKey, Text, Boolean, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserCategory(str, enum.Enum):
    INTERN = "INTERN"
    EMPLOYEE = "EMPLOYEE"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ulid = Column(String(26), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(Enum(UserCategory), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    division_id = Column(Integer, ForeignKey("divisions.id"), nullable=True)
    conversion_date = Column(DateTime, nullable=True)
    date_of_joining = Column(Date, nullable=False, default=date.today)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    end_date = Column(Date, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    domain = relationship("Domain", back_populates="users")
    division = relationship("Division", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    internship = relationship("InternshipTracking", back_populates="user", uselist=False)

    __table_args__ = (
        Index("ix_users_category_status", "category", "status"),
        Index("ix_users_name_search", "name"),
        Index("ix_users_ulid_suffix", "ulid"),  # For display ID suffix lookups
    )

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and self.deleted_at is None


class InternshipStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    EXTENDED = "EXTENDED"
    CONVERTED = "CONVERTED"


class InternshipTracking(Base):
    __tablename__ = "internship_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    extended_count = Column(Integer, default=0)
    override_reason = Column(Text, nullable=True)
    status = Column(Enum(InternshipStatus), default=InternshipStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="internship")

    __table_args__ = (
        Index("ix_internship_end_date", "end_date"),
        Index("ix_internship_status", "status"),
    )
