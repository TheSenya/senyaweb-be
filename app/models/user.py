from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

from typing import Optional
from app.models.base import RequestInfoMixin

class User(RequestInfoMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()

    # TODO: we can implement this later
    # firstname: Optional[str], max length, min_length
    # lastname: Optional[str], max length, min_length
    
    # Audit & Status
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # Tracking
    last_login_time: Optional[datetime] = Field(default=None) # update this everytime the user logs back in
    created_at: datetime = Field(default_factory=datetime.now)



