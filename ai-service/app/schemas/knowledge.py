from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re


ALLOWED_CATEGORIES = {"medicine", "disease", "policy", "doctor", "hospital_info", "procedure", "guideline"}


class KnowledgeAddRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str = Field(..., description="One of: medicine, disease, policy, doctor, hospital_info, procedure, guideline")
    description: str = Field(..., min_length=10, max_length=50_000)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Allowed: {', '.join(sorted(ALLOWED_CATEGORIES))}")
        return v

    @field_validator("title", "description")
    @classmethod
    def sanitize(cls, v: str) -> str:
        """Strip control characters and excessive whitespace."""
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", v)
        v = re.sub(r"\s{3,}", "  ", v)
        return v.strip()


class KnowledgeAddResponse(BaseModel):
    status: str = "success"
    title: str
    category: str
    chunks_stored: int
    total_vectors: int
    duplicates_skipped: int
