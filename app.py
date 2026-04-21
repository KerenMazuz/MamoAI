"""
Therapist Support Bot — main Streamlit application.

State machine:
  select_patient → upload → phase_a → phase_b → phase_c → processing → results
"""
import streamlit as st
from database import db
from ui.styles import RTL_CSS
from ui.sidebar import render_sidebar
from ui.phases import (
    render_phase_header,
    render_conversation,
    render_question_input,
    render_phase_skip_button,
    render_progress_bar,
)
from ui.results import render_results, render_session_history_view
from agents.agent_memory_deepener import MemoryDeepener
from agents.agent_file_manager import load_patient_context, save_session_results
from agents.crew import run_analysis_pipeline
from config import TRACKS

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="כלי תמיכה למטפל/ת",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(RTL_CSS, unsafe_allow_html=True)

# ── DB init ───────────────────────────────────────────────────────────────────
db.init_db()

# ── Session state defaults ────────────────────────────────────────────────────
defaults = {
    "phase": "upload",
    "patient_id": None,
    "track": "psychodynamic",
    "uploaded_text": None,
    "memory_deepener": None,
    "current_question": None,
    "question_index": 0,
    "phase_a_qa": [],
    "phase_b_qa": [],
    "phase_c_qa": [],
    "enriched_package": None,
    "all_analyses": {},        # {track: {"interpretation": ..., "plan": ...}}
    "patient_history": None,
    "show_new_patient_form": False,
    "new_patient_id": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
sidebar = render_sidebar()
patient_id = sidebar["patient_id"]
track = sidebar["track"]

# Show new patient ID banner
if st.session_state.get("new_patient_id"):
    new_id = st.session_state.pop("new_patient_id")
    st.success("✅ מטופל/ת חדש/ה נוצר/ה בהצלחה!")
    st.markdown(
        f'<div style="text-align:center;padding:16px;">'
        f'המזהה של המטופל/ת החדש/ה:<br/>'
        f'<span class="patient-id-badge">{new_id}</span><br/><br/>'
        f'<span style="color:#C00;">🔒 רשום/י אותו בקובץ המקומי שלך. המערכת לא שומרת שמות.</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

# ── History view ──────────────────────────────────────────────────────────────
if st.session_state.get("phase") == "view_history":
    session_id = st.session_state.get("view_session_id")
    if session_id and patient_id:
        sessions = db.get_sessions(patient_id)
        target = next((s for s in sessions if s.id == session_id), None)
        if target:
            render_session_history_view(target)
    st.stop()

# ── Guard: patient required ───────────────────────────────────────────────────
if not patient_id:
    st.markdown("## ברוך/ה הבא/ה 👋")
    st.markdown("בחר/י מטופל/ת מהתפריט הצדדי, או צור/י מטופל/ת חדש/ה כדי להתחיל.")
    st.stop()

# ── Load patient context ──────────────────────────────────────────────────────
if (
    st.session_state.get("patient_history") is None
    or st.session_state.get("_loaded_for") != patient_id
):
    st.session_state["patient_history"] = load_patient_context(patient_id)
    st.session_state["_loaded_for"] = patient_id

patient_history = st.session_state["patient_history"]
session_number = patient_history.get("session_count", 0) + 1

# ── Progress bar ──────────────────────────────────────────────────────────────
render_progress_bar(st.session_state["phase"])

# ── Context card (returning patient) ─────────────────────────────────────────
context_card = patient_history.get("context_card", "")
if context_card and st.session_state["phase"] == "upload":
    st.markdown(
        f'<div class="context-card">{context_card}</div>',
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE: UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["phase"] == "upload":
    st.markdown(f"## פגישה {session_number} — {patient_id}")

    st.warning(
        "⚠️ **שים/י לב לפרטיות:** וודא/י שהקובץ אינו מכיל שם מלא, מספר ת.ז., כתובת "
        "או פרטים מזהים אחרים של המטופל/ת."
    )

    uploaded_file = st.file_uploader(
        "העלה/י קובץ טקסט של הזיכרון",
        type=["txt", "md"],
        key="file_uploader",
    )
    text_input = st.text_area(
        "או הדבק/י את הטקסט כאן:",
        height=200,
        key="direct_text_input",
        placeholder="תאר/י את הזיכרון שעלה בפגישה...",
    )

    if uploaded_file:
        text_content = uploaded_file.read().decode("utf-8", errors="replace")
        st.session_state["uploaded_text"] = text_content
        st.success(f"✅ הקובץ הועלה ({len(text_content)} תווים)")
    elif text_input.strip():
        st.session_state["uploaded_text"] = text_input.strip()

    if st.session_state.get("uploaded_text"):
        with st.expander("תצוגה מקדימה", expanded=False):
            st.text(st.session_state["uploaded_text"][:500] + ("..." if len(st.session_state["uploaded_text"]) > 500 else ""))

        if st.button("התחל עיבוד ←", type="primary", key="btn_start"):
            md = MemoryDeepener()
            first_q = md.start_phase_a(
                original_text=st.session_state["uploaded_text"],
                context_card=context_card,
                patient_history=str(patient_history.get("patterns", [])),
            )
            st.session_state["memory_deepener"] = md
            st.session_state["current_question"] = first_q
            st.session_state["question_index"] = 0
            st.session_state["phase_a_qa"] = []
            st.session_state["phase_b_qa"] = []
            st.session_state["phase_c_qa"] = []
            st.session_state["all_analyses"] = {}
            st.session_state["phase"] = "phase_a"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE A — MEMORY EXPANSION
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == "phase_a":
    render_phase_header("phase_a", mandatory=True)

    md: MemoryDeepener = st.session_state["memory_deepener"]
    render_conversation("phase_a", st.session_state["phase_a_qa"])

    answer, submitted, skipped = render_question_input(
        question=st.session_state["current_question"],
        phase_key="phase_a",
        question_index=st.session_state["question_index"],
    )

    if (submitted and answer) or skipped:
        if submitted and answer:
            st.session_state["phase_a_qa"].append((st.session_state["current_question"], answer))
            next_q = md.continue_phase_a(answer)
        else:
            # Skipped — move on without answer
            next_q = md.continue_phase_a("(דולג)")

        if next_q is None:
            first_b_q = md.start_phase_b()
            st.session_state["current_question"] = first_b_q
            st.session_state["question_index"] = 0
            st.session_state["phase"] = "phase_b"
        else:
            st.session_state["current_question"] = next_q
            st.session_state["question_index"] += 1
        st.rerun()

    # Allow jumping directly to analysis (skip rest of phase A)
    st.divider()
    if st.button("עבור לשלב העברה נגדית ←", key="skip_phase_a_entirely"):
        first_b_q = md.start_phase_b()
        st.session_state["current_question"] = first_b_q
        st.session_state["question_index"] = 0
        st.session_state["phase"] = "phase_b"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE B — COUNTERTRANSFERENCE (mandatory phase, individual questions skippable)
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == "phase_b":
    render_phase_header("phase_b", mandatory=True)
    st.caption("שלב חובה — יש להשלים לפחות שאלה אחת לפני המשך הניתוח")

    md: MemoryDeepener = st.session_state["memory_deepener"]
    render_conversation("phase_b", st.session_state["phase_b_qa"])

    answer, submitted, skipped = render_question_input(
        question=st.session_state["current_question"],
        phase_key="phase_b",
        question_index=st.session_state["question_index"],
    )

    if (submitted and answer) or skipped:
        if submitted and answer:
            st.session_state["phase_b_qa"].append((st.session_state["current_question"], answer))
            next_q = md.continue_phase_b(answer)
        else:
            next_q = md.continue_phase_b("(דולג)")

        if next_q is None:
            first_c_q = md.start_phase_c()
            st.session_state["current_question"] = first_c_q
            st.session_state["question_index"] = 0
            st.session_state["phase"] = "phase_c"
        else:
            st.session_state["current_question"] = next_q
            st.session_state["question_index"] += 1
        st.rerun()

    # Jump to phase C — allowed only if at least one B answer given
    if st.session_state["phase_b_qa"]:
        st.divider()
        if st.button("עבור לשלב הבא ←", key="skip_to_phase_c"):
            first_c_q = md.start_phase_c()
            st.session_state["current_question"] = first_c_q
            st.session_state["question_index"] = 0
            st.session_state["phase"] = "phase_c"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C — INTERSUBJECTIVE (fully optional)
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == "phase_c":
    render_phase_header("phase_c", mandatory=False)

    md: MemoryDeepener = st.session_state["memory_deepener"]
    render_conversation("phase_c", st.session_state["phase_c_qa"])

    answer, submitted, skipped = render_question_input(
        question=st.session_state["current_question"],
        phase_key="phase_c",
        question_index=st.session_state["question_index"],
    )

    col_skip, _ = st.columns([1, 3])
    with col_skip:
        skip_to_analysis = render_phase_skip_button("דלג לניתוח ←")

    if skip_to_analysis:
        st.session_state["phase"] = "processing"
        st.rerun()

    if (submitted and answer) or skipped:
        if submitted and answer:
            st.session_state["phase_c_qa"].append((st.session_state["current_question"], answer))
            next_q = md.continue_phase_c(answer)
            if next_q and not skipped:
                st.session_state["current_question"] = next_q
                st.session_state["question_index"] += 1
                st.rerun()
        st.session_state["phase"] = "processing"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == "processing":
    current_track = st.session_state.get("processing_track", track)
    st.markdown(f"### 🔄 מנתח לפי מסלול: **{TRACKS.get(current_track, current_track)}**...")

    with st.spinner("מעבד... זה עשוי לקחת כדקה"):
        md: MemoryDeepener = st.session_state["memory_deepener"]

        qa_data = {
            "phase_a_qa": st.session_state["phase_a_qa"],
            "phase_b_qa": st.session_state["phase_b_qa"],
            "phase_c_qa": st.session_state["phase_c_qa"],
        }

        # Get enriched package (once — reuse for additional tracks)
        if st.session_state.get("enriched_package") is None:
            enriched_package = md.get_structured_output(qa_data)
            st.session_state["enriched_package"] = enriched_package
        else:
            enriched_package = st.session_state["enriched_package"]

        results = run_analysis_pipeline(
            enriched_package=enriched_package,
            track=current_track,
            patient_history=patient_history,
            qa_data=qa_data,
        )

        # Accumulate analyses per track
        all_analyses = st.session_state.get("all_analyses", {})
        all_analyses[current_track] = {
            "interpretation": results["interpretation"],
            "plan": results["plan"],
        }
        st.session_state["all_analyses"] = all_analyses

        # Save to DB (only on first track)
        if len(all_analyses) == 1:
            save_session_results(
                patient_id=patient_id,
                session_number=session_number,
                original_text=st.session_state["uploaded_text"],
                enriched_package=enriched_package,
                interpretation=results["interpretation"],
                plan=results["plan"],
                track=current_track,
            )
            st.session_state["patient_history"] = None

        st.session_state.pop("processing_track", None)
        st.session_state["phase"] = "results"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == "results":
    all_analyses = st.session_state.get("all_analyses", {})

    render_results(
        all_analyses=all_analyses,
        patient_id=patient_id,
        session_number=session_number,
    )

    # ── Add another track ────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔄 נתח במסלול נוסף")

    available_tracks = {k: v for k, v in TRACKS.items() if k not in all_analyses}
    if available_tracks:
        col1, col2 = st.columns([2, 1])
        with col1:
            extra_track_label = st.selectbox(
                "בחר/י מסלול נוסף:",
                list(available_tracks.values()),
                key="extra_track_select",
            )
        with col2:
            extra_track_key = [k for k, v in available_tracks.items() if v == extra_track_label][0]
            if st.button("נתח ←", key="btn_extra_track", type="primary"):
                st.session_state["processing_track"] = extra_track_key
                st.session_state["phase"] = "processing"
                st.rerun()
    else:
        st.info("✅ נותחו כל המסלולים האפשריים עבור זיכרון זה.")

    st.divider()
    if st.button("← פגישה חדשה", key="btn_new_session"):
        for key in [
            "phase", "uploaded_text", "memory_deepener", "current_question",
            "question_index", "phase_a_qa", "phase_b_qa", "phase_c_qa",
            "enriched_package", "all_analyses", "patient_history",
        ]:
            st.session_state.pop(key, None)
        st.session_state["phase"] = "upload"
        st.rerun()
