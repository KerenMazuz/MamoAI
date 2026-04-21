"""
Agent 3: Lens Interpreter
Direct Anthropic SDK call — receives enriched memory package, RAG chunks,
and returns theoretical hypotheses.
"""
import json
from pathlib import Path
from typing import List

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "agent3_system.txt").read_text(encoding="utf-8")


class LensInterpreter:
    def __init__(self):
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def interpret(
        self,
        enriched_package: dict,
        track: str,
        rag_chunks: List[str],
    ) -> dict:
        """
        Generate 1-2 theoretical hypotheses for the enriched memory.

        Args:
            enriched_package: Output from MemoryDeepener.get_structured_output()
            track: 'psychodynamic'|'narrative'|'strengths'|'integrative'
            rag_chunks: Relevant text chunks from ChromaDB

        Returns:
            dict with keys: track_used, lenses_applied, hypotheses,
                            symbolization, alternative_story, lunar_eclipse,
                            transference_reflection
        """
        rag_context = "\n\n---\n\n".join(rag_chunks) if rag_chunks else "(אין חומר תיאורטי זמין)"

        enriched_memory = enriched_package.get("enriched_memory", "")
        countertransference = enriched_package.get("countertransference", {})
        intersubjective = enriched_package.get("intersubjective", "")
        movement_notes = enriched_package.get("movement_notes", "")

        ct_text = json.dumps(countertransference, ensure_ascii=False, indent=2) if isinstance(countertransference, dict) else str(countertransference)

        prompt = f"""המסלול התיאורטי שנבחר: {track}

זיכרון מועשר:
{enriched_memory}

אלמנטי תנועה שזוהו:
{movement_notes}

נתוני העברה נגדית של המטפל/ת:
{ct_text}

תצפיות שדה בין-סובייקטיבי:
{intersubjective or "(לא סופק)"}

חומר תיאורטי רלוונטי מבסיס הידע:
{rag_context}

---
אנא צור/י {1 if track != "integrative" else 2} עד 2 פרשנויות תיאורטיות לפי הפורמט שהוגדר.
זכור/י: מקסימום 2 עדשות. הכל בגדר "קריאה אפשרית". אין אבחנות.
החזר/י JSON בלבד."""

        response = self._client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=2048,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content.strip()
        return self._parse_output(raw, track)

    def _parse_output(self, raw: str, track: str) -> dict:
        try:
            text = raw
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            result = json.loads(text)
            # Enforce max 2 lenses
            if len(result.get("hypotheses", [])) > 2:
                result["hypotheses"] = result["hypotheses"][:2]
            return result
        except (json.JSONDecodeError, KeyError):
            return {
                "track_used": track,
                "lenses_applied": [],
                "hypotheses": [{"lens": "unknown", "title": "פרשנות", "reading": raw, "key_question": ""}],
                "symbolization": "",
                "alternative_story": "",
                "lunar_eclipse": {"child_feelings": "", "adult_feelings": "", "differentiation_question": ""},
                "transference_reflection": "",
            }
