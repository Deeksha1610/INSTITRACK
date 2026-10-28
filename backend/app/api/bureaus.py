from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user, get_super_admin, get_staff
from app.models.user import User
from app.models.bureau import Bureau
from app.models.case import CategoryBureauRule, CaseCategory
from app.schemas.case import BureauOut
from app.services.case_service import log_audit

router = APIRouter(prefix="/api/bureaus", tags=["Bureaus"])


class BureauCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class BureauUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", response_model=List[BureauOut])
def list_bureaus(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Bureau)
    if active_only:
        query = query.filter(Bureau.is_active == True)
    return query.order_by(Bureau.name).all()


@router.post("", response_model=BureauOut)
def create_bureau(
    data: BureauCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    existing = db.query(Bureau).filter(Bureau.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bureau code already exists")
    bureau = Bureau(**data.model_dump())
    db.add(bureau)
    db.commit()
    db.refresh(bureau)
    log_audit(db, current_user, "BUREAU_CREATED", "bureau", bureau.code)
    db.commit()
    return bureau


@router.patch("/{bureau_id}", response_model=BureauOut)
def update_bureau(
    bureau_id: int,
    data: BureauUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    bureau = db.query(Bureau).filter(Bureau.id == bureau_id).first()
    if not bureau:
        raise HTTPException(status_code=404, detail="Bureau not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(bureau, k, v)
    db.commit()
    db.refresh(bureau)
    return bureau


@router.get("/routing-rules")
def get_routing_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    rules = db.query(CategoryBureauRule).filter(CategoryBureauRule.is_active == True).all()
    result = []
    for r in rules:
        bureau = db.query(Bureau).filter(Bureau.id == r.bureau_id).first()
        result.append({
            "id": r.id,
            "category": r.category.value if r.category else None,
            "bureau_id": r.bureau_id,
            "bureau_name": bureau.name if bureau else None,
            "bureau_code": bureau.code if bureau else None,
        })
    return result


@router.get("/recommend/{category}")
def recommend_bureau(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    try:
        cat = CaseCategory(category)
    except ValueError:
        return {"recommended_bureau_id": None, "message": "Unknown category"}
    rule = db.query(CategoryBureauRule).filter(
        CategoryBureauRule.category == cat, CategoryBureauRule.is_active == True
    ).first()
    if not rule:
        return {"recommended_bureau_id": None, "message": "No routing rule configured"}
    bureau = db.query(Bureau).filter(Bureau.id == rule.bureau_id).first()
    return {
        "recommended_bureau_id": rule.bureau_id,
        "bureau_name": bureau.name if bureau else None,
        "bureau_code": bureau.code if bureau else None,
        "message": "Recommendation based on configured category-to-bureau rules (demonstration)",
    }
