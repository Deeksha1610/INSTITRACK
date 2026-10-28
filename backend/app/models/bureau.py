from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class Bureau(Base):
    __tablename__ = "bureaus"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    officers = relationship("User", back_populates="bureau", foreign_keys="User.bureau_id")
    cases = relationship("Case", back_populates="assigned_bureau", foreign_keys="Case.assigned_bureau_id")
    category_rules = relationship("CategoryBureauRule", back_populates="bureau")

    def __repr__(self):
        return f"<Bureau {self.code}: {self.name}>"
