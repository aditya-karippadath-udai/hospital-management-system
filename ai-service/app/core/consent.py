from typing import Dict, Any
from fastapi import HTTPException, status

class ConsentService:
    """
    Ensures Patients have active consent for AI interactions.
    In prod, this would check a 'consents' table in PostgreSQL.
    """
    
    @staticmethod
    def verify_ai_consent(user: Dict[str, Any]):
        """
        Check if patient-role users have consented to AI processing.
        """
        if user.get("role") == "patient":
            # Mocking DB check for 'has_consented_to_ai'
            has_consented = user.get("has_consent", False) 
            if not has_consented:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="AI Medical Consent not found. Please sign the disclosure in the patient portal."
                )
        return True

    @staticmethod
    def get_data_isolation_filter(user: Dict[str, Any]):
        """
        Enforce patient-data isolation. 
        Patients can only see their own records.
        Doctors can see records within their assigned building/dept.
        """
        role = user.get("role")
        user_id = user.get("sub") # User ID from JWT
        
        if role == "patient":
            return {"patient_id": user_id} # Narrowest scope
        if role == "doctor":
            return {"department": user.get("department")} # Dept scope
            
        return {} # Broad scope for Admins
