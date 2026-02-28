import os
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Triggers real-time alerts for hospital staff during emergencies.
    """
    
    # In prod, these would be webhook URLs or SMS/Pager gateway APIs
    DOCTOR_ALERT_WEBHOOK = os.getenv("DOCTOR_ALERT_WEBHOOK")
    ADMIN_ALERT_WEBHOOK = os.getenv("ADMIN_ALERT_WEBHOOK")

    @classmethod
    def trigger_emergency_alert(cls, user_info: Dict[str, Any], symptoms: list, query: str):
        """
        Notify appropriate medical personnel of an emergency AI interaction.
        """
        user_id = user_info.get("sub", "Unknown")
        role = user_info.get("role", "patient")
        
        payload = {
            "type": "EMERGENCY_AI_TRIAGE",
            "priority": "P0",
            "details": {
                "user_id": user_id,
                "role": role,
                "detected_symptoms": symptoms,
                "raw_query": query
            },
            "timestamp": "auto"
        }

        logger.critical(f"EMERGENCY TRIGGERED by user {user_id}. Symptoms: {symptoms}")

        # Send to Doctor Dashboard (via ERP webhook)
        if cls.DOCTOR_ALERT_WEBHOOK:
            try:
                requests.post(cls.DOCTOR_ALERT_WEBHOOK, json=payload, timeout=2)
            except Exception as e:
                logger.error(f"Doctor notification failed: {e}")

        # Send to Admin/Safety Monitor
        if cls.ADMIN_ALERT_WEBHOOK:
            try:
                requests.post(cls.ADMIN_ALERT_WEBHOOK, json=payload, timeout=2)
            except Exception as e:
                logger.error(f"Admin notification failed: {e}")
                
        return True
