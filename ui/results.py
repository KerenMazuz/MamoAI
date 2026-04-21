"""Tabbed results display and PDF export."""
import json
import io
from datetime import datetime
from typing import Optional

import streamlit as st


def render_results(all_analyses: dict, patient_id: str, session_number: int):
    """Render all results in tabs, supporting one or multiple tracks."""
    st.markdown("---")
    st.markdown(f"### 📄 תוצאות — פגישה {session_number} עם {patient_id}")

    for track, data in all_analyses.items():
        plan = data.get("plan", {})
        interpretation = data.get("interpretation", {})

        if len(all_analyses) > 1:
            st.markdown(f"#### 🔹 מסלול: {track}")

        tab_hyp, tab_q, tab_int, tab_sum, tab_anc = st.tabs([
            "השערות תיאורטיות",
            "שאלות לפגישה הבאה",
            "התערבויות",
            "סיכום",
            "עוגנים ודפוסים",
        ])

        with tab_hyp:
            _render_hypotheses(interpretation)

        with tab_q:
            _render_question_bank(plan.get("question_bank", []))

        with tab_int:
            _render_interventions(plan.get("interventions", []), plan.get("homework", {}))

        with tab_sum:
            _render_summary(plan.get("session_summary", ""), plan.get("transference_reflection", ""))

        with tab_anc:
            _render_anchors_patterns(plan.get("anchors", []), plan.get("patterns", {}))

        st.divider()
        _render_export_button(plan, interpretation, patient_id, session_number)


def _render_hypotheses(interpretation: dict):
    hypotheses = interpretation.get("hypotheses", [])
    if not hypotheses:
        st.info("אין השערות.")
        return

    for h in hypotheses:
        lens = h.get("lens", "")
        title = h.get("title", "")
        reading = h.get("reading", "")
        key_q = h.get("key_question", "")

        st.markdown(
            f'<div class="hypothesis-card">'
            f'<div class="hypothesis-title">🌱 {lens}: {title}</div>'
            f'<div>{reading}</div>'
            + (f'<div style="margin-top:8px;font-style:italic;color:#555;">❓ {key_q}</div>' if key_q else "")
            + "</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    symbolization = interpretation.get("symbolization", "")
    if symbolization:
        st.markdown(f"**🔮 סמל ומטפורה:** {symbolization}")

    alt_story = interpretation.get("alternative_story", "")
    if alt_story:
        st.markdown(f"**🔄 סיפור חלופי:** {alt_story}")

    lunar = interpretation.get("lunar_eclipse", {})
    if lunar:
        st.markdown("---")
        st.markdown("**🌑 ליקוי ירח — הפרדת הרגשות:**")
        st.markdown(f"- רגשות הילד/ה (אז): {lunar.get('child_feelings', '')}")
        st.markdown(f"- רגשות המבוגר/ת (עכשיו): {lunar.get('adult_feelings', '')}")
        if lunar.get("differentiation_question"):
            st.markdown(f'> *{lunar["differentiation_question"]}*')


def _render_question_bank(questions: list):
    if not questions:
        st.info("אין שאלות.")
        return

    st.markdown(f"**{len(questions)} שאלות לפגישה הבאה:**")
    for i, q in enumerate(questions, 1):
        approach = q.get("approach_tag", "")
        difficulty = q.get("difficulty", "")
        focus = q.get("focus", "")
        question_text = q.get("question", "")

        tags_html = ""
        if approach:
            tags_html += f'<span class="question-tag">{approach}</span>'
        if difficulty:
            tags_html += f'<span class="question-tag">{difficulty}</span>'
        if focus:
            tags_html += f'<span class="question-tag">{focus}</span>'

        st.markdown(
            f'<div class="question-card">'
            f'<div style="margin-bottom:6px;">{i}. {question_text}</div>'
            f'<div>{tags_html}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )


def _render_interventions(interventions: list, homework: dict):
    if interventions:
        st.markdown("**התערבויות מוצעות (2-3 דקות כל אחת):**")
        for iv in interventions:
            name = iv.get("name", "")
            duration = iv.get("duration", "2-3 דקות")
            goal = iv.get("goal", "")
            steps = iv.get("steps", [])

            steps_html = "".join(f"<li>{s}</li>" for s in steps)
            st.markdown(
                f'<div class="intervention-card">'
                f'<div style="font-weight:600;font-size:15px;">✨ {name} <span style="font-size:12px;color:#666;">({duration})</span></div>'
                f'<div style="color:#444;margin:6px 0;">{goal}</div>'
                f"<ol style='margin:0;padding-right:20px;'>{steps_html}</ol>"
                f"</div>",
                unsafe_allow_html=True,
            )

    if homework:
        task = homework.get("task", "") if isinstance(homework, dict) else str(homework)
        rationale = homework.get("rationale", "") if isinstance(homework, dict) else ""
        options = homework.get("options", []) if isinstance(homework, dict) else []

        st.markdown("---")
        st.markdown("**📝 מטלה בין-פגישתית:**")
        st.markdown(f"> {task}")
        if rationale:
            st.markdown(f"*{rationale}*")
        if options:
            st.markdown("אפשרויות נוספות:")
            for opt in options:
                st.markdown(f"- {opt}")


def _render_summary(summary: str, transference_reflection: str):
    if summary:
        st.markdown("**📋 סיכום הפגישה:**")
        st.markdown(
            f'<div style="background:#F8F8F8;padding:14px;border-radius:8px;direction:rtl;">{summary}</div>',
            unsafe_allow_html=True,
        )

    if transference_reflection:
        st.markdown("---")
        st.markdown("**🔍 רפלקציה על ההעברה (להמשך עיבוד עצמי):**")
        st.markdown(
            f'<div style="background:#F5F0FF;padding:14px;border-radius:8px;direction:rtl;font-style:italic;">'
            f"{transference_reflection}</div>",
            unsafe_allow_html=True,
        )


def _render_anchors_patterns(anchors: list, patterns: dict):
    if anchors:
        st.markdown("**⚓ עוגנים חיוביים שזוהו:**")
        pills = "".join(
            f'<span class="anchor-pill">{"💪" if a.get("strength") == "strong" else "🌱"} {a.get("description", "")}</span>'
            for a in anchors
        )
        st.markdown(f'<div style="direction:rtl;">{pills}</div>', unsafe_allow_html=True)
        st.markdown("")

    new_patterns = patterns.get("new", []) if isinstance(patterns, dict) else []
    accumulated = patterns.get("accumulated", []) if isinstance(patterns, dict) else []

    if new_patterns:
        st.markdown("**🆕 דפוסים חדשים שזוהו בפגישה זו:**")
        for p in new_patterns:
            cat = p.get("category", "")
            desc = p.get("description", "")
            st.markdown(f"- **[{cat}]** {desc}")

    if accumulated:
        st.markdown("**🔄 דפוסים מצטברים:**")
        for p in accumulated:
            occ = p.get("occurrences", 1)
            desc = p.get("description", "")
            cat = p.get("category", "")
            st.markdown(f"- **[{cat}]** {desc} *(הופיע {occ} פעמים)*")


def _render_export_button(plan: dict, interpretation: dict, patient_id: str, session_number: int):
    col1, col2 = st.columns([1, 4])
    with col1:
        pdf_bytes = _generate_pdf(plan, interpretation, patient_id, session_number)
        st.download_button(
            label="📥 הורד PDF",
            data=pdf_bytes,
            file_name=f"session_{patient_id}_{session_number}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _generate_pdf(plan: dict, interpretation: dict, patient_id: str, session_number: int) -> bytes:
    """Generate a PDF of the session output (excludes raw countertransference)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        rtl_style = ParagraphStyle(
            "RTL",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
            fontSize=11,
            leading=16,
        )
        title_style = ParagraphStyle(
            "RTLTitle",
            parent=styles["Heading1"],
            alignment=TA_RIGHT,
            fontSize=14,
        )
        section_style = ParagraphStyle(
            "RTLSection",
            parent=styles["Heading2"],
            alignment=TA_RIGHT,
            fontSize=12,
        )

        story = []
        date_str = datetime.now().strftime("%d/%m/%Y")

        story.append(Paragraph(f"דוח פגישה — {patient_id} | מפגש {session_number} | {date_str}", title_style))
        story.append(Spacer(1, 0.4 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color="grey"))
        story.append(Spacer(1, 0.3 * cm))

        def add_section(heading: str, content: str):
            if content:
                story.append(Paragraph(heading, section_style))
                story.append(Paragraph(content.replace("\n", "<br/>"), rtl_style))
                story.append(Spacer(1, 0.3 * cm))

        # Summary
        add_section("סיכום הפגישה", plan.get("session_summary", ""))

        # Hypotheses
        hypotheses = interpretation.get("hypotheses", [])
        if hypotheses:
            story.append(Paragraph("השערות תיאורטיות", section_style))
            for h in hypotheses:
                text = f"<b>{h.get('lens', '')}: {h.get('title', '')}</b><br/>{h.get('reading', '')}"
                story.append(Paragraph(text, rtl_style))
                story.append(Spacer(1, 0.2 * cm))

        # Question bank
        questions = plan.get("question_bank", [])
        if questions:
            story.append(Paragraph("שאלות לפגישה הבאה", section_style))
            for i, q in enumerate(questions, 1):
                story.append(Paragraph(f"{i}. {q.get('question', '')}", rtl_style))
            story.append(Spacer(1, 0.2 * cm))

        # Interventions
        interventions = plan.get("interventions", [])
        if interventions:
            story.append(Paragraph("התערבויות מוצעות", section_style))
            for iv in interventions:
                steps_text = " | ".join(iv.get("steps", []))
                text = f"<b>{iv.get('name', '')}</b> ({iv.get('duration', '')})<br/>{iv.get('goal', '')}<br/>{steps_text}"
                story.append(Paragraph(text, rtl_style))
                story.append(Spacer(1, 0.2 * cm))

        # Homework
        hw = plan.get("homework", {})
        if isinstance(hw, dict) and hw.get("task"):
            add_section("מטלה בין-פגישתית", hw.get("task", ""))

        # Anchors
        anchors = plan.get("anchors", [])
        if anchors:
            anchor_text = " | ".join(a.get("description", "") for a in anchors)
            add_section("עוגנים חיוביים שזוהו", anchor_text)

        doc.build(story)
        return buffer.getvalue()

    except Exception as e:
        # Fallback: plain text PDF alternative
        return _plain_text_export(plan, interpretation, patient_id, session_number).encode("utf-8")


def _plain_text_export(plan: dict, interpretation: dict, patient_id: str, session_number: int) -> str:
    """Plain text fallback if reportlab fails."""
    lines = [
        f"דוח פגישה — {patient_id} | מפגש {session_number}",
        "=" * 50,
        "",
        "סיכום:",
        plan.get("session_summary", ""),
        "",
        "שאלות לפגישה הבאה:",
    ]
    for i, q in enumerate(plan.get("question_bank", []), 1):
        lines.append(f"{i}. {q.get('question', '')}")
    return "\n".join(lines)


def render_session_history_view(session):
    """Render a past session in read-only view."""
    st.markdown(f"### 📖 פגישה {session.session_number} — {str(session.created_at)[:10]}")

    if session.summary:
        st.markdown("**סיכום:**")
        st.markdown(session.summary)

    if session.question_bank:
        try:
            questions = json.loads(session.question_bank)
            st.markdown("**שאלות שנשאלו:**")
            for q in questions:
                st.markdown(f"- {q.get('question', '')}")
        except Exception:
            pass

    if session.homework:
        st.markdown(f"**מטלה:** {session.homework}")

    if st.button("← חזרה", key="back_from_history"):
        st.session_state["phase"] = "upload"
        st.session_state.pop("view_session_id", None)
        st.rerun()
