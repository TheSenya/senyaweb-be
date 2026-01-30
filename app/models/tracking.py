from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

from app.models.base import RequestInfoMixin

class LoginAttempt(RequestInfoMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    is_success: bool
    email: str
    is_success: bool
    timestamp: datetime = Field(default_factory=datetime.now)

class ApiPing(RequestInfoMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Request Info
    method: str = Field(default="GET")
    path: str = Field(default="/")
    
    method: str = Field(default="GET")
    path: str = Field(default="/")
    timestamp: datetime = Field(default_factory=datetime.now)

