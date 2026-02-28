from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models.kb import KnowledgeDocument, DocumentVersion, AccessLevel, DocumentType
from ..schemas.kb import KBDocumentCreate, KBVersionCreate
import uuid

class KBService:
    @staticmethod
    def create_document(db: Session, doc_data: KBDocumentCreate) -> KnowledgeDocument:
        """Create a new document with its initial version."""
        new_doc = KnowledgeDocument(
            title=doc_data.title,
            doc_type=doc_data.doc_type,
            department=doc_data.department,
            access_level_required=doc_data.access_level_required
        )
        db.add(new_doc)
        db.flush() # Get ID

        initial_version = DocumentVersion(
            document_id=new_doc.id,
            version_number=1,
            content=doc_data.initial_content,
            author_id=doc_data.author_id,
            change_summary="Initial version"
        )
        db.add(initial_version)
        db.commit()
        db.refresh(new_doc)
        return new_doc

    @staticmethod
    def add_version(db: Session, doc_id: uuid.UUID, version_data: KBVersionCreate) -> DocumentVersion:
        """Add a new version to an existing document."""
        # Get latest version number
        latest_version = db.query(DocumentVersion)\
            .filter(DocumentVersion.document_id == doc_id)\
            .order_by(DocumentVersion.version_number.desc())\
            .first()
        
        new_version_num = (latest_version.version_number + 1) if latest_version else 1
        
        new_version = DocumentVersion(
            document_id=doc_id,
            version_number=new_version_num,
            content=version_data.content,
            author_id=version_data.author_id,
            change_summary=version_data.change_summary
        )
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        return new_version

    @staticmethod
    def get_filtered_documents(
        db: Session, 
        user_role: str, 
        department: Optional[str] = None
    ) -> List[KnowledgeDocument]:
        """
        Retrieve documents based on user role and optional department filter.
        Ensures role-based data isolation.
        """
        # Define role priority/visibility
        role_map = {
            "admin": [AccessLevel.ADMIN, AccessLevel.DOCTOR, AccessLevel.NURSE, AccessLevel.PATIENT, AccessLevel.PUBLIC],
            "doctor": [AccessLevel.DOCTOR, AccessLevel.NURSE, AccessLevel.PATIENT, AccessLevel.PUBLIC],
            "nurse": [AccessLevel.NURSE, AccessLevel.PATIENT, AccessLevel.PUBLIC],
            "patient": [AccessLevel.PATIENT, AccessLevel.PUBLIC],
            "receptionist": [AccessLevel.PUBLIC]
        }
        
        allowed_levels = role_map.get(user_role.lower(), [AccessLevel.PUBLIC])
        
        query = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.access_level_required.in_(allowed_levels),
            KnowledgeDocument.is_active == True
        )
        
        if department:
            query = query.filter(KnowledgeDocument.department == department)
            
        return query.all()

    @staticmethod
    def get_document_content(db: Session, doc_id: uuid.UUID, version: Optional[int] = None) -> Optional[str]:
        """Retrieve the content of a specific version or the latest one."""
        query = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc_id)
        
        if version:
            query = query.filter(DocumentVersion.version_number == version)
        else:
            query = query.order_by(DocumentVersion.version_number.desc())
            
        version_obj = query.first()
        return version_obj.content if version_obj else None
