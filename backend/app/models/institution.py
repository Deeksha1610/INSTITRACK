from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String(50), unique=True, index=True, nullable=False)  # stable public ID
    name = Column(String(300), nullable=False, index=True)
    institution_type = Column(String(100), nullable=True)  # University, College, Polytechnic, etc.
    state = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    registration_ref = Column(String(100), nullable=True)  # fictional demo reference
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cases = relationship("Case", back_populates="institution")

    def __repr__(self):
        return f"<Institution {self.institution_id}: {self.name}>"
