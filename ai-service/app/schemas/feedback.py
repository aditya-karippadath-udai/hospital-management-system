from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class FeedbackCreate(BaseModel):
    audit_log_id: UUID
    rating: int = Field(..., ge=1, le=5)
    is_clinically_accurate: bool
    comment: Optional[str] = None
    suggested_correction: Optional[str] = None

class FeedbackResponse(FeedbackCreate):
    id: UUID
    created_at: datetime
    doctor_id: str

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_queries: int
    avg_rating: float
    accuracy_rate: float
    failure_rate: float
    failures_by_dept: dict
