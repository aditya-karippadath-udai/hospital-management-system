import re
import logging
from typing import str

logger = logging.getLogger(__name__)

class PHIScrubber:
    """
    Detects and masks Protected Health Information (PHI).
    Used before ingestion and before sending context to LLM.
    """
    
    # Common PHI Patterns
    PATTERNS = {
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "PHONE": r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b",
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "DOB": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
        "NAME_INDICATOR": r"(?i)(?:patient|mr\.|ms\.|mrs\.|dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    }

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Scan text and replace PHI with generic placeholders.
        """
        if not text:
            return text
            
        redacted_text = text
        
        # Redact standardized patterns
        for label, pattern in cls.PATTERNS.items():
            redacted_text = re.sub(pattern, f"[REDACTED_{label}]", redacted_text)
            
        return redacted_text

    @classmethod
    def has_high_risk_phi(cls, text: str) -> bool:
        """
        Determine if text contains unmasked critical PHI.
        """
        for pattern in cls.PATTERNS.values():
            if re.search(pattern, text):
                return True
        return False
