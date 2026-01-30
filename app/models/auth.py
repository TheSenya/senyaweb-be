from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

from app.models.base import RequestInfoMixin
from sqlmodel import SQLModel, Field

class RefreshToken(RequestInfoMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    # `default_factory` tells Python to run a function to generate a default value every time a new item is created, rather than setting a single fixed value. 
    # by using datetime.now rather than datetime.now(), the function is only ran when the refresh token is created
    revoked: bool = Field(default=False)
    
    
    replaced_by: Optional[str] = Field(default=None)
    
    # Foreign Key
    user_id: int = Field(foreign_key="user.id")