import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc
from fastapi import HTTPException, status

from app.models.case import (
    Case, CaseStatus, CasePriority, CaseCategory, CaseAssignment,
    CaseHistory, CaseComment, Attachment, RelatedCase, CoordinationRequest,
    Notification, AuditLog, DeadlineRule, CategoryBureauRule
)
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.bureau import Bureau
from app.schemas.case import CaseCreate, CaseAssign
from app.core.config import settings


# Valid status transitions: (from_status, to_status) -> allowed roles
VALID_TRANSITIONS = {
    (CaseStatus.SUBMITTED, CaseStatus.UNDER_REVIEW): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.SUBMITTED, CaseStatus.ACCEPTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.SUBMITTED, CaseStatus.REJECTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.SUBMITTED, CaseStatus.NEEDS_INFORMATION): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.UNDER_REVIEW, CaseStatus.ACCEPTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.UNDER_REVIEW, CaseStatus.REJECTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.UNDER_REVIEW, CaseStatus.NEEDS_INFORMATION): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.ACCEPTED, CaseStatus.ASSIGNED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.ACCEPTED, CaseStatus.REJECTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS): [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.ASSIGNED, CaseStatus.RETURNED): [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.IN_PROGRESS, CaseStatus.NEEDS_INFORMATION): [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.IN_PROGRESS, CaseStatus.RESOLUTION_SUBMITTED): [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.IN_PROGRESS, CaseStatus.ESCALATED): [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.NEEDS_INFORMATION, CaseStatus.UNDER_REVIEW): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.NEEDS_INFORMATION, CaseStatus.IN_PROGRESS): [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.NEEDS_INFORMATION, CaseStatus.ACCEPTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.RETURNED, CaseStatus.ASSIGNED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.RETURNED, CaseStatus.ACCEPTED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.RESOLUTION_SUBMITTED, CaseStatus.CLOSED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.RESOLUTION_SUBMITTED, CaseStatus.IN_PROGRESS): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.ESCALATED, CaseStatus.ASSIGNED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.ESCALATED, CaseStatus.IN_PROGRESS): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.CLOSED, CaseStatus.REOPENED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.REOPENED, CaseStatus.ASSIGNED): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN],
    (CaseStatus.REOPENED, CaseStatus.IN_PROGRESS): [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN, RoleEnum.BUREAU_OFFICER],
}


def generate_case_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(func.count(Case.id)).scalar() or 0
    return f"INST-{year}-{count + 1:05d}"


def generate_tracking_ref() -> str:
    return uuid.uuid4().hex


def add_history(
    db: Session,
    case: Case,
    actor: Optional[User],
    action: str,
    from_status: Optional[str] = None,
    to_status: Optional[str] = None,
    remarks: Optional[str] = None,
):
    entry = CaseHistory(
        case_id=case.id,
        actor_id=actor.id if actor else None,
        action=action,
        from_status=from_status,
        to_status=to_status,
        remarks=remarks,
    )
    db.add(entry)


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    case_id: Optional[int] = None,
):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        case_id=case_id,
    )
    db.add(notif)


def log_audit(
    db: Session,
    user: Optional[User],
    action: str,
    entity_type: str = None,
    entity_id: str = None,
    details: str = None,
):
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)


def compute_deadline(db: Session, category: CaseCategory, priority: CasePriority) -> Optional[datetime]:
    rule = (
        db.query(DeadlineRule)
        .filter(
            DeadlineRule.is_active == True,
            or_(
                and_(DeadlineRule.category == category, DeadlineRule.priority == priority),
                and_(DeadlineRule.category == category, DeadlineRule.priority == None),
                and_(DeadlineRule.category == None, DeadlineRule.priority == priority),
            ),
        )
        .order_by(DeadlineRule.category.desc().nullslast(), DeadlineRule.priority.desc().nullslast())
        .first()
    )
    days = rule.days_to_resolve if rule else 30
    return datetime.now(timezone.utc) + timedelta(days=days)


def create_case(db: Session, data: CaseCreate, complainant: User) -> Case:
    institution = db.query(Institution).filter(Institution.id == data.institution_id, Institution.is_active == True).first()
    if not institution:
        raise HTTPException(status_code=400, detail="Invalid or inactive institution")

    case_id = generate_case_id(db)
    tracking_ref = generate_tracking_ref()
    deadline = compute_deadline(db, data.category, CasePriority.MEDIUM)

    case = Case(
        case_id=case_id,
        tracking_ref=tracking_ref,
        title=data.title,
        description=data.description,
        category=data.category,
        status=CaseStatus.SUBMITTED,
        priority=CasePriority.MEDIUM,
        institution_id=data.institution_id,
        complainant_id=complainant.id,
        incident_date=data.incident_date,
        contact_phone=data.contact_phone or complainant.phone,
        contact_email=data.contact_email or complainant.email,
        deadline=deadline,
    )
    db.add(case)
    db.flush()

    add_history(db, case, complainant, "CASE_SUBMITTED", None, CaseStatus.SUBMITTED.value, "Complaint submitted by complainant")
    log_audit(db, complainant, "CASE_CREATED", "case", case.case_id, f"Title: {case.title}")

    # Notify central monitoring officers
    monitors = db.query(User).filter(
        User.role.in_([RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]),
        User.is_active == True,
    ).all()
    for m in monitors:
        create_notification(
            db, m.id,
            "New Complaint Submitted",
            f"Case {case.case_id}: {case.title} from {institution.name}",
            "new_case",
            case.id,
        )

    db.commit()
    db.refresh(case)
    return case


def can_transition(current: CaseStatus, new_status: CaseStatus, role: RoleEnum) -> bool:
    allowed = VALID_TRANSITIONS.get((current, new_status), [])
    return role in allowed


def accept_case(db: Session, case: Case, user: User, notes: Optional[str] = None) -> Case:
    if case.status not in [CaseStatus.SUBMITTED, CaseStatus.UNDER_REVIEW, CaseStatus.NEEDS_INFORMATION]:
        raise HTTPException(status_code=400, detail=f"Cannot accept case in status {case.status}")
    if user.role not in [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to accept cases")

    old = case.status
    case.status = CaseStatus.ACCEPTED
    case.version += 1
    add_history(db, case, user, "CASE_ACCEPTED", old.value, CaseStatus.ACCEPTED.value, notes)
    create_notification(db, case.complainant_id, "Case Accepted", f"Your case {case.case_id} has been accepted for processing.", "status", case.id)
    log_audit(db, user, "CASE_ACCEPTED", "case", case.case_id)
    db.commit()
    db.refresh(case)
    return case


def reject_case(db: Session, case: Case, user: User, reason: str) -> Case:
    if case.status not in [CaseStatus.SUBMITTED, CaseStatus.UNDER_REVIEW, CaseStatus.ACCEPTED]:
        raise HTTPException(status_code=400, detail=f"Cannot reject case in status {case.status}")
    if user.role not in [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    old = case.status
    case.status = CaseStatus.REJECTED
    case.rejection_reason = reason
    case.version += 1
    case.closed_at = datetime.now(timezone.utc)
    add_history(db, case, user, "CASE_REJECTED", old.value, CaseStatus.REJECTED.value, reason)
    create_notification(db, case.complainant_id, "Case Rejected", f"Your case {case.case_id} was rejected. Reason: {reason}", "status", case.id)
    log_audit(db, user, "CASE_REJECTED", "case", case.case_id, reason)
    db.commit()
    db.refresh(case)
    return case


def request_information(db: Session, case: Case, user: User, request_text: str) -> Case:
    if user.role not in [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN, RoleEnum.BUREAU_OFFICER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    old = case.status
    case.status = CaseStatus.NEEDS_INFORMATION
    case.information_request = request_text
    case.version += 1
    add_history(db, case, user, "INFORMATION_REQUESTED", old.value, CaseStatus.NEEDS_INFORMATION.value, request_text)
    create_notification(db, case.complainant_id, "Additional Information Required", f"Case {case.case_id}: {request_text}", "info_request", case.id)
    log_audit(db, user, "INFO_REQUESTED", "case", case.case_id)
    db.commit()
    db.refresh(case)
    return case


def assign_case(db: Session, case: Case, user: User, data: CaseAssign) -> Case:
    if user.role not in [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to assign cases")
    if case.status not in [CaseStatus.ACCEPTED, CaseStatus.RETURNED, CaseStatus.REOPENED, CaseStatus.ESCALATED]:
        raise HTTPException(status_code=400, detail=f"Cannot assign case in status {case.status}")

    bureau = db.query(Bureau).filter(Bureau.id == data.bureau_id, Bureau.is_active == True).first()
    if not bureau:
        raise HTTPException(status_code=400, detail="Invalid bureau")

    officer = None
    if data.officer_id:
        officer = db.query(User).filter(
            User.id == data.officer_id,
            User.role == RoleEnum.BUREAU_OFFICER,
            User.is_active == True,
        ).first()
        if not officer:
            raise HTTPException(status_code=400, detail="Invalid officer")

    # Mark previous assignments as not current
    db.query(CaseAssignment).filter(CaseAssignment.case_id == case.id, CaseAssignment.is_current == True).update({"is_current": False})

    assignment = CaseAssignment(
        case_id=case.id,
        bureau_id=data.bureau_id,
        officer_id=data.officer_id,
        assigned_by_id=user.id,
        priority=data.priority,
        notes=data.notes,
        deadline=data.deadline or case.deadline,
        is_current=True,
    )
    db.add(assignment)

    old = case.status
    case.status = CaseStatus.ASSIGNED
    case.assigned_bureau_id = data.bureau_id
    case.assigned_officer_id = data.officer_id
    case.priority = data.priority
    if data.deadline:
        case.deadline = data.deadline
    case.version += 1

    add_history(db, case, user, "CASE_ASSIGNED", old.value, CaseStatus.ASSIGNED.value, f"Assigned to {bureau.name}" + (f" / {officer.full_name}" if officer else "") + (f". Notes: {data.notes}" if data.notes else ""))
    log_audit(db, user, "CASE_ASSIGNED", "case", case.case_id, f"Bureau: {bureau.code}")

    if officer:
        create_notification(db, officer.id, "New Case Assigned", f"Case {case.case_id} has been assigned to you.", "assignment", case.id)
    # Notify other officers in bureau if no specific officer
    else:
        officers = db.query(User).filter(User.bureau_id == data.bureau_id, User.role == RoleEnum.BUREAU_OFFICER, User.is_active == True).all()
        for o in officers:
            create_notification(db, o.id, "New Case for Bureau", f"Case {case.case_id} assigned to your bureau ({bureau.name}).", "assignment", case.id)

    create_notification(db, case.complainant_id, "Case Assigned", f"Your case {case.case_id} has been assigned for investigation.", "status", case.id)

    db.commit()
    db.refresh(case)
    return case


def acknowledge_assignment(db: Session, case: Case, user: User) -> Case:
    if user.role != RoleEnum.BUREAU_OFFICER and user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only bureau officers can acknowledge")
    if case.assigned_officer_id and case.assigned_officer_id != user.id and user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="This case is not assigned to you")
    if case.assigned_bureau_id and user.bureau_id and case.assigned_bureau_id != user.bureau_id and user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Case not in your bureau")

    assignment = (
        db.query(CaseAssignment)
        .filter(CaseAssignment.case_id == case.id, CaseAssignment.is_current == True)
        .first()
    )
    if assignment and not assignment.acknowledged:
        assignment.acknowledged = True
        assignment.acknowledged_at = datetime.now(timezone.utc)
        if not case.assigned_officer_id:
            case.assigned_officer_id = user.id
            assignment.officer_id = user.id

    old = case.status
    if case.status == CaseStatus.ASSIGNED:
        case.status = CaseStatus.IN_PROGRESS
        case.version += 1
        add_history(db, case, user, "ASSIGNMENT_ACKNOWLEDGED", old.value, CaseStatus.IN_PROGRESS.value, "Officer acknowledged assignment")
    else:
        add_history(db, case, user, "ASSIGNMENT_ACKNOWLEDGED", old.value, old.value, "Officer acknowledged assignment")

    log_audit(db, user, "ASSIGNMENT_ACKNOWLEDGED", "case", case.case_id)
    db.commit()
    db.refresh(case)
    return case


def update_status(db: Session, case: Case, user: User, new_status: CaseStatus, remarks: Optional[str] = None) -> Case:
    if not can_transition(case.status, new_status, user.role):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {case.status} to {new_status} for role {user.role}",
        )

    # Bureau officer can only act on their cases
    if user.role == RoleEnum.BUREAU_OFFICER:
        if case.assigned_officer_id and case.assigned_officer_id != user.id:
            raise HTTPException(status_code=403, detail="Case not assigned to you")
        if case.assigned_bureau_id and user.bureau_id and case.assigned_bureau_id != user.bureau_id:
            raise HTTPException(status_code=403, detail="Case not in your bureau")

    old = case.status
    case.status = new_status
    case.version += 1
    if new_status == CaseStatus.CLOSED:
        case.closed_at = datetime.now(timezone.utc)

    add_history(db, case, user, "STATUS_UPDATED", old.value, new_status.value, remarks)
    create_notification(db, case.complainant_id, "Case Status Updated", f"Case {case.case_id} is now {new_status.value}", "status", case.id)
    log_audit(db, user, "STATUS_UPDATED", "case", case.case_id, f"{old.value} -> {new_status.value}")
    db.commit()
    db.refresh(case)
    return case


def submit_resolution(db: Session, case: Case, user: User, summary: str) -> Case:
    if user.role not in [RoleEnum.BUREAU_OFFICER, RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if case.status not in [CaseStatus.IN_PROGRESS, CaseStatus.ASSIGNED, CaseStatus.ESCALATED]:
        raise HTTPException(status_code=400, detail=f"Cannot submit resolution from status {case.status}")

    if user.role == RoleEnum.BUREAU_OFFICER:
        if case.assigned_officer_id and case.assigned_officer_id != user.id:
            raise HTTPException(status_code=403, detail="Case not assigned to you")

    old = case.status
    case.status = CaseStatus.RESOLUTION_SUBMITTED
    case.resolution_summary = summary
    case.version += 1
    add_history(db, case, user, "RESOLUTION_SUBMITTED", old.value, CaseStatus.RESOLUTION_SUBMITTED.value, summary)
    create_notification(db, case.complainant_id, "Resolution Submitted", f"A resolution has been submitted for case {case.case_id}.", "resolution", case.id)

    monitors = db.query(User).filter(User.role.in_([RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]), User.is_active == True).all()
    for m in monitors:
        create_notification(db, m.id, "Resolution Awaiting Review", f"Case {case.case_id} resolution submitted for approval.", "resolution", case.id)

    log_audit(db, user, "RESOLUTION_SUBMITTED", "case", case.case_id)
    db.commit()
    db.refresh(case)
    return case


def approve_closure(db: Session, case: Case, user: User, approve: bool, remarks: Optional[str] = None) -> Case:
    if user.role not in [RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to approve closure")
    if case.status != CaseStatus.RESOLUTION_SUBMITTED:
        raise HTTPException(status_code=400, detail="Case must be in RESOLUTION_SUBMITTED status")

    old = case.status
    if approve:
        case.status = CaseStatus.CLOSED
        case.closed_at = datetime.now(timezone.utc)
        case.version += 1
        add_history(db, case, user, "CLOSURE_APPROVED", old.value, CaseStatus.CLOSED.value, remarks or "Closure approved")
        create_notification(db, case.complainant_id, "Case Closed", f"Your case {case.case_id} has been closed. {remarks or ''}", "closure", case.id)
        if case.assigned_officer_id:
            create_notification(db, case.assigned_officer_id, "Case Closed", f"Case {case.case_id} has been closed.", "closure", case.id)
        log_audit(db, user, "CLOSURE_APPROVED", "case", case.case_id)
    else:
        case.status = CaseStatus.IN_PROGRESS
        case.version += 1
        add_history(db, case, user, "RESOLUTION_RETURNED", old.value, CaseStatus.IN_PROGRESS.value, remarks or "Resolution returned for rework")
        if case.assigned_officer_id:
            create_notification(db, case.assigned_officer_id, "Resolution Returned", f"Case {case.case_id} resolution returned. {remarks or ''}", "rework", case.id)
        log_audit(db, user, "RESOLUTION_RETURNED", "case", case.case_id, remarks)

    db.commit()
    db.refresh(case)
    return case


def check_case_access(case: Case, user: User) -> bool:
    if user.role in [RoleEnum.SUPER_ADMIN, RoleEnum.CENTRAL_MONITORING, RoleEnum.AUDITOR]:
        return True
    if user.role == RoleEnum.COMPLAINANT:
        return case.complainant_id == user.id
    if user.role == RoleEnum.BUREAU_OFFICER:
        if case.assigned_officer_id == user.id:
            return True
        if case.assigned_bureau_id and user.bureau_id and case.assigned_bureau_id == user.bureau_id:
            return True
        return False
    return False
