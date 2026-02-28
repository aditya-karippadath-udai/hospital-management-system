import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthService:
    """
    Handles JWT decryption and role verification.
    Accepts tokens from Flask ERP (Shared Secret).
    """
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-prod")
    ALGORITHM = "HS256"

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        Validate JWT and return payload.
        Fail closed on any uncertainty.
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            
            # Mandatory Claims Check
            if "role" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token missing role claim"
                )
                
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(e)}"
            )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
) -> Dict[str, Any]:
    """FastAPI Dependency for extracting user from token."""
    return AuthService.verify_token(credentials.credentials)

class RBAC:
    """Role-Based Access Control Utilities."""
    
    @staticmethod
    def check_permissions(user: Dict[str, Any], required_roles: list):
        """Enforce role scope. Fail closed if role not in allowed list."""
        user_role = user.get("role", "public").lower()
        if user_role not in [r.lower() for r in required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Resource requires roles: {required_roles}. Your role: {user_role}"
            )
        return True
