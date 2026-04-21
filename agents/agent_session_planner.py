"""
Agent 4: Session Planner
Direct Anthropic SDK call — generates all therapist-facing deliverables.
"""
import json
from pathlib import Path
from typing import List

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "agent4_system.txt").read_text(encoding="utf-8")


class SessionPlanner:
    def __init__(self):
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def plan(
        self,
        interpretation: dict,
        enriched_package: dict,
        patient_history: dict,
        track: str,
        qa_data: dict = None,
        rag_chunks: List[str] = None,
    ) -> dict:
        """
        Generate all session deliverables.

        Args:
            interpretation: Output from LensInterpreter.interpret()
            enriched_package: Output from MemoryDeepener.get_structured_output()
            patient_history: Context from Agent 1
            track: Selected therapeutic track
            qa_data: Full Q&A from all phases {"phase_a_qa": [...], ...}
            rag_chunks: Optional additional RAG context
        """
        qa_data = qa_data or {}

        def format_qa(pairs):
            if not pairs:
                return "(לא סופק)"
            return "\n".join(f"  שאלה: {q}\n  תשובה: {a}" for q, a in pairs)

        phase_a_text = format_qa(qa_data.get("phase_a_qa", []))
        phase_b_text = format_qa(qa_data.get("phase_b_qa", []))
        phase_c_text = format_qa(qa_data.get("phase_c_qa", []))

        interp_text = json.dumps(interpretation, ensure_ascii=False, indent=2)

        prev_questions = patient_history.get("previous_questions", [])[-5:]
        prev_interventions = patient_history.get("previous_interventions", [])[-3:]
        prev_patterns = patient_history.get("patterns", [])[-5:]
        prev_anchors = patient_history.get("anchors", [])[-5:]
        session_number = patient_history.get("session_count", 1) + 1

        prev_q_text = "\n".join(f"- {q}" for q in prev_questions) if prev_questions else "אין שאלות קודמות"
        prev_i_text = "\n".join(f"- {i}" for i in prev_interventions) if prev_interventions else "אין התערבויות קודמות"
        prev_p_text = json.dumps(prev_patterns, ensure_ascii=False) if prev_patterns else "[]"
        prev_a_text = json.dumps(prev_anchors, ensure_ascii=False) if prev_anchors else "[]"

        prompt = f"""מפגש מספר: {session_number}
מסלול: {track}

=== פרשנות תיאורטית (Agent 3) ===
{interp_text}

שאלות שנשאלו בפגישות קודמות (אל תחזור עליהן):
{prev_q_text}

התערבויות שהשתמשו בהן (אל תחזור עליהן):
{prev_i_text}

דפוסים שנצברו:
{prev_p_text}

עוגנים שנצברו:
{prev_a_text}

---
אנא צור/י את כל הפלטים לפי הפורמט שהוגדר. החזר/י JSON בלבד."""

        response = self._client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=3000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content.strip()
        return self._parse_output(raw)

    def _parse_output(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, KeyError):
            return {
                "session_summary": raw,
                "question_bank": [],
                "interventions": [],
                "homework": {"task": "", "rationale": "", "options": []},
                "patterns": {"new": [], "accumulated": []},
                "transference_reflection": "",
                "anchors": [],
            }
