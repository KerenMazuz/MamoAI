"""
Financial Agent 1: Organizer
Receives a raw financial data table (from an uploaded Excel/CSV file, plus
optional user-filled additions) and maps it into a unified JSON structure
covering income, expenses (ongoing/periodic/future one-time), savings,
emergency fund, retirement, insurance, and free capital.
"""
import json
from pathlib import Path

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "financial_organizer_system.txt").read_text(encoding="utf-8")


class FinancialOrganizer:
    def __init__(self):
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def organize(self, raw_table: str, manual_additions: dict | None = None) -> dict:
        """
        Args:
            raw_table: the uploaded data, rendered as text (e.g. CSV/markdown table)
            manual_additions: optional dict of user-filled values for categories
                               that were missing from the uploaded file

        Returns:
            dict matching the schema described in financial_organizer_system.txt
        """
        manual_text = ""
        if manual_additions:
            manual_text = (
                "\n\nהשלמות שהמשתמש מילא ידנית עבור קטגוריות חסרות:\n"
                + json.dumps(manual_additions, ensure_ascii=False, indent=2)
            )

        prompt = f"""הנתונים הגולמיים שהועלו:

{raw_table}
{manual_text}

מפה את הנתונים האלה למבנה ה-JSON המבוקש."""

        response = self._client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        return json.loads(response.choices[0].message.content)
