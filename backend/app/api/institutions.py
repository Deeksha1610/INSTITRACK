from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.core.deps import get_current_user, get_super_admin, get_staff
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.case import Case, CaseStatus
from app.schemas.institution import InstitutionCreate, InstitutionUpdate, InstitutionOut, InstitutionStats
from app.services.case_service import log_audit

router = APIRouter(prefix="/api/institutions", tags=["Institutions"])


@router.get("", response_model=List[InstitutionOut])
def list_institutions(
    q: Optional[str] = None,
    state: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Institution)
    if active_only:
        query = query.filter(Institution.is_active == True)
    if q:
        query = query.filter(
            (Institution.name.ilike(f"%{q}%")) | (Institution.institution_id.ilike(f"%{q}%"))
        )
    if state:
        query = query.filter(Institution.state == state)
    return query.order_by(Institution.name).all()


@router.get("/public", response_model=List[InstitutionOut])
def list_institutions_public(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Public endpoint for complaint form institution selector."""
    query = db.query(Institution).filter(Institution.is_active == True)
    if q:
        query = query.filter(Institution.name.ilike(f"%{q}%"))
    return query.order_by(Institution.name).limit(100).all()


@router.get("/{institution_id}", response_model=InstitutionOut)
def get_institution(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst


@router.get("/{institution_id}/stats", response_model=InstitutionStats)
def get_institution_stats(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    total = db.query(func.count(Case.id)).filter(Case.institution_id == institution_id).scalar() or 0
    open_statuses = [
        CaseStatus.SUBMITTED, CaseStatus.UNDER_REVIEW, CaseStatus.ACCEPTED,
        CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS, CaseStatus.NEEDS_INFORMATION,
        CaseStatus.RETURNED, CaseStatus.RESOLUTION_SUBMITTED, CaseStatus.ESCALATED, CaseStatus.REOPENED,
    ]
    open_count = db.query(func.count(Case.id)).filter(
        Case.institution_id == institution_id, Case.status.in_(open_statuses)
    ).scalar() or 0
    resolved = db.query(func.count(Case.id)).filter(
        Case.institution_id == institution_id, Case.status.in_([CaseStatus.CLOSED, CaseStatus.REJECTED])
    ).scalar() or 0
    overdue = db.query(func.count(Case.id)).filter(
        Case.institution_id == institution_id, Case.is_overdue == True
    ).scalar() or 0

    cats = (
        db.query(Case.category, func.count(Case.id))
        .filter(Case.institution_id == institution_id)
        .group_by(Case.category)
        .all()
    )
    breakdown = {c.value if hasattr(c, "value") else str(c): n for c, n in cats}

    return InstitutionStats(
        institution=inst,
        total_cases=total,
        open_cases=open_count,
        resolved_cases=resolved,
        overdue_cases=overdue,
        category_breakdown=breakdown,
    )


@router.post("", response_model=InstitutionOut)
def create_institution(
    data: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    existing = db.query(Institution).filter(Institution.institution_id == data.institution_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution ID already exists")
    inst = Institution(**data.model_dump())
    db.add(inst)
    db.commit()
    db.refresh(inst)
    log_audit(db, current_user, "INSTITUTION_CREATED", "institution", inst.institution_id)
    db.commit()
    return inst


@router.patch("/{institution_id}", response_model=InstitutionOut)
def update_institution(
    institution_id: int,
    data: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(inst, k, v)
    db.commit()
    db.refresh(inst)
    log_audit(db, current_user, "INSTITUTION_UPDATED", "institution", inst.institution_id)
    db.commit()
    return inst
