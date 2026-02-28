from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .base import Base

class AuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # User Context
    user_id = Column(String(100), index=True)
    role = Column(String(50))
    
    # AI Interaction Data
    query = Column(Text, nullable=False)
    retrieved_docs = Column(JSON) # List of doc IDs/titles
    llm_output = Column(Text)
    
    # Metrics & Safety
    confidence_score = Column(Float)
    risk_level = Column(String(20)) # 'low', 'medium', 'high', 'critical'
    
    # Tamper-Evidence (Hash Chaining)
    previous_hash = Column(String(64), nullable=True) # Hash of the previous log entry
    current_hash = Column(String(64), unique=True, nullable=False) # SHA256 of this entry's content + prev_hash
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.user_id}, risk={self.risk_level})>"
