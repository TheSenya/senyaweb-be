from typing import Optional
from fastapi import Cookie, HTTPException, status
from jose import jwt, JWTError
from app.core.config import settings

async def get_current_user(access_token: Optional[str] = Cookie(None)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    if not access_token:
        raise credentials_exception
        
    try:
        if access_token.startswith("Bearer "):
            token = access_token.split(" ")[1]
        else:
            token = access_token
            
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return username
