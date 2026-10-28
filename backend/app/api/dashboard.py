from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.core.deps import get_current_user, get_staff
from app.models.user import User, RoleEnum
from app.models.case import Case, CaseStatus, CoordinationRequest
from app.models.institution import Institution
from app.models.bureau import Bureau
from app.schemas.case import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = DashboardSummary()

    if current_user.role == RoleEnum.COMPLAINANT:
        base = db.query(Case).filter(Case.complainant_id == current_user.id)
        s.total_cases = base.count()
        s.needs_information = base.filter(Case.status == CaseStatus.NEEDS_INFORMATION).count()
        s.resolved_closed = base.filter(Case.status.in_([CaseStatus.CLOSED, CaseStatus.REJECTED])).count()
        s.assigned_in_progress = base.filter(
            Case.status.in_([CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS, CaseStatus.RESOLUTION_SUBMITTED])
        ).count()
        return s

    if current_user.role == RoleEnum.BUREAU_OFFICER:
        base = db.query(Case).filter(
            (Case.assigned_officer_id == current_user.id) | (Case.assigned_bureau_id == current_user.bureau_id)
        )
        s.my_assigned = base.count()
        s.awaiting_acknowledgement = base.filter(Case.status == CaseStatus.ASSIGNED).count()
        s.assigned_in_progress = base.filter(Case.status == CaseStatus.IN_PROGRESS).count()
        s.overdue = base.filter(Case.is_overdue == True).count()
        s.returned = base.filter(Case.status == CaseStatus.RETURNED).count()
        s.resolution_pending_review = base.filter(Case.status == CaseStatus.RESOLUTION_SUBMITTED).count()
        s.needs_information = base.filter(Case.status == CaseStatus.NEEDS_INFORMATION).count()
        s.pending_coordination = (
            db.query(CoordinationRequest)
            .filter(CoordinationRequest.to_bureau_id == current_user.bureau_id, CoordinationRequest.status == "PENDING")
            .count()
        )
        return s

    # Central monitoring / Super admin / Auditor
    s.total_cases = db.query(func.count(Case.id)).scalar() or 0
    s.new_awaiting_review = db.query(func.count(Case.id)).filter(
        Case.status.in_([CaseStatus.SUBMITTED, CaseStatus.UNDER_REVIEW])
    ).scalar() or 0
    s.accepted_unassigned = db.query(func.count(Case.id)).filter(Case.status == CaseStatus.ACCEPTED).scalar() or 0
    s.assigned_in_progress = db.query(func.count(Case.id)).filter(
        Case.status.in_([CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS])
    ).scalar() or 0
    s.needs_information = db.query(func.count(Case.id)).filter(Case.status == CaseStatus.NEEDS_INFORMATION).scalar() or 0
    s.overdue = db.query(func.count(Case.id)).filter(Case.is_overdue == True).scalar() or 0
    s.resolved_closed = db.query(func.count(Case.id)).filter(
        Case.status.in_([CaseStatus.CLOSED, CaseStatus.REJECTED])
    ).scalar() or 0
    s.pending_coordination = db.query(func.count(CoordinationRequest.id)).filter(
        CoordinationRequest.status == "PENDING"
    ).scalar() or 0
    s.resolution_pending_review = db.query(func.count(Case.id)).filter(
        Case.status == CaseStatus.RESOLUTION_SUBMITTED
    ).scalar() or 0

    if current_user.role in [RoleEnum.SUPER_ADMIN]:
        s.total_users = db.query(func.count(User.id)).scalar() or 0
        s.total_institutions = db.query(func.count(Institution.id)).scalar() or 0
        s.total_bureaus = db.query(func.count(Bureau.id)).scalar() or 0

    return s


@router.get("/workload")
def workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    rows = (
        db.query(Bureau.name, Bureau.code, func.count(Case.id))
        .outerjoin(Case, Case.assigned_bureau_id == Bureau.id)
        .filter(Bureau.is_active == True)
        .group_by(Bureau.id)
        .all()
    )
    return [{"bureau": name, "code": code, "case_count": count} for name, code, count in rows]


@router.get("/trends")
def trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    submitted = (
        db.query(func.date(Case.created_at), func.count(Case.id))
        .filter(Case.created_at >= since)
        .group_by(func.date(Case.created_at))
        .order_by(func.date(Case.created_at))
        .all()
    )
    closed = (
        db.query(func.date(Case.closed_at), func.count(Case.id))
        .filter(Case.closed_at != None, Case.closed_at >= since)
        .group_by(func.date(Case.closed_at))
        .order_by(func.date(Case.closed_at))
        .all()
    )
    by_category = (
        db.query(Case.category, func.count(Case.id))
        .group_by(Case.category)
        .all()
    )
    by_status = (
        db.query(Case.status, func.count(Case.id))
        .group_by(Case.status)
        .all()
    )
    return {
        "submitted_over_time": [{"date": str(d), "count": c} for d, c in submitted],
        "closed_over_time": [{"date": str(d), "count": c} for d, c in closed],
        "by_category": [{"category": (cat.value if hasattr(cat, "value") else str(cat)), "count": n} for cat, n in by_category],
        "by_status": [{"status": (st.value if hasattr(st, "value") else str(st)), "count": n} for st, n in by_status],
    }


@router.get("/recent-activity")
def recent_activity(
    limit: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.case import CaseHistory
    query = db.query(CaseHistory).order_by(desc(CaseHistory.created_at)).limit(limit)
    if current_user.role == RoleEnum.COMPLAINANT:
        case_ids = [c.id for c in db.query(Case.id).filter(Case.complainant_id == current_user.id).all()]
        query = query.filter(CaseHistory.case_id.in_(case_ids))
    elif current_user.role == RoleEnum.BUREAU_OFFICER:
        case_ids = [
            c.id for c in db.query(Case.id).filter(
                (Case.assigned_officer_id == current_user.id) | (Case.assigned_bureau_id == current_user.bureau_id)
            ).all()
        ]
        query = query.filter(CaseHistory.case_id.in_(case_ids))
    items = query.all()
    result = []
    for h in items:
        case = db.query(Case).filter(Case.id == h.case_id).first()
        actor = db.query(User).filter(User.id == h.actor_id).first() if h.actor_id else None
        result.append({
            "id": h.id,
            "action": h.action,
            "from_status": h.from_status,
            "to_status": h.to_status,
            "remarks": h.remarks,
            "created_at": h.created_at,
            "case_id": case.case_id if case else None,
            "case_db_id": h.case_id,
            "actor_name": actor.full_name if actor else "System",
        })
    return result
