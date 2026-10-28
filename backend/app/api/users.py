from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, get_super_admin
from app.core.security import get_password_hash
from app.models.user import User, RoleEnum
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.case_service import log_audit

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=List[UserOut])
def list_users(
    role: Optional[str] = None,
    bureau_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    query = db.query(User)
    if role:
        try:
            query = query.filter(User.role == RoleEnum(role))
        except ValueError:
            pass
    if bureau_id:
        query = query.filter(User.bureau_id == bureau_id)
    return query.order_by(User.full_name).all()


@router.get("/officers")
def list_officers(
    bureau_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List bureau officers for assignment dropdowns."""
    query = db.query(User).filter(User.role == RoleEnum.BUREAU_OFFICER, User.is_active == True)
    if bureau_id:
        query = query.filter(User.bureau_id == bureau_id)
    officers = query.all()
    return [{"id": o.id, "full_name": o.full_name, "username": o.username, "bureau_id": o.bureau_id} for o in officers]


@router.post("", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    existing = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        phone=data.phone,
        hashed_password=get_password_hash(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, current_user, "USER_CREATED", "user", str(user.id), f"Role: {user.role.value}")
    db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    log_audit(db, current_user, "USER_UPDATED", "user", str(user.id))
    db.commit()
    return user
