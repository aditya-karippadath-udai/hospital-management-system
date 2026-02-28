from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum
from .base import Base

class DocumentType(enum.Enum):
    CLINICAL_GUIDELINE = "clinical_guideline"
    DRUG_INFO = "drug_info"
    HOSPITAL_SOP = "hospital_sop"
    DOCTOR_NOTE = "doctor_note"
    PATIENT_HISTORY = "patient_history"

class AccessLevel(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    PUBLIC = "public"

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    doc_type = Column(Enum(DocumentType), nullable=False)
    department = Column(String(100), index=True) # e.g., 'Cardiology', 'ER'
    
    # Metadata for filtering
    access_level_required = Column(Enum(AccessLevel), default=AccessLevel.DOCTOR)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), nullable=False)
    
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False) # The raw text content
    
    # PHI Scrubbing flag
    is_scrubbed = Column(Boolean, default=False)
    
    # Metadata for audit
    author_id = Column(String(100)) # ID from Flask ERP
    change_summary = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("KnowledgeDocument", back_populates="versions")

    # Ensure uniqueness of version number per document
    __table_args__ = (
        # UniqueConstraint('document_id', 'version_number', name='_doc_version_uc'),
    )
