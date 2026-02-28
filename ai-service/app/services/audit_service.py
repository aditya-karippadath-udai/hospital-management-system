import hashlib
import json
import logging
import requests
import os
from sqlalchemy.orm import Session
from datetime import datetime
from .audit import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """
    Handles append-only cryptographic logging and external SIEM alerts.
    """
    
    SIEM_WEBHOOK_URL = os.getenv("SIEM_WEBHOOK_URL")

    @classmethod
    def log_interaction(
        cls, 
        db: Session,
        user_id: str,
        role: str,
        query: str,
        retrieved_docs: list,
        llm_output: str,
        confidence_score: float,
        risk_level: str
    ) -> AuditLog:
        """
        Record an AI interaction with tamper-evident hash chaining.
        """
        # 1. Get the previous hash
        last_log = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
        prev_hash = last_log.current_hash if last_log else "0" * 64

        # 2. Create entry (Pre-hash)
        new_log = AuditLog(
            user_id=user_id,
            role=role,
            query=query,
            retrieved_docs=retrieved_docs,
            llm_output=llm_output,
            confidence_score=confidence_score,
            risk_level=risk_level,
            previous_hash=prev_hash,
            current_hash="PENDING" # Placeholder
        )

        # 3. Generate Cryptographic Hash (Content + Prev Hash)
        log_data = f"{new_log.timestamp}|{user_id}|{query}|{llm_output}|{prev_hash}"
        new_log.current_hash = hashlib.sha256(log_data.encode()).hexdigest()

        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        # 4. Process Alerts
        if risk_level in ["high", "critical"]:
            cls._trigger_security_alert(new_log)

        return new_log

    @classmethod
    def _trigger_security_alert(cls, log: AuditLog):
        """Send urgent notification to SIEM/Security team."""
        alert_payload = {
            "alert": "CRITICAL_AI_RISK",
            "severity": "high" if log.risk_level == "high" else "critical",
            "user_id": log.user_id,
            "query": log.query[:100],
            "log_id": str(log.id),
            "timestamp": log.timestamp.isoformat()
        }
        
        logger.warning(f"SECURITY ALERT: Risky AI output detected for user {log.user_id}")
        
        if cls.SIEM_WEBHOOK_URL:
            try:
                requests.post(cls.SIEM_WEBHOOK_URL, json=alert_payload, timeout=2)
            except Exception as e:
                logger.error(f"Failed to send SIEM alert: {e}")

    @staticmethod
    def verify_chain_integrity(db: Session) -> bool:
        """
        Audit the entire chain for tampering.
        Validates that each entry's 'previous_hash' matches the actual previous record.
        """
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.asc()).all()
        for i in range(1, len(logs)):
            if logs[i].previous_hash != logs[i-1].current_hash:
                logger.critical(f"AUDIT TAMPER DETECTED at log ID: {logs[i].id}")
                return False
        return True
