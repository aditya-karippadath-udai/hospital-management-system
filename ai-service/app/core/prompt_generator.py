import logging
from typing import List, Dict, Any
from .prompts import (
    DOCTOR_PROMPT_TEMPLATE, 
    PATIENT_PROMPT_TEMPLATE, 
    EMERGENCY_PROMPT_TEMPLATE,
    MEDICATION_SAFETY_PROMPT,
    BASE_SYSTEM_INSTRUCTION,
    PromptRole
)

logger = logging.getLogger(__name__)

class PromptGenerator:
    """
    Assembles secure, grounded prompts for the LLM.
    Enforces 'Context Only' and 'Citations' rules.
    """

    @staticmethod
    def generate(
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        role: str,
        detected_symptoms: List[str] = None
    ) -> str:
        """
        Generate a role-specific, context-grounded prompt.
        """
        # 1. Format Context with Citations
        formatted_context = ""
        for i, chunk in enumerate(context_chunks):
            source = chunk.get("payload", {}).get("title", "Unknown Source")
            content = chunk.get("payload", {}).get("content", "")
            formatted_context += f"--- START SOURCE {i+1}: {source} ---\n{content}\n--- END SOURCE {i+1} ---\n\n"

        # 2. Select Template
        role_type = role.lower()
        
        # Check for emergency symptoms first
        if detected_symptoms:
            return EMERGENCY_PROMPT_TEMPLATE.format(
                system_instruction=BASE_SYSTEM_INSTRUCTION,
                context=formatted_context if formatted_context else "No clinical context available.",
                query=query,
                detected_symptoms=", ".join(detected_symptoms)
            )

        if role_type in ["doctor", "admin"]:
            template = DOCTOR_PROMPT_TEMPLATE
        elif role_type == "patient":
            template = PATIENT_PROMPT_TEMPLATE
        else:
            # Default to patient safety for uncertain roles (Fail Closed)
            template = PATIENT_PROMPT_TEMPLATE

        # 3. Handle Medications (if detected in query)
        if any(term in query.lower() for term in ["dose", "medication", "drug", "dosage", "side effect"]):
            template = MEDICATION_SAFETY_PROMPT

        return template.format(
            system_instruction=BASE_SYSTEM_INSTRUCTION,
            context=formatted_context if formatted_context else "NO CONTEXT PROVIDED. STICK TO DISCLAIMERS.",
            query=query
        )
