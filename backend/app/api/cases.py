from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc
import os
import uuid
import aiofiles

from app.db.session import get_db
from app.core.deps import get_current_user, get_central_monitoring, get_bureau_officer, get_staff, get_auditor
from app.core.config import settings
from app.models.user import User, RoleEnum
from app.models.case import (
    Case, CaseStatus, CasePriority, CaseCategory, CaseAssignment,
    CaseHistory, CaseComment, Attachment, RelatedCase, CoordinationRequest
)
from app.models.bureau import Bureau
from app.schemas.case import (
    CaseCreate, CaseOut, CaseDetail, CaseListItem, CaseAccept, CaseReject,
    CaseRequestInfo, CaseAssign, CaseStatusUpdate, CaseResolution, CaseClosure,
    CaseComplainantResponse, CaseHistoryOut, RelatedCaseOut, CoordinationRequestCreate,
    CoordinationRequestRespond, CoordinationRequestOut, AttachmentOut, CaseCommentOut,
    BureauOut, DashboardSummary, NotificationOut
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.case_service import (
    create_case, accept_case, reject_case, request_information, assign_case,
    acknowledge_assignment, update_status, submit_resolution, approve_closure,
    check_case_access, add_history, create_notification, log_audit
)
from app.ai.similarity import find_related_cases, persist_suggestion

router = APIRouter(prefix="/api/cases", tags=["Cases"])


def _case_to_list_item(case: Case) -> dict:
    return {
        "id": case.id,
        "case_id": case.case_id,
        "title": case.title,
        "category": case.category,
        "status": case.status,
        "priority": case.priority,
        "institution_name": case.institution.name if case.institution else None,
        "institution_id_str": case.institution.institution_id if case.institution else None,
        "assigned_bureau_name": case.assigned_bureau.name if case.assigned_bureau else None,
        "assigned_officer_name": case.assigned_officer.full_name if case.assigned_officer else None,
        "is_overdue": case.is_overdue,
        "deadline": case.deadline,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


@router.post("", response_model=CaseOut)
def submit_complaint(
    data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complainant submits a new complaint."""
    if current_user.role != RoleEnum.COMPLAINANT and current_user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only complainants can submit complaints")
    case = create_case(db, data, current_user)
    # Reload with relationships
    case = db.query(Case).options(
        joinedload(Case.institution), joinedload(Case.complainant)
    ).filter(Case.id == case.id).first()
    return case


@router.get("", response_model=dict)
def list_cases(
    status: Optional[str] = None,
    category: Optional[str] = None,
    institution_id: Optional[int] = None,
    bureau_id: Optional[int] = None,
    officer_id: Optional[int] = None,
    priority: Optional[str] = None,
    overdue: Optional[bool] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Case).options(
        joinedload(Case.institution),
        joinedload(Case.assigned_bureau),
        joinedload(Case.assigned_officer),
    )

    # Role-based filtering
    if current_user.role == RoleEnum.COMPLAINANT:
        query = query.filter(Case.complainant_id == current_user.id)
    elif current_user.role == RoleEnum.BUREAU_OFFICER:
        query = query.filter(
            or_(
                Case.assigned_officer_id == current_user.id,
                Case.assigned_bureau_id == current_user.bureau_id,
            )
        )
    # Central monitoring, super admin, auditor see all

    if status:
        try:
            query = query.filter(Case.status == CaseStatus(status))
        except ValueError:
            pass
    if category:
        try:
            query = query.filter(Case.category == CaseCategory(category))
        except ValueError:
            pass
    if institution_id:
        query = query.filter(Case.institution_id == institution_id)
    if bureau_id:
        query = query.filter(Case.assigned_bureau_id == bureau_id)
    if officer_id:
        query = query.filter(Case.assigned_officer_id == officer_id)
    if priority:
        try:
            query = query.filter(Case.priority == CasePriority(priority))
        except ValueError:
            pass
    if overdue is not None:
        query = query.filter(Case.is_overdue == overdue)
    if q:
        query = query.filter(
            or_(
                Case.case_id.ilike(f"%{q}%"),
                Case.title.ilike(f"%{q}%"),
                Case.description.ilike(f"%{q}%"),
            )
        )

    total = query.count()
    cases = query.order_by(desc(Case.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    items = [_case_to_list_item(c) for c in cases]
    pages = (total + page_size - 1) // page_size if page_size else 1
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = (
        db.query(Case)
        .options(
            joinedload(Case.institution),
            joinedload(Case.complainant),
            joinedload(Case.assigned_officer),
            joinedload(Case.assigned_bureau),
            joinedload(Case.history).joinedload(CaseHistory.actor),
            joinedload(Case.assignments),
            joinedload(Case.comments).joinedload(CaseComment.author),
            joinedload(Case.attachments),
            joinedload(Case.related_from),
            joinedload(Case.coordination_requests),
        )
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied to this case")

    # Build related cases
    related = []
    for r in case.related_from:
        target = db.query(Case).filter(Case.id == r.target_case_id).first()
        related.append({
            "id": r.id,
            "target_case_id": r.target_case_id,
            "target_case_public_id": target.case_id if target else None,
            "target_title": target.title if target else None,
            "similarity_score": r.similarity_score,
            "confirmed": r.confirmed,
            "notes": r.notes,
            "created_at": r.created_at,
        })

    # Filter internal comments for complainants
    comments = case.comments
    if current_user.role == RoleEnum.COMPLAINANT:
        comments = [c for c in comments if not c.is_internal]
        attachments = [a for a in case.attachments if a.is_public_to_complainant]
    else:
        attachments = case.attachments

    # Assignment details
    assignments = []
    for a in case.assignments:
        bureau = db.query(Bureau).filter(Bureau.id == a.bureau_id).first()
        officer = db.query(User).filter(User.id == a.officer_id).first() if a.officer_id else None
        assignments.append({
            "id": a.id,
            "bureau_id": a.bureau_id,
            "officer_id": a.officer_id,
            "assigned_by_id": a.assigned_by_id,
            "priority": a.priority,
            "notes": a.notes,
            "deadline": a.deadline,
            "acknowledged": a.acknowledged,
            "acknowledged_at": a.acknowledged_at,
            "is_current": a.is_current,
            "reassignment_reason": a.reassignment_reason,
            "created_at": a.created_at,
            "bureau_name": bureau.name if bureau else None,
            "officer_name": officer.full_name if officer else None,
        })

    coord = []
    for cr in case.coordination_requests:
        fb = db.query(Bureau).filter(Bureau.id == cr.from_bureau_id).first()
        tb = db.query(Bureau).filter(Bureau.id == cr.to_bureau_id).first()
        coord.append({
            "id": cr.id,
            "case_id": cr.case_id,
            "case_public_id": case.case_id,
            "from_bureau_id": cr.from_bureau_id,
            "to_bureau_id": cr.to_bureau_id,
            "from_bureau_name": fb.name if fb else None,
            "to_bureau_name": tb.name if tb else None,
            "reason": cr.reason,
            "requested_action": cr.requested_action,
            "response": cr.response,
            "status": cr.status,
            "response_deadline": cr.response_deadline,
            "created_at": cr.created_at,
            "responded_at": cr.responded_at,
        })

    result = CaseDetail(
        id=case.id,
        case_id=case.case_id,
        tracking_ref=case.tracking_ref if current_user.role != RoleEnum.COMPLAINANT or case.complainant_id == current_user.id else "",
        title=case.title,
        description=case.description,
        category=case.category,
        status=case.status,
        priority=case.priority,
        institution_id=case.institution_id,
        complainant_id=case.complainant_id,
        assigned_bureau_id=case.assigned_bureau_id,
        assigned_officer_id=case.assigned_officer_id,
        incident_date=case.incident_date,
        contact_phone=case.contact_phone if current_user.role != RoleEnum.COMPLAINANT else None,
        contact_email=case.contact_email if current_user.role != RoleEnum.COMPLAINANT else None,
        deadline=case.deadline,
        is_overdue=case.is_overdue,
        resolution_summary=case.resolution_summary,
        rejection_reason=case.rejection_reason,
        information_request=case.information_request,
        complainant_response=case.complainant_response,
        version=case.version,
        created_at=case.created_at,
        updated_at=case.updated_at,
        closed_at=case.closed_at,
        institution=case.institution,
        complainant=case.complainant if current_user.role != RoleEnum.COMPLAINANT else None,
        assigned_officer=case.assigned_officer,
        assigned_bureau_name=case.assigned_bureau.name if case.assigned_bureau else None,
        history=[CaseHistoryOut.model_validate(h) for h in case.history],
        assignments=assignments,
        comments=[CaseCommentOut.model_validate(c) for c in comments],
        attachments=[AttachmentOut.model_validate(a) for a in attachments],
        related_cases=related,
        coordination_requests=coord,
    )
    return result


@router.post("/{case_id}/accept", response_model=CaseOut)
def accept(
    case_id: int,
    data: CaseAccept = CaseAccept(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_central_monitoring),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return accept_case(db, case, current_user, data.notes)


@router.post("/{case_id}/reject", response_model=CaseOut)
def reject(
    case_id: int,
    data: CaseReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_central_monitoring),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return reject_case(db, case, current_user, data.reason)


@router.post("/{case_id}/request-information", response_model=CaseOut)
def request_info(
    case_id: int,
    data: CaseRequestInfo,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_bureau_officer),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    return request_information(db, case, current_user, data.information_request)


@router.post("/{case_id}/respond-information", response_model=CaseOut)
def respond_info(
    case_id: int,
    data: CaseComplainantResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.complainant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the complainant can respond")
    if case.status != CaseStatus.NEEDS_INFORMATION:
        raise HTTPException(status_code=400, detail="Case is not awaiting information")

    case.complainant_response = data.response
    old = case.status
    case.status = CaseStatus.UNDER_REVIEW
    case.version += 1
    add_history(db, case, current_user, "INFORMATION_PROVIDED", old.value, CaseStatus.UNDER_REVIEW.value, data.response)
    create_notification(
        db,
        # notify monitors
        db.query(User).filter(User.role == RoleEnum.CENTRAL_MONITORING, User.is_active == True).first().id
        if db.query(User).filter(User.role == RoleEnum.CENTRAL_MONITORING, User.is_active == True).first()
        else current_user.id,
        "Complainant Response Received",
        f"Case {case.case_id}: additional information provided.",
        "info_response",
        case.id,
    )
    # Notify all monitors properly
    monitors = db.query(User).filter(
        User.role.in_([RoleEnum.CENTRAL_MONITORING, RoleEnum.SUPER_ADMIN]), User.is_active == True
    ).all()
    for m in monitors:
        create_notification(db, m.id, "Complainant Response", f"Case {case.case_id} has a response to information request.", "info_response", case.id)
    if case.assigned_officer_id:
        create_notification(db, case.assigned_officer_id, "Complainant Response", f"Case {case.case_id}: info provided.", "info_response", case.id)
    db.commit()
    db.refresh(case)
    return case


@router.post("/{case_id}/assign", response_model=CaseOut)
def assign(
    case_id: int,
    data: CaseAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_central_monitoring),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return assign_case(db, case, current_user, data)


@router.post("/{case_id}/acknowledge-assignment", response_model=CaseOut)
def acknowledge(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_bureau_officer),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return acknowledge_assignment(db, case, current_user)


@router.post("/{case_id}/status", response_model=CaseOut)
def change_status(
    case_id: int,
    data: CaseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_bureau_officer),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return update_status(db, case, current_user, data.status, data.remarks)


@router.post("/{case_id}/submit-resolution", response_model=CaseOut)
def resolution(
    case_id: int,
    data: CaseResolution,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_bureau_officer),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return submit_resolution(db, case, current_user, data.resolution_summary)


@router.post("/{case_id}/approve-closure", response_model=CaseOut)
def closure(
    case_id: int,
    data: CaseClosure,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_central_monitoring),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return approve_closure(db, case, current_user, data.approve, data.remarks)


@router.get("/{case_id}/related", response_model=List[RelatedCaseOut])
def get_related(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    results = find_related_cases(db, case)
    out = []
    for target, score in results:
        persist_suggestion(db, case.id, target.id, score)
        out.append({
            "id": 0,
            "target_case_id": target.id,
            "target_case_public_id": target.case_id,
            "target_title": target.title,
            "similarity_score": round(score, 4),
            "confirmed": False,
            "notes": None,
            "created_at": datetime.now(timezone.utc),
        })
    db.commit()
    return out


@router.post("/{case_id}/related/{target_id}/confirm")
def confirm_related(
    case_id: int,
    target_id: int,
    confirmed: bool = True,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    rel = (
        db.query(RelatedCase)
        .filter(RelatedCase.source_case_id == case_id, RelatedCase.target_case_id == target_id)
        .first()
    )
    if not rel:
        rel = RelatedCase(source_case_id=case_id, target_case_id=target_id, confirmed=confirmed, notes=notes)
        db.add(rel)
    else:
        rel.confirmed = confirmed
        rel.notes = notes
        rel.confirmed_by_id = current_user.id
        rel.confirmed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Related case updated", "confirmed": confirmed}


@router.post("/{case_id}/comments", response_model=CaseCommentOut)
def add_comment(
    case_id: int,
    content: str = Form(...),
    is_internal: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == RoleEnum.COMPLAINANT:
        is_internal = False
    comment = CaseComment(case_id=case_id, author_id=current_user.id, content=content, is_internal=is_internal)
    db.add(comment)
    add_history(db, case, current_user, "COMMENT_ADDED", None, None, content[:200])
    db.commit()
    db.refresh(comment)
    return comment


@router.post("/{case_id}/attachments", response_model=AttachmentOut)
async def upload_attachment(
    case_id: int,
    file: UploadFile = File(...),
    is_evidence: bool = Form(False),
    is_public_to_complainant: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    stored_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(settings.UPLOAD_DIR, stored_name)
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    att = Attachment(
        case_id=case_id,
        uploaded_by_id=current_user.id,
        filename=stored_name,
        original_filename=file.filename or stored_name,
        content_type=file.content_type,
        file_size=len(content),
        file_path=path,
        is_evidence=is_evidence,
        is_public_to_complainant=is_public_to_complainant or current_user.role == RoleEnum.COMPLAINANT,
    )
    db.add(att)
    add_history(db, case, current_user, "ATTACHMENT_UPLOADED", None, None, file.filename)
    db.commit()
    db.refresh(att)
    return att


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    att = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    case = db.query(Case).filter(Case.id == att.case_id).first()
    if not case or not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == RoleEnum.COMPLAINANT and not att.is_public_to_complainant:
        raise HTTPException(status_code=403, detail="Attachment not available")
    if not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(att.file_path, filename=att.original_filename, media_type=att.content_type or "application/octet-stream")
