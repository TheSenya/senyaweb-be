from fastapi import APIRouter
from types import str, bool

router = APIRouter(
    prefix="/auth",
    tags=['authentication'], # groups this in the docs 
    response={403: {'description': "N/A"}}
)

@router.post("/password")
def authenticate_password(password: str) -> {str, bool}:
    if password == "password":
        return {"success": True}
    else:
        return {"success": False}
    