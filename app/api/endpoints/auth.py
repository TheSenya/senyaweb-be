from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from pydantic import BaseModel
from datetime import datetime
from sqlmodel import Session, select
from datetime import timedelta, timezone
from typing import Literal

from app.core.config import settings, ENV
from app.core.db import get_session
from app.api.deps import get_current_user
from app.middleware.security import rate_limit_gaurd
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash
from app.models.auth import RefreshToken
from app.models.user import User
from app.models.tracking import LoginAttempt


# Determine if we're in production for secure cookie settings
IS_PRODUCTION = ENV.lower() == "prod"


def set_auth_cookies(
    response: Response, 
    access_token: str, 
    refresh_token: str
) -> None:
    """
    Set authentication cookies with proper security settings.
    
    In production:
    - secure=True: Only sent over HTTPS
    - samesite=strict: Prevents CSRF attacks
    
    In development:
    - secure=False: Works over HTTP
    - samesite=lax: More lenient for dev
    """
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="strict" if IS_PRODUCTION else "lax",
        secure=IS_PRODUCTION
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        expires=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="strict" if IS_PRODUCTION else "lax",
        secure=IS_PRODUCTION
    )


class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(
    prefix="/auth",
    tags=['authentication'],
    responses={403: {'description': "N/A"}}
)


@router.post("/register")
def register(response: Response, request: Request, register_data: LoginRequest, session: Session = Depends(get_session)):
    # Capture Request Info
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")

    # 1. Check if user exists
    statement = select(User).where(User.email == register_data.email)
    user = session.exec(statement).first()
    
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # 2. Create User
    hashed_password = get_password_hash(register_data.password)
    user = User(
        email=register_data.email, 
        hashed_password=hashed_password,
        ip_address=ip,
        user_agent=user_agent
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # 3. Auto-Login (Generate Tokens)
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)
    
    # 4. Store Refresh Token
    db_refresh_token = RefreshToken(
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_id=user.id,
        ip_address=ip,
        user_agent=user_agent
    )
    session.add(db_refresh_token)
    session.commit()
    
    # 5. Set Cookies (secure in production)
    set_auth_cookies(response, access_token, refresh_token)
    
    return {"success": True, "message": "User registered successfully"}


@router.post("/login")
def login(
    response: Response, 
    request: Request, 
    login_data: LoginRequest, 
    session: Session = Depends(get_session),
    _rate_limit: None = Depends(rate_limit_gaurd)  # Rate limit protection
):
    # Capture Request Info
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")

    # 1. Verify User
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        # Log failure
        login_attempt = LoginAttempt(
            email=login_data.email, 
            is_success=False,
            ip_address=ip,
            user_agent=user_agent
        )
        session.add(login_attempt)
        session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Log Success
    login_attempt = LoginAttempt(
        email=login_data.email, 
        is_success=True,
        ip_address=ip,
        user_agent=user_agent
    )
    session.add(login_attempt)
    
    # Update User Stats
    user.last_login_time = datetime.now(timezone.utc)
    user.ip_address = ip
    user.user_agent = user_agent
    session.add(user)
    
    # 2. Create Tokens
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)
    
    # 3. Store Refresh Token
    db_refresh_token = RefreshToken(
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_id=user.id,
        ip_address=ip,
        user_agent=user_agent
    )
    session.add(db_refresh_token)
    session.commit()
    
    # 4. Set Cookies (secure in production)
    set_auth_cookies(response, access_token, refresh_token)
    
    return {"success": True}


@router.post("/logout")
def logout(response: Response):
    """
    Logout the current user by clearing auth cookies.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"success": True}


@router.post("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    
    Returns user data including admin status for frontend authorization.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_superuser,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login_time.isoformat() if current_user.last_login_time else None
    }
