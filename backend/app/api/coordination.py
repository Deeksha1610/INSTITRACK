from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.db.session import get_db
from app.core.deps import get_current_user, get_bureau_officer, get_staff
from app.models.user import User, RoleEnum
from app.models.case import Case, CoordinationRequest
from app.models.bureau import Bureau
from app.schemas.case import CoordinationRequestCreate, CoordinationRequestRespond, CoordinationRequestOut
from app.services.case_service import add_history, create_notification, log_audit, check_case_access

router = APIRouter(prefix="/api/coordination-requests", tags=["Coordination"])


@router.post("", response_model=CoordinationRequestOut)
def create_request(
    data: CoordinationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_bureau_officer),
):
    case = db.query(Case).filter(Case.id == data.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not check_case_access(case, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    from_bureau_id = current_user.bureau_id or case.assigned_bureau_id
    if not from_bureau_id:
        raise HTTPException(status_code=400, detail="Cannot determine source bureau")

    to_bureau = db.query(Bureau).filter(Bureau.id == data.to_bureau_id, Bureau.is_active == True).first()
    if not to_bureau:
        raise HTTPException(status_code=400, detail="Invalid target bureau")

    cr = CoordinationRequest(
        case_id=data.case_id,
        from_bureau_id=from_bureau_id,
        to_bureau_id=data.to_bureau_id,
        requested_by_id=current_user.id,
        reason=data.reason,
        requested_action=data.requested_action,
        response_deadline=data.response_deadline,
        status="PENDING",
    )
    db.add(cr)
    add_history(db, case, current_user, "COORDINATION_REQUESTED", None, None, f"To bureau {to_bureau.name}: {data.reason}")
    log_audit(db, current_user, "COORDINATION_CREATED", "coordination", str(case.case_id))

    # Notify officers in target bureau
    officers = db.query(User).filter(
        User.bureau_id == data.to_bureau_id, User.role == RoleEnum.BUREAU_OFFICER, User.is_active == True
    ).all()
    for o in officers:
        create_notification(
            db, o.id, "Coordination Request",
            f"Case {case.case_id}: coordination requested from another bureau.",
            "coordination", case.id,
        )
    db.commit()
    db.refresh(cr)

    fb = db.query(Bureau).filter(Bureau.id == cr.from_bureau_id).first()
    return {
        "id": cr.id,
        "case_id": cr.case_id,
        "case_public_id": case.case_id,
        "from_bureau_id": cr.from_bureau_id,
        "to_bureau_id": cr.to_bureau_id,
        "from_bureau_name": fb.name if fb else None,
        "to_bureau_name": to_bureau.name,
        "reason": cr.reason,
        "requested_action": cr.requested_action,
        "response": cr.response,
        "status": cr.status,
        "response_deadline": cr.response_deadline,
        "created_at": cr.created_at,
        "responded_at": cr.responded_at,
    }


@router.get("", response_model=List[CoordinationRequestOut])
def list_requests(
    status: Optional[str] = None,
    direction: Optional[str] = None,  # incoming / outgoing
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    query = db.query(CoordinationRequest)
    if current_user.role == RoleEnum.BUREAU_OFFICER and current_user.bureau_id:
        if direction == "incoming":
            query = query.filter(CoordinationRequest.to_bureau_id == current_user.bureau_id)
        elif direction == "outgoing":
            query = query.filter(CoordinationRequest.from_bureau_id == current_user.bureau_id)
        else:
            query = query.filter(
                or_(
                    CoordinationRequest.to_bureau_id == current_user.bureau_id,
                    CoordinationRequest.from_bureau_id == current_user.bureau_id,
                )
            )
    if status:
        query = query.filter(CoordinationRequest.status == status)

    items = query.order_by(desc(CoordinationRequest.created_at)).limit(100).all()
    result = []
    for cr in items:
        case = db.query(Case).filter(Case.id == cr.case_id).first()
        fb = db.query(Bureau).filter(Bureau.id == cr.from_bureau_id).first()
        tb = db.query(Bureau).filter(Bureau.id == cr.to_bureau_id).first()
        result.append({
            "id": cr.id,
            "case_id": cr.case_id,
            "case_public_id": case.case_id if case else None,
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
    return result


@router.post("/{request_id}/respond", response_model=CoordinationRequestOut)
def respond(
    request_id: int,
    data: CoordinationRequestRespond,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_bureau_officer),
):
    cr = db.query(CoordinationRequest).filter(CoordinationRequest.id == request_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Request not found")
    if current_user.role == RoleEnum.BUREAU_OFFICER and current_user.bureau_id != cr.to_bureau_id:
        raise HTTPException(status_code=403, detail="Not authorized for this request")

    cr.response = data.response
    cr.responded_by_id = current_user.id
    cr.responded_at = datetime.now(timezone.utc)
    cr.status = "COMPLETED" if data.mark_completed else "RESPONDED"
    if data.mark_completed:
        cr.completed_at = datetime.now(timezone.utc)

    case = db.query(Case).filter(Case.id == cr.case_id).first()
    if case:
        add_history(db, case, current_user, "COORDINATION_RESPONDED", None, None, data.response[:200])
        create_notification(
            db, cr.requested_by_id, "Coordination Response",
            f"Case {case.case_id}: response received on coordination request.",
            "coordination", case.id,
        )

    db.commit()
    db.refresh(cr)
    fb = db.query(Bureau).filter(Bureau.id == cr.from_bureau_id).first()
    tb = db.query(Bureau).filter(Bureau.id == cr.to_bureau_id).first()
    return {
        "id": cr.id,
        "case_id": cr.case_id,
        "case_public_id": case.case_id if case else None,
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
    }
