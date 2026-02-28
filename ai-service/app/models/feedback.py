from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .base import Base

class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_log_id = Column(UUID(as_uuid=True), ForeignKey("ai_audit_logs.id"), nullable=False)
    
    # User Context
    doctor_id = Column(String(100), nullable=False)
    rating = Column(Integer) # 1-5 scale
    is_clinically_accurate = Column(Boolean, default=True)
    
    # Comments
    comment = Column(Text)
    suggested_correction = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class QueryFailure(Base):
    __tablename__ = "ai_query_failures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    error_type = Column(String(50)) # 'no_context', 'low_confidence', 'timeout'
    
    # Metadata for gap detection
    department = Column(String(100))
    retrieved_doc_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
