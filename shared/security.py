import time
import jwt
import os

class ServiceAuth:
    """
    Handles secure authentication between Flask ERP and FastAPI AI microservice.
    Uses short-lived JWTs signed with a shared secret.
    """
    SECRET = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-prod")
    ALGORITHM = "HS256"

    @classmethod
    def generate_token(cls, service_name: str, exp_seconds: int = 60):
        """Generate a short-lived token for internal service requests."""
        payload = {
            "iss": "hms-internal",
            "sub": service_name,
            "iat": int(time.time()),
            "exp": int(time.time()) + exp_seconds
        }
        return jwt.encode(payload, cls.SECRET, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_token(cls, token: str):
        """Verify the internal service token."""
        try:
            payload = jwt.decode(token, cls.SECRET, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.PyJWTError:
            return None
