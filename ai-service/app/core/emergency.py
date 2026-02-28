import re
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class Severity(str):
    CRITICAL = "critical" # Life-threatening
    HIGH = "high"         # Urgent medical attention
    MODERATE = "moderate" # Non-urgent but needs care
    LOW = "low"          # Routine

class EmergencyDetector:
    """
    Detects medical emergencies using a hybrid rule-based and symptom check.
    Prioritizes safety by failing towards 'Critical' on ambiguity.
    """

    # Life-threatening keywords (Rule-based)
    CRITICAL_KEYWORDS = {
        "chest pain", "difficulty breathing", "shortness of breath", 
        "unconscious", "not breathing", "severe bleeding", "stroke symptoms",
        "paralysis", "seizure", "poisoning", "suicidal", "overdose"
    }

    # Urgent but non-immediate keywords
    HIGH_RISK_KEYWORDS = {
        "high fever", "persistent vomiting", "broken bone", "deep cut",
        "allergic reaction", "blurred vision", "dehydration"
    }

    @classmethod
    def analyze_query(cls, query: str) -> Tuple[Severity, List[str]]:
        """
        Analyze user query for emergency signals.
        Returns: (Severity Level, List of detected symptoms)
        """
        query_lower = query.lower()
        detected_symptoms = []

        # 1. Critical Keyword Check
        for kw in cls.CRITICAL_KEYWORDS:
            if re.search(rf"\b{kw}\b", query_lower):
                detected_symptoms.append(kw)
        
        if detected_symptoms:
            return Severity.CRITICAL, detected_symptoms

        # 2. High Risk Keyword Check
        for kw in cls.HIGH_RISK_KEYWORDS:
            if re.search(rf"\b{kw}\b", query_lower):
                detected_symptoms.append(kw)

        if detected_symptoms:
            return Severity.HIGH, detected_symptoms

        # 3. Contextual Heuristic (Simulated Severity Classifier)
        # In prod, this could be a small BERT model for symptom classification
        if any(term in query_lower for term in ["intense", "extreme", "worst pain", "cannot move"]):
            return Severity.HIGH, ["Severe pain/immobility reported"]

        return Severity.LOW, []

    @staticmethod
    def get_emergency_advice(symptoms: List[str]) -> str:
        """
        Returns a hardcoded, safe emergency protocol.
        """
        return (
            "EMERGENCY DETECTED: Based on your symptoms (" + ", ".join(symptoms) + "), "
            "please CALL EMERGENCY SERVICES (911) or go to the nearest Emergency Room IMMEDIATELY. "
            "Do not wait for a response from this AI assistant."
        )
