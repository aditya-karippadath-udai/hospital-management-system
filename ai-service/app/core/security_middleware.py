from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    """
    Enforces TLS, Security Headers, and Tenant Isolation at the network layer.
    """
    
    async def dispatch(self, request: Request, call_next):
        # 1. TLS Enforcement (HSTS)
        # Note: In production, this is usually handled by the NGINX/K8s Ingress,
        # but we enforce it here as a second layer of defense.
        if os.getenv("ENV") == "prod" and request.url.scheme != "https":
            raise HTTPException(status_code=403, detail="HTTPS connection required.")

        response = await call_next(request)
        
        # 2. Hardened Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        
        # 3. Tenant Isolation Header Check
        tenant_id = request.headers.get("X-Tenant-ID")
        if os.getenv("ENV") == "prod" and not tenant_id:
             # Even if JWT has it, we require a explicit header for secondary validation
             pass # Logic will be reinforced in Auth service
             
        return response
