from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

class PasscodeRequest(BaseModel):
    passcode: str

router = APIRouter(
    prefix="/auth",
    tags=['authentication'],
    responses={403: {'description': "N/A"}}
)

@router.post("/passcode")
def authenticate_passcode(request: PasscodeRequest):
    if request.passcode == settings.PASSCODE:
        return {"success": True}
    else:
        return {"success": False}

#TODO: implement login and logout
@router.post("/login")
def login():
    return {"success": False}

#TODO: implement login and logout
@router.post("/logout")
def logout():
    return {"success": False}
