"""
Cryptography endpoints for public key distribution.

The public key endpoint is intentionally unprotected - public keys are meant
to be public. Clients need this key to encrypt requests to the server.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.config import settings

router = APIRouter(
    prefix="/crypto",
    tags=['cryptography'],
    responses={404: {'description': "Key not found"}}
)


@router.get("/public-key", response_class=PlainTextResponse)
async def get_public_key():
    """
    Returns the server's public key in PEM format.
    
    This is used by frontend clients to encrypt requests to the server.
    Only the server's private key can decrypt messages encrypted with this key.
    
    Security Note:
    - This endpoint is excluded from EncryptionMiddleware
    - The public key is safe to share - that's the whole point of public keys!
    """
    if not settings.PUBLIC_KEY:
        return PlainTextResponse(
            content="Public key not configured",
            status_code=500
        )
    
    return settings.PUBLIC_KEY
