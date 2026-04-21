from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Patient:
    id: str                          # 'P-XXXX'
    age: int
    track: str                       # 'psychodynamic'|'narrative'|'strengths'|'integrative'
    alias: Optional[str] = None
    anchor_count: int = 0
    session_count: int = 0
    created_at: Optional[str] = None


@dataclass
class Session:
    patient_id: str
    session_number: int
    original_text: str
    id: Optional[int] = None
    enriched_text: Optional[str] = None
    countertransference: Optional[str] = None   # JSON string
    intersubjective: Optional[str] = None       # JSON string, nullable
    hypotheses: Optional[str] = None            # JSON string
    track_used: Optional[str] = None
    interventions: Optional[str] = None         # JSON string
    question_bank: Optional[str] = None         # JSON string
    homework: Optional[str] = None
    summary: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Anchor:
    patient_id: str
    session_id: int
    description: str
    strength: str                    # 'strong'|'moderate'|'emerging'
    id: Optional[int] = None


@dataclass
class Pattern:
    patient_id: str
    description: str
    category: str                    # 'figure'|'emotion'|'body'|'movement'|'containment'|'other'
    first_seen_session: int
    last_seen_session: int
    occurrences: int = 1
    id: Optional[int] = None
