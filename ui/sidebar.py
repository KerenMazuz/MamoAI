"""Sidebar: patient selector, new patient form, track picker, session history."""
import streamlit as st
from database import db
from database.models import Patient
from config import TRACKS


def render_sidebar() -> dict:
    """
    Render the sidebar and return the current selection:
    {
        "patient_id": str | None,
        "track": str,
        "action": "new_session" | "view_history" | None,
        "history_session_id": int | None,
    }
    """
    result = {
        "patient_id": st.session_state.get("patient_id"),
        "track": st.session_state.get("track", "psychodynamic"),
        "action": None,
        "history_session_id": None,
    }

    with st.sidebar:
        st.markdown("## 🧠 כלי תמיכה למטפל/ת")
        st.divider()

        # ── Patient selector ──────────────────────────────────────────
        patients = db.list_patients()

        if patients:
            options = ["— בחר/י מטופל/ת —"] + [
                _patient_label(p) for p in patients
            ]
            patient_ids = [None] + [p.id for p in patients]

            current_pid = st.session_state.get("patient_id")
            current_index = 0
            if current_pid in patient_ids:
                current_index = patient_ids.index(current_pid)

            selected_index = st.selectbox(
                "מטופל/ת",
                range(len(options)),
                format_func=lambda i: options[i],
                index=current_index,
                key="sidebar_patient_select",
            )
            selected_pid = patient_ids[selected_index]
            if selected_pid != st.session_state.get("patient_id"):
                st.session_state["patient_id"] = selected_pid
                st.session_state["phase"] = "upload"
                st.rerun()
            result["patient_id"] = selected_pid
        else:
            st.info("אין מטופלים עדיין. צור/י מטופל/ת חדש/ה.")

        st.divider()

        # ── New patient button ────────────────────────────────────────
        if st.button("＋ מטופל/ת חדש/ה", use_container_width=True, key="btn_new_patient"):
            st.session_state["show_new_patient_form"] = True

        if st.session_state.get("show_new_patient_form"):
            _render_new_patient_form()

        st.divider()

        # ── Track selector ────────────────────────────────────────────
        track_keys = list(TRACKS.keys())
        track_labels = list(TRACKS.values())

        current_track = st.session_state.get("track", "psychodynamic")
        current_track_index = track_keys.index(current_track) if current_track in track_keys else 0

        selected_track_label = st.radio(
            "מסלול טיפולי",
            track_labels,
            index=current_track_index,
            key="sidebar_track_radio",
        )
        selected_track = track_keys[track_labels.index(selected_track_label)]
        if selected_track != st.session_state.get("track"):
            st.session_state["track"] = selected_track
        result["track"] = selected_track

        st.divider()

        # ── Session history ───────────────────────────────────────────
        pid = result["patient_id"]
        if pid:
            sessions = db.get_sessions(pid)
            if sessions:
                st.markdown("**היסטוריית פגישות**")
                for s in reversed(sessions):
                    date = str(s.created_at)[:10] if s.created_at else ""
                    label = f"פגישה {s.session_number}  {date}"
                    if st.button(label, key=f"hist_{s.id}", use_container_width=True):
                        st.session_state["view_session_id"] = s.id
                        st.session_state["phase"] = "view_history"
                        result["action"] = "view_history"
                        result["history_session_id"] = s.id
                        st.rerun()

    return result


def _patient_label(p: Patient) -> str:
    alias = f" · {p.alias}" if p.alias else ""
    return f"{p.id}{alias} · גיל {p.age} · {TRACKS.get(p.track, p.track)} · {p.session_count} פגישות"


def _render_new_patient_form():
    with st.sidebar.expander("פרטי מטופל/ת חדש/ה", expanded=True):
        age = st.number_input("גיל", min_value=5, max_value=100, value=30, key="new_patient_age")
        track_labels = list(TRACKS.values())
        track_keys = list(TRACKS.keys())
        track_label = st.selectbox("מסלול", track_labels, key="new_patient_track")
        track = track_keys[track_labels.index(track_label)]
        alias = st.text_input(
            "כינוי (לא מזהה) — אופציונלי",
            placeholder='למשל: "הנגן", "הילדה עם הכובע"',
            key="new_patient_alias",
        )

        st.warning("⚠️ ודא/י שהכינוי אינו מאפשר זיהוי המטופל/ת")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("צור/י", key="btn_create_patient"):
                patient = db.create_patient(
                    age=int(age),
                    track=track,
                    alias=alias.strip() if alias.strip() else None,
                )
                st.session_state["patient_id"] = patient.id
                st.session_state["track"] = track
                st.session_state["phase"] = "upload"
                st.session_state["show_new_patient_form"] = False
                st.session_state["new_patient_id"] = patient.id
                st.rerun()
        with col2:
            if st.button("ביטול", key="btn_cancel_new"):
                st.session_state["show_new_patient_form"] = False
                st.rerun()
