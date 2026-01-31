"""
Security Headers Middleware

Adds important security headers to all HTTP responses to protect against
common web vulnerabilities like XSS, clickjacking, MIME sniffing, etc.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Legacy XSS protection (for older browsers)
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    - Strict-Transport-Security: Forces HTTPS (HSTS)
    - Content-Security-Policy: Controls resource loading
    """
    
    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # HSTS - Only in production to avoid issues with local dev
        if self.is_production:
            # max-age=1 year, includeSubDomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
            
            # Basic CSP - adjust based on your needs
            # This is a restrictive default, you may need to loosen it
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://api.senya.ca; "
                "frame-ancestors 'none';"
            )
        
        return response
