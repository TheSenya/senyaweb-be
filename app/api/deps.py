"""
Authentication Dependencies

Provides reusable dependency functions for FastAPI endpoints
to handle authentication and authorization.
"""

from typing import Optional
from fastapi import Cookie, HTTPException, status, Depends
from jose import jwt, JWTError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.models.user import User


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    session: Session = Depends(get_session)
) -> User:
    """
    Dependency that extracts and validates the current user from the access token.
    
    Returns the full User object from the database.
    
    Raises:
        HTTPException 401: If token is missing, invalid, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    print(f"getting current user, access_token = {access_token}")   

    if not access_token:
        raise credentials_exception
        
    try:
        # Handle "Bearer " prefix if present
        if access_token.startswith("Bearer "):
            token = access_token.split(" ")[1]
        else:
            token = access_token
            
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch the user from the database
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
        
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures the current user is an admin (superuser).
    
    Use this dependency on endpoints that should only be accessible by admins.
    
    Raises:
        HTTPException 403: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
