import sqlite3
import random
import string
import json
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from config import DB_PATH
from database.models import Patient, Session, Anchor, Pattern


def _ensure_db_dir():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    _ensure_db_dir()
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                alias TEXT,
                age INTEGER,
                track TEXT,
                anchor_count INTEGER DEFAULT 0,
                session_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT REFERENCES patients(id),
                session_number INTEGER,
                original_text TEXT,
                enriched_text TEXT,
                countertransference TEXT,
                intersubjective TEXT,
                hypotheses TEXT,
                track_used TEXT,
                interventions TEXT,
                question_bank TEXT,
                homework TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS anchors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT REFERENCES patients(id),
                session_id INTEGER REFERENCES sessions(id),
                description TEXT,
                strength TEXT
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT REFERENCES patients(id),
                description TEXT,
                category TEXT,
                first_seen_session INTEGER,
                last_seen_session INTEGER,
                occurrences INTEGER DEFAULT 1
            );
        """)


def _generate_patient_id(conn) -> str:
    """Generate a unique P-XXXX patient ID."""
    while True:
        digits = "".join(random.choices(string.digits, k=4))
        candidate = f"P-{digits}"
        existing = conn.execute(
            "SELECT id FROM patients WHERE id = ?", (candidate,)
        ).fetchone()
        if not existing:
            return candidate


def create_patient(age: int, track: str, alias: Optional[str] = None) -> Patient:
    with _get_conn() as conn:
        patient_id = _generate_patient_id(conn)
        conn.execute(
            "INSERT INTO patients (id, alias, age, track) VALUES (?, ?, ?, ?)",
            (patient_id, alias, age, track),
        )
    return Patient(id=patient_id, age=age, track=track, alias=alias)


def get_patient(patient_id: str) -> Optional[Patient]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if not row:
            return None
        return Patient(
            id=row["id"],
            alias=row["alias"],
            age=row["age"],
            track=row["track"],
            anchor_count=row["anchor_count"],
            session_count=row["session_count"],
            created_at=row["created_at"],
        )


def list_patients() -> List[Patient]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM patients ORDER BY created_at DESC"
        ).fetchall()
        return [
            Patient(
                id=r["id"],
                alias=r["alias"],
                age=r["age"],
                track=r["track"],
                anchor_count=r["anchor_count"],
                session_count=r["session_count"],
                created_at=r["created_at"],
            )
            for r in rows
        ]


def save_session(session: Session) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO sessions
               (patient_id, session_number, original_text, enriched_text,
                countertransference, intersubjective, hypotheses, track_used,
                interventions, question_bank, homework, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.patient_id,
                session.session_number,
                session.original_text,
                session.enriched_text,
                session.countertransference,
                session.intersubjective,
                session.hypotheses,
                session.track_used,
                session.interventions,
                session.question_bank,
                session.homework,
                session.summary,
            ),
        )
        session_id = cursor.lastrowid
        conn.execute(
            "UPDATE patients SET session_count = session_count + 1 WHERE id = ?",
            (session.patient_id,),
        )
        return session_id


def get_sessions(patient_id: str) -> List[Session]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE patient_id = ? ORDER BY session_number",
            (patient_id,),
        ).fetchall()
        return [
            Session(
                id=r["id"],
                patient_id=r["patient_id"],
                session_number=r["session_number"],
                original_text=r["original_text"],
                enriched_text=r["enriched_text"],
                countertransference=r["countertransference"],
                intersubjective=r["intersubjective"],
                hypotheses=r["hypotheses"],
                track_used=r["track_used"],
                interventions=r["interventions"],
                question_bank=r["question_bank"],
                homework=r["homework"],
                summary=r["summary"],
                created_at=r["created_at"],
            )
            for r in rows
        ]


def add_anchor(patient_id: str, session_id: int, description: str, strength: str) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO anchors (patient_id, session_id, description, strength) VALUES (?, ?, ?, ?)",
            (patient_id, session_id, description, strength),
        )
        conn.execute(
            "UPDATE patients SET anchor_count = anchor_count + 1 WHERE id = ?",
            (patient_id,),
        )
        return cursor.lastrowid


def get_anchors(patient_id: str) -> List[Anchor]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM anchors WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        ).fetchall()
        return [
            Anchor(
                id=r["id"],
                patient_id=r["patient_id"],
                session_id=r["session_id"],
                description=r["description"],
                strength=r["strength"],
            )
            for r in rows
        ]


def add_pattern(
    patient_id: str,
    description: str,
    category: str,
    session_number: int,
) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO patterns
               (patient_id, description, category, first_seen_session, last_seen_session)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, description, category, session_number, session_number),
        )
        return cursor.lastrowid


def update_pattern(pattern_id: int, session_number: int):
    with _get_conn() as conn:
        conn.execute(
            """UPDATE patterns
               SET occurrences = occurrences + 1, last_seen_session = ?
               WHERE id = ?""",
            (session_number, pattern_id),
        )


def get_patterns(patient_id: str) -> List[Pattern]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM patterns WHERE patient_id = ? ORDER BY occurrences DESC",
            (patient_id,),
        ).fetchall()
        return [
            Pattern(
                id=r["id"],
                patient_id=r["patient_id"],
                description=r["description"],
                category=r["category"],
                first_seen_session=r["first_seen_session"],
                last_seen_session=r["last_seen_session"],
                occurrences=r["occurrences"],
            )
            for r in rows
        ]
