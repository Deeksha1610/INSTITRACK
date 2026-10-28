import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class RoleEnum(str, enum.Enum):
    COMPLAINANT = "complainant"
    SUPER_ADMIN = "super_admin"
    CENTRAL_MONITORING = "central_monitoring"
    BUREAU_OFFICER = "bureau_officer"
    AUDITOR = "auditor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.COMPLAINANT)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    bureau_id = Column(Integer, ForeignKey("bureaus.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    bureau = relationship("Bureau", back_populates="officers", foreign_keys=[bureau_id])
    assigned_cases = relationship("Case", back_populates="assigned_officer", foreign_keys="Case.assigned_officer_id")
    created_cases = relationship("Case", back_populates="complainant", foreign_keys="Case.complainant_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
