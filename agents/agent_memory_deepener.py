"""
Agent 2: Memory Deepener
Runs as a direct Anthropic SDK conversation (outside CrewAI) so it can be
driven interactively through the Streamlit UI.
"""
import json
from pathlib import Path
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "agent2_system.txt").read_text(encoding="utf-8")
_PHASE_COMPLETE_TAG = "[PHASE_COMPLETE]"


class MemoryDeepener:
    """
    Stateful conversational agent for 3-phase memory exploration.

    Usage:
        md = MemoryDeepener()
        q = md.start_phase_a(original_text, context_card, patient_history)
        # show q to therapist, collect answer
        q = md.continue_phase_a(answer)   # None → phase done
        ...
        output = md.get_structured_output()
    """

    def __init__(self):
        self._client = OpenAI(api_key=OPENAI_API_KEY)
        self._messages: list = []
        self._phase = None
        self._phase_a_complete = False
        self._phase_b_complete = False
        self._original_text = ""
        self._context_card = ""

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _chat(self, user_content: str) -> str:
        self._messages.append({"role": "user", "content": user_content})
        response = self._client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=1024,
            messages=[{"role": "system", "content": _SYSTEM_PROMPT}] + self._messages,
        )
        assistant_text = response.choices[0].message.content
        self._messages.append({"role": "assistant", "content": assistant_text})
        return assistant_text

    def _is_phase_complete(self, response: str) -> bool:
        return _PHASE_COMPLETE_TAG in response

    def _clean_response(self, response: str) -> str:
        return response.replace(_PHASE_COMPLETE_TAG, "").strip()

    # ------------------------------------------------------------------ #
    # Phase A — Memory Expansion
    # ------------------------------------------------------------------ #

    def start_phase_a(
        self,
        original_text: str,
        context_card: str = "",
        patient_history: str = "",
    ) -> str:
        self._original_text = original_text
        self._context_card = context_card
        self._phase = "a"

        intro = f"""אנחנו מתחילים שלב א׳ — הרחבת הזיכרון.

הזיכרון שהועלה על ידי המטפל/ת:
---
{original_text}
---
"""
        if context_card:
            intro += f"\nהקשר מפגישות קודמות:\n{context_card}\n"

        intro += "\nאנא שאל/י את השאלה הראשונה להרחבת הזיכרון."
        response = self._chat(intro)
        return self._clean_response(response)

    def continue_phase_a(self, answer: str) -> Optional[str]:
        """Returns next question or None when phase is complete."""
        response = self._chat(answer)
        if self._is_phase_complete(response):
            self._phase_a_complete = True
            return None
        return self._clean_response(response)

    # ------------------------------------------------------------------ #
    # Phase B — Countertransference (mandatory)
    # ------------------------------------------------------------------ #

    def start_phase_b(self) -> str:
        self._phase = "b"
        response = self._chat(
            "עברנו לשלב ב׳ — ההעברה הנגדית שלך. זה שלב חובה. "
            "אנא שאל/י את השאלה הראשונה על החוויה הרגשית של המטפל/ת."
        )
        return self._clean_response(response)

    def continue_phase_b(self, answer: str) -> Optional[str]:
        response = self._chat(answer)
        if self._is_phase_complete(response):
            self._phase_b_complete = True
            return None
        return self._clean_response(response)

    # ------------------------------------------------------------------ #
    # Phase C — Intersubjective (optional)
    # ------------------------------------------------------------------ #

    def start_phase_c(self) -> str:
        self._phase = "c"
        response = self._chat(
            "עברנו לשלב ג׳ — השדה הבין-סובייקטיבי (אופציונלי). "
            "אנא שאל/י שאלה אחת על הדינמיקה בין המטפל/ת למטופל/ת."
        )
        return self._clean_response(response)

    def continue_phase_c(self, answer: str) -> Optional[str]:
        response = self._chat(answer)
        if self._is_phase_complete(response):
            return None
        return self._clean_response(response)

    # ------------------------------------------------------------------ #
    # Structured output
    # ------------------------------------------------------------------ #

    def get_structured_output(self, qa_data: dict = None) -> dict:
        """
        Synthesize all conversation into a structured JSON package.
        Uses a fresh OpenAI call with json_object format for clean output.
        qa_data: {"phase_a_qa": [...], "phase_b_qa": [...], "phase_c_qa": [...]}
        """
        qa_data = qa_data or {}
        phase_a = qa_data.get("phase_a_qa", [])
        phase_b = qa_data.get("phase_b_qa", [])
        phase_c = qa_data.get("phase_c_qa", [])

        def format_qa(pairs):
            if not pairs:
                return "(לא סופק)"
            return "\n".join(f"שאלה: {q}\nתשובה: {a}" for q, a in pairs)

        synthesis_prompt = f"""אתה מסכם שיחה קלינית. הנה הנתונים המלאים:

זיכרון מקורי:
{self._original_text}

שלב א׳ — הרחבת הזיכרון:
{format_qa(phase_a)}

שלב ב׳ — העברה נגדית:
{format_qa(phase_b)}

שלב ג׳ — שדה בין-סובייקטיבי:
{format_qa(phase_c)}

סכם לפי מבנה ה-JSON הבא. כל ערך חייב להיות בעברית בלבד:
{{
  "enriched_memory": "הזיכרון המקורי + כל הפרטים שנוספו בשלב א (תיאור מלא, שוטף, עשיר בחושים ובתנועה)",
  "countertransference": {{
    "emotions": "הרגשות שחווה המטפל/ת תוך כדי ההאזנה",
    "body_sensations": "תחושות גוף ומיקומן",
    "personal_resonance": "זיכרונות או תמונות אישיות שעלו",
    "role_identification": "עם מי זוהה המטפל/ת בסצנה",
    "impulses": "דחפים שעלו — להגן, לחבק, לברוח וכד׳",
    "unsaid": "מה הרגיש נוכח אך לא נאמר בפגישה"
  }},
  "intersubjective": "תצפיות על הדינמיקה בין המטפל/ת למטופל/ת (null אם לא סופק)",
  "movement_notes": "אלמנטי תנועה שזוהו בזיכרון — הליכה, ריצה, עמידה, ישיבה, תנוחה גופנית, או היעדרם המשמעותי"
}}"""

        response = self._client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=2000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a clinical data synthesizer. Output valid JSON only, all values in Hebrew."},
                {"role": "user", "content": synthesis_prompt},
            ],
        )
        try:
            return json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError):
            return {
                "enriched_memory": self._original_text,
                "countertransference": {},
                "intersubjective": None,
                "movement_notes": "",
            }

    @property
    def phase_a_complete(self) -> bool:
        return self._phase_a_complete

    @property
    def phase_b_complete(self) -> bool:
        return self._phase_b_complete
