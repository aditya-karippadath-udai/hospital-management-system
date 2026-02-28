from sqlalchemy.orm import Session
from sqlalchemy import func
from .feedback import AIFeedback, QueryFailure
from .audit import AuditLog
from ..schemas.feedback import FeedbackCreate, AnalyticsSummary
import logging

logger = logging.getLogger(__name__)

class FeedbackService:
    @staticmethod
    def submit_feedback(db: Session, doctor_id: str, data: FeedbackCreate) -> AIFeedback:
        """Record doctor feedback and check for improvement triggers."""
        feedback = AIFeedback(
            audit_log_id=data.audit_log_id,
            doctor_id=doctor_id,
            rating=data.rating,
            is_clinically_accurate=data.is_clinically_accurate,
            comment=data.comment,
            suggested_correction=data.suggested_correction
        )
        db.add(feedback)
        
        # Trigger re-evaluation if accuracy is low
        if not data.is_clinically_accurate:
            logger.warning(f"Inaccurate AI response reported by Dr. {doctor_id} | Audit ID: {data.audit_log_id}")
            # Potential re-embedding trigger logic here
            
        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def log_failure(db: Session, query: str, error_type: str, dept: str = None):
        """Track queries where the AI failed to provide a valid answer."""
        failure = QueryFailure(
            query=query,
            error_type=error_type,
            department=dept
        )
        db.add(failure)
        db.commit()

    @staticmethod
    def get_analytics(db: Session) -> AnalyticsSummary:
        """Calculate performance metrics for the Admin Dashboard."""
        total_q = db.query(AuditLog).count()
        avg_r = db.query(func.avg(AIFeedback.rating)).scalar() or 0.0
        
        # Accuracy Rate
        accurate_count = db.query(AIFeedback).filter(AIFeedback.is_clinically_accurate == True).count()
        feedback_count = db.query(AIFeedback).count()
        accuracy_rate = (accurate_count / feedback_count) if feedback_count > 0 else 1.0
        
        # Failure Rate
        failure_count = db.query(QueryFailure).count()
        failure_rate = (failure_count / total_q) if total_q > 0 else 0.0
        
        return AnalyticsSummary(
            total_queries=total_q,
            avg_rating=round(float(avg_r), 2),
            accuracy_rate=round(accuracy_rate, 2),
            failure_rate=round(failure_rate, 2),
            failures_by_dept={} # Future: Group by dept
        )
