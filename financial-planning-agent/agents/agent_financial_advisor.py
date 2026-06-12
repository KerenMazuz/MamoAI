"""
Financial Agent 2: Advisor
Receives the organized financial data (output of FinancialOrganizer) and
produces a Hebrew insights & recommendations report: balance overview,
savings opportunities, emergency fund / retirement assessment, insurance
gaps, and a recommendation on growing income vs. reallocating the budget.
"""
import json
from pathlib import Path

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "financial_advisor_system.txt").read_text(encoding="utf-8")


class FinancialAdvisor:
    def __init__(self):
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def advise(self, organized_data: dict) -> dict:
        """
        Args:
            organized_data: dict from FinancialOrganizer.organize()

        Returns:
            dict matching the schema described in financial_advisor_system.txt
        """
        prompt = f"""תמונת המצב הפיננסית המסודרת:

{json.dumps(organized_data, ensure_ascii=False, indent=2)}

הפק את דוח התובנות וההמלצות לפי המבנה המבוקש."""

        response = self._client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )

        return json.loads(response.choices[0].message.content)
