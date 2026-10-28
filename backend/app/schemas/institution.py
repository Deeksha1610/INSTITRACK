from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class InstitutionBase(BaseModel):
    name: str
    institution_type: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    registration_ref: Optional[str] = None


class InstitutionCreate(InstitutionBase):
    institution_id: str


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    institution_type: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    registration_ref: Optional[str] = None
    is_active: Optional[bool] = None


class InstitutionOut(InstitutionBase):
    id: int
    institution_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InstitutionStats(BaseModel):
    institution: InstitutionOut
    total_cases: int
    open_cases: int
    resolved_cases: int
    overdue_cases: int
    category_breakdown: dict
