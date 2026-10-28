from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
