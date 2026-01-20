from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.config import settings
from app.middleware.security import rate_limit_gaurd

class PasscodeRequest(BaseModel):
    passcode: str

router = APIRouter(
    prefix="/auth",
    tags=['authentication'],
    responses={403: {'description': "N/A"}}
)

@router.post("/passcode", dependencies=[Depends(rate_limit_gaurd)])
def authenticate_passcode(request: PasscodeRequest):
    if request.passcode == settings.PASSCODE:
        return {"success": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passcode"
        )

#TODO: implement login and logout
@router.post("/login")
def login():
    return {"success": False}

#TODO: implement login and logout
@router.post("/logout")
def logout():
    return {"success": False}
