import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey,
    Float, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class CaseStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"
    RESOLUTION_SUBMITTED = "RESOLUTION_SUBMITTED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseCategory(str, enum.Enum):
    ACADEMIC_EXAM = "Academic / Examination Issues"
    ADMISSION = "Admission-related Issues"
    FACILITIES = "Institutional Facilities"
    FEE = "Fee-related Issues"
    FACULTY_STAFF = "Faculty / Staff Issues"
    STUDENT_GRIEVANCE = "Student Grievances"
    INFRASTRUCTURE = "Infrastructure Issues"
    REGULATORY = "Regulatory / Compliance Concerns"
    OTHER = "Other"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(30), unique=True, index=True, nullable=False)  # e.g. INST-2026-00001
    tracking_ref = Column(String(64), unique=True, index=True, nullable=False)  # non-guessable
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(CaseCategory), nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.SUBMITTED, index=True)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM)

    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    complainant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_bureau_id = Column(Integer, ForeignKey("bureaus.id"), nullable=True, index=True)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    incident_date = Column(DateTime, nullable=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)

    deadline = Column(DateTime, nullable=True)
    target_resolution_date = Column(DateTime, nullable=True)
    is_overdue = Column(Boolean, default=False)

    resolution_summary = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    information_request = Column(Text, nullable=True)
    complainant_response = Column(Text, nullable=True)

    version = Column(Integer, default=1)  # optimistic concurrency

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    institution = relationship("Institution", back_populates="cases")
    complainant = relationship("User", back_populates="created_cases", foreign_keys=[complainant_id])
    assigned_bureau = relationship("Bureau", back_populates="cases", foreign_keys=[assigned_bureau_id])
    assigned_officer = relationship("User", back_populates="assigned_cases", foreign_keys=[assigned_officer_id])

    assignments = relationship("CaseAssignment", back_populates="case", cascade="all, delete-orphan", order_by="CaseAssignment.created_at")
    history = relationship("CaseHistory", back_populates="case", cascade="all, delete-orphan", order_by="CaseHistory.created_at")
    comments = relationship("CaseComment", back_populates="case", cascade="all, delete-orphan", order_by="CaseComment.created_at")
    attachments = relationship("Attachment", back_populates="case", cascade="all, delete-orphan")
    related_from = relationship("RelatedCase", back_populates="source_case", foreign_keys="RelatedCase.source_case_id", cascade="all, delete-orphan")
    related_to = relationship("RelatedCase", back_populates="target_case", foreign_keys="RelatedCase.target_case_id", cascade="all, delete-orphan")
    coordination_requests = relationship("CoordinationRequest", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Case {self.case_id} [{self.status}]>"


class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    bureau_id = Column(Integer, ForeignKey("bureaus.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM)
    notes = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)
    reassignment_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="assignments")
    bureau = relationship("Bureau")
    officer = relationship("User", foreign_keys=[officer_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class CaseHistory(Base):
    __tablename__ = "case_history"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    case = relationship("Case", back_populates="history")
    actor = relationship("User")


class CaseComment(Base):
    __tablename__ = "case_comments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)  # internal remarks not visible to complainant
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="comments")
    author = relationship("User")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=False)
    is_evidence = Column(Boolean, default=False)
    is_public_to_complainant = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="attachments")
    uploaded_by = relationship("User")


class RelatedCase(Base):
    __tablename__ = "related_cases"
    __table_args__ = (UniqueConstraint("source_case_id", "target_case_id", name="uq_related_pair"),)

    id = Column(Integer, primary_key=True, index=True)
    source_case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    target_case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=True)
    confirmed = Column(Boolean, default=False)
    confirmed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    confirmed_at = Column(DateTime, nullable=True)

    source_case = relationship("Case", back_populates="related_from", foreign_keys=[source_case_id])
    target_case = relationship("Case", back_populates="related_to", foreign_keys=[target_case_id])
    confirmed_by = relationship("User")


class CoordinationRequest(Base):
    __tablename__ = "coordination_requests"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    from_bureau_id = Column(Integer, ForeignKey("bureaus.id"), nullable=False)
    to_bureau_id = Column(Integer, ForeignKey("bureaus.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    requested_action = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    responded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default="PENDING")  # PENDING, RESPONDED, COMPLETED
    response_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    case = relationship("Case", back_populates="coordination_requests")
    from_bureau = relationship("Bureau", foreign_keys=[from_bureau_id])
    to_bureau = relationship("Bureau", foreign_keys=[to_bureau_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    responded_by = relationship("User", foreign_keys=[responded_by_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="notifications")
    case = relationship("Case")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="audit_logs")


class DeadlineRule(Base):
    __tablename__ = "deadline_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(Enum(CaseCategory), nullable=True)
    priority = Column(Enum(CasePriority), nullable=True)
    days_to_resolve = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CategoryBureauRule(Base):
    __tablename__ = "category_bureau_rules"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(Enum(CaseCategory), nullable=False, unique=True)
    bureau_id = Column(Integer, ForeignKey("bureaus.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bureau = relationship("Bureau", back_populates="category_rules")
