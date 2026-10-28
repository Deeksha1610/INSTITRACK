from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.case import CaseStatus, CasePriority, CaseCategory
from app.schemas.user import UserBrief
from app.schemas.institution import InstitutionOut


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=20)
    category: CaseCategory
    institution_id: int
    incident_date: Optional[datetime] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class CaseAccept(BaseModel):
    notes: Optional[str] = None


class CaseReject(BaseModel):
    reason: str = Field(..., min_length=5)


class CaseRequestInfo(BaseModel):
    information_request: str = Field(..., min_length=5)


class CaseComplainantResponse(BaseModel):
    response: str = Field(..., min_length=5)


class CaseAssign(BaseModel):
    bureau_id: int
    officer_id: Optional[int] = None
    priority: CasePriority = CasePriority.MEDIUM
    deadline: Optional[datetime] = None
    notes: Optional[str] = None


class CaseStatusUpdate(BaseModel):
    status: CaseStatus
    remarks: Optional[str] = None


class CaseResolution(BaseModel):
    resolution_summary: str = Field(..., min_length=10)


class CaseClosure(BaseModel):
    approve: bool
    remarks: Optional[str] = None


class CaseHistoryOut(BaseModel):
    id: int
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    actor: Optional[UserBrief] = None

    class Config:
        from_attributes = True


class CaseAssignmentOut(BaseModel):
    id: int
    bureau_id: int
    officer_id: Optional[int] = None
    assigned_by_id: int
    priority: CasePriority
    notes: Optional[str] = None
    deadline: Optional[datetime] = None
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    is_current: bool
    reassignment_reason: Optional[str] = None
    created_at: datetime
    bureau_name: Optional[str] = None
    officer_name: Optional[str] = None

    class Config:
        from_attributes = True


class CaseCommentOut(BaseModel):
    id: int
    content: str
    is_internal: bool
    created_at: datetime
    author: Optional[UserBrief] = None

    class Config:
        from_attributes = True


class AttachmentOut(BaseModel):
    id: int
    original_filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    is_evidence: bool
    is_public_to_complainant: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RelatedCaseOut(BaseModel):
    id: int
    target_case_id: int
    target_case_public_id: Optional[str] = None
    target_title: Optional[str] = None
    similarity_score: Optional[float] = None
    confirmed: bool
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CoordinationRequestCreate(BaseModel):
    case_id: int
    to_bureau_id: int
    reason: str = Field(..., min_length=5)
    requested_action: Optional[str] = None
    response_deadline: Optional[datetime] = None


class CoordinationRequestRespond(BaseModel):
    response: str = Field(..., min_length=5)
    mark_completed: bool = False


class CoordinationRequestOut(BaseModel):
    id: int
    case_id: int
    case_public_id: Optional[str] = None
    from_bureau_id: int
    to_bureau_id: int
    from_bureau_name: Optional[str] = None
    to_bureau_name: Optional[str] = None
    reason: str
    requested_action: Optional[str] = None
    response: Optional[str] = None
    status: str
    response_deadline: Optional[datetime] = None
    created_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseOut(BaseModel):
    id: int
    case_id: str
    tracking_ref: str
    title: str
    description: str
    category: CaseCategory
    status: CaseStatus
    priority: CasePriority
    institution_id: int
    complainant_id: int
    assigned_bureau_id: Optional[int] = None
    assigned_officer_id: Optional[int] = None
    incident_date: Optional[datetime] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    deadline: Optional[datetime] = None
    is_overdue: bool
    resolution_summary: Optional[str] = None
    rejection_reason: Optional[str] = None
    information_request: Optional[str] = None
    complainant_response: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    institution: Optional[InstitutionOut] = None
    complainant: Optional[UserBrief] = None
    assigned_officer: Optional[UserBrief] = None
    assigned_bureau_name: Optional[str] = None

    class Config:
        from_attributes = True


class CaseDetail(CaseOut):
    history: List[CaseHistoryOut] = []
    assignments: List[CaseAssignmentOut] = []
    comments: List[CaseCommentOut] = []
    attachments: List[AttachmentOut] = []
    related_cases: List[RelatedCaseOut] = []
    coordination_requests: List[CoordinationRequestOut] = []


class CaseListItem(BaseModel):
    id: int
    case_id: str
    title: str
    category: CaseCategory
    status: CaseStatus
    priority: CasePriority
    institution_name: Optional[str] = None
    institution_id_str: Optional[str] = None
    assigned_bureau_name: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    is_overdue: bool
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_cases: int = 0
    new_awaiting_review: int = 0
    accepted_unassigned: int = 0
    assigned_in_progress: int = 0
    needs_information: int = 0
    overdue: int = 0
    resolved_closed: int = 0
    pending_coordination: int = 0
    my_assigned: int = 0
    awaiting_acknowledgement: int = 0
    returned: int = 0
    resolution_pending_review: int = 0
    total_users: int = 0
    total_institutions: int = 0
    total_bureaus: int = 0


class BureauOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: Optional[str] = None
    case_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime
    user: Optional[UserBrief] = None

    class Config:
        from_attributes = True
