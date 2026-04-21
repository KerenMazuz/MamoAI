"""Phase A/B/C conversation UI components."""
import streamlit as st
from config import PHASES


def render_phase_header(phase: str, mandatory: bool = True):
    label = PHASES.get(phase, phase)
    css_class = {"phase_a": "phase-a", "phase_b": "phase-b", "phase_c": "phase-c"}.get(phase, "phase-a")
    optional_badge = "" if mandatory else " <span style='font-size:12px;font-weight:400;'>(אופציונלי)</span>"
    st.markdown(
        f'<div class="phase-header {css_class}">{label}{optional_badge}</div>',
        unsafe_allow_html=True,
    )


def render_conversation(phase_key: str, qa_list: list):
    """Display previous Q&A exchanges for a phase."""
    for i, (q, a) in enumerate(qa_list):
        with st.container():
            st.markdown(f"**🌱 {q}**")
            st.markdown(
                f'<div style="background:#F5F5F5;padding:10px 14px;border-radius:6px;'
                f'direction:rtl;margin-bottom:8px;">{a}</div>',
                unsafe_allow_html=True,
            )


def render_question_input(question: str, phase_key: str, question_index: int) -> tuple[str, bool, bool]:
    """
    Show the current question and a text area for the therapist's answer.
    Returns (answer_text, submitted, skipped).
    """
    st.markdown(f"**🌸 {question}**")
    answer = st.text_area(
        "תשובתך:",
        height=120,
        key=f"answer_{phase_key}_{question_index}",
        placeholder="כתוב/י כאן את תשובתך...",
    )
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        submitted = st.button("המשך ←", key=f"submit_{phase_key}_{question_index}", type="primary")
    with col2:
        skipped = st.button("דלג →", key=f"skip_{phase_key}_{question_index}")
    return answer.strip(), submitted, skipped


def render_phase_skip_button(label: str = "דלג לניתוח ←") -> bool:
    """Optional skip button (Phase C only)."""
    return st.button(label, key="skip_phase_c")


def render_progress_bar(current_phase: str):
    phases_order = ["phase_a", "phase_b", "phase_c", "processing", "results"]
    phase_labels = ["הרחבה", "העברה נגדית", "שדה בין-סובייקטיבי", "עיבוד", "תוצאות"]
    idx = phases_order.index(current_phase) if current_phase in phases_order else 0
    progress = (idx + 1) / len(phases_order)

    cols = st.columns(len(phases_order))
    for i, (col, label) in enumerate(zip(cols, phase_labels)):
        with col:
            if i < idx:
                st.markdown(f"<div style='text-align:center;color:#1B7A63;font-size:12px;'>✓ {label}</div>", unsafe_allow_html=True)
            elif i == idx:
                st.markdown(f"<div style='text-align:center;color:#3C3489;font-weight:700;font-size:12px;'>● {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;color:#AAA;font-size:12px;'>○ {label}</div>", unsafe_allow_html=True)
    st.progress(progress)
