from fastapi import APIRouter
from typing import str, bool

router = APIRouter(
    prefix="/auth",
    tags=['authentication'], # groups this in the docs 
    response={403: {'description': "N/A"}}
)

@router.post("/passcode", response_model={str, bool})
def authenticate_passcode(passcode: str) -> {str, bool}:
    if passcode == "passcode":
        return {"success": True}
    else:
        return {"success": False}

