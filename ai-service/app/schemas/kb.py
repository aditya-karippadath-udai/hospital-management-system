from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from enum import Enum

class DocumentType(str, Enum):
    CLINICAL_GUIDELINE = "clinical_guideline"
    DRUG_INFO = "drug_info"
    HOSPITAL_SOP = "hospital_sop"
    DOCTOR_NOTE = "doctor_note"
    PATIENT_HISTORY = "patient_history"

class AccessLevel(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    PUBLIC = "public"

class KBVersionBase(BaseModel):
    version_number: int
    content: str
    change_summary: Optional[str] = None
    author_id: str

class KBVersionCreate(KBVersionBase):
    pass

class KBVersionResponse(KBVersionBase):
    id: UUID
    created_at: datetime
    is_scrubbed: bool

    class Config:
        from_attributes = True

class KBDocumentBase(BaseModel):
    title: str
    doc_type: DocumentType
    department: Optional[str] = None
    access_level_required: AccessLevel = AccessLevel.DOCTOR

class KBDocumentCreate(KBDocumentBase):
    initial_content: str
    author_id: str

class KBDocumentResponse(KBDocumentBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class KBDocumentDetail(KBDocumentResponse):
    versions: List[KBVersionResponse]
