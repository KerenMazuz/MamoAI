"""
Agent 1: File Manager
Handles patient context loading and session result saving.
Pure Python logic — no LLM call needed; uses the database layer directly.
"""
import json
from typing import Optional

from config import TRACKS
from database import db
from database.models import Patient, Session, Anchor, Pattern


def load_patient_context(patient_id: str) -> dict:
    """
    Load all historical data for a patient and generate a context card.

    Returns:
        {
            "patient": Patient,
            "context_card": str (Hebrew formatted card),
            "sessions": List[Session],
            "anchors": List[Anchor],
            "patterns": List[Pattern],
            "previous_questions": List[str],
            "previous_interventions": List[str],
            "session_count": int,
            "anchor_count": int,
        }
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    sessions = db.get_sessions(patient_id)
    anchors = db.get_anchors(patient_id)
    patterns = db.get_patterns(patient_id)

    # Collect all previously used questions and interventions
    previous_questions = []
    previous_interventions = []
    for s in sessions:
        if s.question_bank:
            try:
                qb = json.loads(s.question_bank)
                previous_questions.extend(q.get("question", "") for q in qb)
            except (json.JSONDecodeError, AttributeError):
                pass
        if s.interventions:
            try:
                ivs = json.loads(s.interventions)
                previous_interventions.extend(iv.get("name", "") for iv in ivs)
            except (json.JSONDecodeError, AttributeError):
                pass

    context_card = _build_context_card(patient, sessions, anchors, patterns)

    return {
        "patient": patient,
        "context_card": context_card,
        "sessions": sessions,
        "anchors": [
            {"description": a.description, "strength": a.strength}
            for a in anchors
        ],
        "patterns": [
            {"description": p.description, "category": p.category, "occurrences": p.occurrences}
            for p in patterns
        ],
        "previous_questions": previous_questions,
        "previous_interventions": previous_interventions,
        "session_count": patient.session_count,
        "anchor_count": patient.anchor_count,
    }


def _build_context_card(
    patient: Patient,
    sessions: list,
    anchors: list,
    patterns: list,
) -> str:
    if not sessions:
        return ""

    track_label = TRACKS.get(patient.track, patient.track)
    session_num = patient.session_count + 1

    # Top recurring pattern
    top_pattern = patterns[0].description if patterns else "לא זוהו דפוסים עדיין"

    # Last session memory snippet
    last_session = sessions[-1]
    last_memory = ""
    if last_session.original_text:
        snippet = last_session.original_text[:80].strip().replace("\n", " ")
        last_memory = f'"{snippet}..."'

    # Anchor list
    anchor_labels = [a.description for a in anchors[:5]]
    anchor_text = " | ".join(anchor_labels) if anchor_labels else "אין עדיין"

    # Previous session dates
    session_dates = []
    for s in sessions[-3:]:
        if s.created_at:
            date_part = str(s.created_at)[:10]
            session_dates.append(f"פגישה {s.session_number} ({date_part})")
    sessions_text = " | ".join(session_dates) if session_dates else ""

    card = f"""📋 **פגישה {session_num} עם {patient.id}**
גיל: {patient.age} | מסלול: {track_label} | {patient.anchor_count} עוגנים חיוביים
{"כינוי: " + patient.alias if patient.alias else ""}

ערוץ חוזר: {top_pattern}
זיכרון מפגש אחרון: {last_memory}
עוגנים שנצברו: {anchor_text}
{sessions_text}"""

    return card.strip()


def save_session_results(
    patient_id: str,
    session_number: int,
    original_text: str,
    enriched_package: dict,
    interpretation: dict,
    plan: dict,
    track: str,
) -> int:
    """
    Persist all session data to SQLite.
    Returns the new session_id.
    """
    session = Session(
        patient_id=patient_id,
        session_number=session_number,
        original_text=original_text,
        enriched_text=enriched_package.get("enriched_memory", ""),
        countertransference=json.dumps(
            enriched_package.get("countertransference", {}), ensure_ascii=False
        ),
        intersubjective=json.dumps(
            enriched_package.get("intersubjective"), ensure_ascii=False
        ) if enriched_package.get("intersubjective") else None,
        hypotheses=json.dumps(
            interpretation.get("hypotheses", []), ensure_ascii=False
        ),
        track_used=track,
        interventions=json.dumps(
            plan.get("interventions", []), ensure_ascii=False
        ),
        question_bank=json.dumps(
            plan.get("question_bank", []), ensure_ascii=False
        ),
        homework=plan.get("homework", {}).get("task", "") if isinstance(plan.get("homework"), dict) else "",
        summary=plan.get("session_summary", ""),
    )

    session_id = db.save_session(session)

    # Save new anchors
    for anchor in plan.get("anchors", []):
        if anchor.get("description"):
            db.add_anchor(
                patient_id=patient_id,
                session_id=session_id,
                description=anchor["description"],
                strength=anchor.get("strength", "emerging"),
            )

    # Save new patterns
    for pattern in plan.get("patterns", {}).get("new", []):
        if pattern.get("description"):
            db.add_pattern(
                patient_id=patient_id,
                description=pattern["description"],
                category=pattern.get("category", "other"),
                session_number=session_number,
            )

    return session_id
