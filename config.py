import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-4o"

DB_PATH = str(BASE_DIR / "database" / "therapist_bot.db")
CHROMA_PATH = str(BASE_DIR / "rag" / "chroma_db")
RAG_DATA_PATH = str(BASE_DIR / "RAG data")

# ChromaDB collection names
COLLECTIONS = {
    "psychodynamic": "psychodynamic",
    "narrative": "narrative",
    "strengths": "strengths",
    "shared": "shared",
    "integrative": "integrative",
}

# PDF file → ChromaDB collection mapping
PDF_COLLECTION_MAP = {
    "זיכרונות ילדות מוקדמים - חוזקות.pdf": "strengths",
    "זיכרונות ילדות מוקדמים- אנליזה ארגונית.pdf": "psychodynamic",
    "זכרונות ילדות- מרואן דוירי.pdf": "psychodynamic",
    "זכרונות מוקדמים- טיפול נרטיבי.pdf": "narrative",
    "זכרונות- מחקר- הפרעות קשב.pdf": "shared",
    "זכרונות- רחל שפרון- הדרכה.pdf": "narrative",
    "חוברת מאמרים - זכרונות ילדות.pdf": "shared",
    "מאמר- זיכרונות- פסיכותירפיה ממוקדת.pdf": "psychodynamic",
    "מי ימחה את הכתמים שלי - גלי לוין (1).pdf": "psychodynamic",
    "תכנים ערכים ותהליכים.pdf": "shared",
}

# Large files that need bigger chunks to preserve article coherence
LARGE_FILE_CHUNK_SIZE = 800
DEFAULT_CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

LARGE_FILES = {"חוברת מאמרים - זכרונות ילדות.pdf"}

# Track options for UI
TRACKS = {
    "psychodynamic": "פסיכודינמי-יחסי",
    "narrative": "נרטיבי-חווייתי",
    "strengths": "מבוסס חוזקות",
    "integrative": "אינטגרטיבי חופשי",
}

# Phase labels
PHASES = {
    "phase_a": "שלב א׳ — הרחבת הזיכרון",
    "phase_b": "שלב ב׳ — ההעברה הנגדית שלך",
    "phase_c": "שלב ג׳ — השדה הבין-סובייקטיבי",
}
