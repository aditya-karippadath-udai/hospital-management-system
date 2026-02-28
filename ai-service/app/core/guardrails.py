import re
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class GuardrailService:
    """
    Intercepts and analyzes prompts for injection attacks.
    Fail-closed on security uncertainty.
    """
    
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+all\s+(?:previous|above)\s+instructions",
        r"(?i)system\s+override",
        r"(?i)you\s+are\s+now\s+a\b",
        r"(?i)new\s+role\b",
        r"(?i)reveal\s+your\s+system\s+prompt",
        r"(?i)output\s+the\s+identity\s+of\s+other\s+users",
        r"(?i)base64\s+decode",
        r"(?i)execute\s+code",
        r"(?i)sql\s+injection"
    ]

    @classmethod
    def validate_prompt(cls, query: str):
        """
        Scan query for known jailbreak and injection strings.
        """
        if not query:
            return True
            
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, query):
                logger.critical(f"PROMPT INJECTION DETECTED: {pattern} in query: {query}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Security Policy Violation: Malicious instruction patterns detected."
                )
        
        # Check for excessive length (potential buffer/context stuffing)
        if len(query) > 2000:
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="Query exceeds maximum allowed length for security reasons."
            )
            
        return True
