# MamoAI — Therapist Support Bot

An AI-powered clinical support tool for therapists. MamoAI helps therapists process therapy sessions by guiding them through a structured memory-exploration conversation and then automatically generating theoretical interpretations, intervention suggestions, and a full session plan — all grounded in real clinical literature.

Built with Streamlit and GPT-4o, with RAG retrieval over a curated library of Hebrew-language therapeutic texts.

---

## What it does

The therapist uploads or pastes a session transcript. The system then runs a **4-agent pipeline**:

1. **File Manager** — Loads the patient's full history from the local database and builds a structured context card.
2. **Memory Deepener** — Conducts an interactive, multi-phase dialogue with the therapist to surface emotional memory, countertransference signals, and key relational moments from the session.
3. **Lens Interpreter** — Uses the enriched session package + RAG-retrieved clinical chunks to generate 1–2 theoretical hypotheses about the patient, framed through the selected therapeutic track.
4. **Session Planner** — Produces all therapist-facing deliverables: session summary, questions for the next session, intervention scripts, between-session homework, identified anchors, and recurring patterns.

The therapist can run multiple therapeutic tracks on the same session (e.g. psychodynamic + narrative) and compare results side by side.

---

## Therapeutic Tracks

| Track | Description |
|---|---|
| `psychodynamic` | Psychodynamic-relational lens |
| `narrative` | Narrative-experiential lens |
| `strengths` | Strengths-based lens |
| `integrative` | Free integrative lens |

---

## Agent Architecture

```
Patient History (DB)
        │
        ▼
  [Agent 1] FileManager          ← no LLM, pure data retrieval
        │
        ▼
  [Agent 2] MemoryDeepener       ← interactive UI conversation (3 phases)
        │  Phase A: memory expansion
        │  Phase B: countertransference
        │  Phase C: intersubjective field
        │
        ▼
    RAG Retrieval                ← ChromaDB over clinical PDFs
        │
        ▼
  [Agent 3] LensInterpreter      ← theoretical hypotheses
        │
        ▼
  [Agent 4] SessionPlanner       ← full session deliverables
        │
        ▼
    Results UI + PDF Export
```

Agent 2 runs interactively inside the Streamlit UI. Agents 3 and 4 run automatically back-to-back once all three phases are complete.

---

## Tech Stack

- **Frontend**: Streamlit (RTL Hebrew UI)
- **LLM**: OpenAI GPT-4o
- **Vector store**: ChromaDB (per-track collections)
- **Database**: SQLite via SQLAlchemy
- **PDF export**: ReportLab
- **PDF ingestion**: PyMuPDF + pdfplumber

---

## Project Structure

```
MamoAI/
├── app.py                  # Streamlit entry point & session state machine
├── config.py               # API keys, model name, track/phase definitions
├── requirements.txt
│
├── agents/
│   ├── crew.py                     # Pipeline orchestration (Agents 3 & 4)
│   ├── agent_file_manager.py       # Agent 1: patient context loader
│   ├── agent_memory_deepener.py    # Agent 2: interactive memory exploration
│   ├── agent_lens_interpreter.py   # Agent 3: theoretical interpretation
│   └── agent_session_planner.py    # Agent 4: session plan generator
│
├── prompts/
│   ├── agent2_system.txt
│   ├── agent3_system.txt
│   └── agent4_system.txt
│
├── rag/
│   ├── ingest.py           # PDF → chunks → ChromaDB
│   └── retriever.py        # Semantic retrieval per track
│
├── RAG data/               # Clinical PDFs (Hebrew therapeutic literature)
│
├── database/
│   ├── db.py
│   └── models.py           # Patient, Session, Anchor, Pattern models
│
└── ui/
    ├── phases.py           # Phase A/B/C conversation UI
    ├── results.py          # Tabbed results display + PDF export
    ├── sidebar.py          # Patient selector
    └── styles.py           # RTL CSS
```

---

## Setup

**1. Clone and install dependencies**

```bash
git clone https://github.com/KerenMazuz/MamoAI.git
cd MamoAI
pip install -r requirements.txt
```

**2. Set your OpenAI API key**

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

**3. Ingest the clinical literature into ChromaDB**

```bash
python -m rag.ingest
```

**4. Run the app**

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

---

## Notes

- The database and ChromaDB store are local and excluded from version control (see `.gitignore`).
- All prompts are in Hebrew; the UI is right-to-left.
- PDF export requires `reportlab`. If it is not available, the export falls back to plain text.
