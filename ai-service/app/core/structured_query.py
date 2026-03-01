"""
Structured Query Engine
=======================
Detects ERP-intent queries (doctor availability, appointments, departments)
and routes them to PostgreSQL with parameterised, injection-safe templates.

If an intent is matched the vector search is bypassed entirely and the DB
result is formatted into context that feeds the LLaMA prompt.
"""

import re
import os
import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/hospital_db",
)

_engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
Session = sessionmaker(bind=_engine)


# ─── Intent Definitions ──────────────────────────────────────────────────────

class ERPIntent:
    DOCTOR_AVAILABILITY = "doctor_availability"
    APPOINTMENT_SLOTS   = "appointment_slots"
    DEPARTMENT_LIST     = "department_list"
    NONE                = "none"


_INTENT_PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    (
        ERPIntent.DOCTOR_AVAILABILITY,
        [
            re.compile(r"(?i)(?:which|what|who|any|list|show|find|available)\b.*\b(?:doctor|physician|specialist)s?\b.*\b(?:available|free|on duty)", re.DOTALL),
            re.compile(r"(?i)\b(?:doctor|dr\.?)\b.*\b(?:available|availability|schedule|when|timing)", re.DOTALL),
            re.compile(r"(?i)\b(?:available|free)\b.*\b(?:doctor|physician|specialist)", re.DOTALL),
            re.compile(r"(?i)\bis\s+dr\.?\s+\w+\s+available", re.DOTALL),
        ],
    ),
    (
        ERPIntent.APPOINTMENT_SLOTS,
        [
            re.compile(r"(?i)\b(?:appointment|slot|book|booking|schedule)\b.*\b(?:available|open|free)", re.DOTALL),
            re.compile(r"(?i)\b(?:can i|how to|want to)\b.*\b(?:book|schedule|make)\b.*\b(?:appointment)", re.DOTALL),
            re.compile(r"(?i)\b(?:next|upcoming|open)\b.*\bslots?\b", re.DOTALL),
        ],
    ),
    (
        ERPIntent.DEPARTMENT_LIST,
        [
            re.compile(r"(?i)\b(?:department|departments|specialit(?:y|ies)|specialization|ward|unit)\b.*\b(?:list|available|offer|have|show|what)", re.DOTALL),
            re.compile(r"(?i)\b(?:what|which|list|show)\b.*\b(?:department|specialit)", re.DOTALL),
        ],
    ),
]


# ─── Intent Classifier ───────────────────────────────────────────────────────

def classify_intent(query: str) -> str:
    """Return the ERPIntent constant that best matches *query*, or NONE."""
    for intent, patterns in _INTENT_PATTERNS:
        for pat in patterns:
            if pat.search(query):
                logger.info("StructuredQueryEngine: matched intent=%s", intent)
                return intent
    return ERPIntent.NONE


# ─── Safe DB Query Templates ─────────────────────────────────────────────────
# All queries use SQLAlchemy `text()` with bound parameters — zero SQL-injection risk.

_QUERIES: dict[str, str] = {
    ERPIntent.DOCTOR_AVAILABILITY: """
        SELECT d.id, u.first_name, u.last_name, d.specialization, d.department,
               d.available_days, d.available_time_start, d.available_time_end,
               d.consultation_fee, d.is_available
        FROM doctors d
        JOIN users u ON u.id = d.user_id
        WHERE d.is_available = true
        ORDER BY d.department, u.last_name
        LIMIT 50
    """,

    ERPIntent.APPOINTMENT_SLOTS: """
        SELECT a.appointment_date, a.appointment_time, a.status,
               u.first_name || ' ' || u.last_name AS doctor_name,
               d.specialization, d.department
        FROM appointments a
        JOIN doctors d ON d.id = a.doctor_id
        JOIN users u ON u.id = d.user_id
        WHERE a.appointment_date >= :today
          AND a.status IN ('pending', 'confirmed')
        ORDER BY a.appointment_date, a.appointment_time
        LIMIT 30
    """,

    ERPIntent.DEPARTMENT_LIST: """
        SELECT DISTINCT d.department, d.specialization, COUNT(*) AS doctor_count
        FROM doctors d
        WHERE d.department IS NOT NULL
        GROUP BY d.department, d.specialization
        ORDER BY d.department
    """,
}


# ─── DB Query Executor ───────────────────────────────────────────────────────

def _execute_query(intent: str, role: str, user_id: str | None = None) -> list[dict]:
    """Run the parameterised query for *intent* and return rows as dicts."""
    sql_template = _QUERIES.get(intent)
    if not sql_template:
        return []

    params: dict[str, Any] = {}
    if intent == ERPIntent.APPOINTMENT_SLOTS:
        params["today"] = date.today().isoformat()

    try:
        with Session() as session:
            result = session.execute(text(sql_template), params)
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        logger.error("StructuredQueryEngine DB error: %s", e)
        return []


# ─── Context Builder ─────────────────────────────────────────────────────────

def _build_context(intent: str, rows: list[dict]) -> str:
    """Convert DB rows into a human-readable context block for the LLM."""
    if not rows:
        return "No results found in hospital records for this query."

    if intent == ERPIntent.DOCTOR_AVAILABILITY:
        lines = ["### Available Doctors\n"]
        for r in rows:
            days = r.get("available_days") or "Not specified"
            lines.append(
                f"- **Dr. {r['first_name']} {r['last_name']}** — "
                f"{r['specialization']} ({r['department'] or 'General'})\n"
                f"  Schedule: {days} | "
                f"{r.get('available_time_start', '?')} – {r.get('available_time_end', '?')} | "
                f"Fee: ₹{r.get('consultation_fee', 'N/A')}"
            )
        return "\n".join(lines)

    if intent == ERPIntent.APPOINTMENT_SLOTS:
        lines = ["### Upcoming Appointment Slots\n"]
        for r in rows:
            lines.append(
                f"- {r['appointment_date']} at {r['appointment_time']} — "
                f"Dr. {r['doctor_name']} ({r['specialization']}, {r['department']}) "
                f"[{r['status']}]"
            )
        return "\n".join(lines)

    if intent == ERPIntent.DEPARTMENT_LIST:
        lines = ["### Hospital Departments\n"]
        for r in rows:
            lines.append(
                f"- **{r['department']}** — {r['specialization']} "
                f"({r['doctor_count']} doctor(s))"
            )
        return "\n".join(lines)

    return ""


# ─── Public API ───────────────────────────────────────────────────────────────

def try_structured_query(
    query: str,
    role: str,
    user_id: str | None = None,
) -> tuple[bool, str]:
    """
    Attempt to answer *query* from PostgreSQL.

    Returns
    -------
    (handled, context_text)
        handled=True  → bypass vector search, use context_text for prompt
        handled=False → fall through to normal RAG pipeline
    """
    intent = classify_intent(query)
    if intent == ERPIntent.NONE:
        return False, ""

    rows = _execute_query(intent, role, user_id)
    context = _build_context(intent, rows)

    logger.info(
        "StructuredQueryEngine: intent=%s  rows=%d  role=%s",
        intent, len(rows), role,
    )
    return True, context
