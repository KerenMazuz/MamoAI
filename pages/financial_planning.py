"""
Financial Planning Agent — Streamlit page.

Flow:
  upload Excel/CSV → (optional) fill in missing categories →
  run organizer + advisor agents → show organized tables + insights report →
  download full Excel report.
"""
import pandas as pd
import streamlit as st

from agents.financial_crew import advise_only, organize_only
from financial.excel_builder import build_workbook
from ui.styles import RTL_CSS

st.set_page_config(
    page_title="תכנון פיננסי",
    page_icon="💰",
    layout="wide",
)
st.markdown(RTL_CSS, unsafe_allow_html=True)

st.title("💰 סוכן תכנון פיננסי")
st.markdown(
    "העלה/י קובץ אקסל/CSV עם הנתונים הפיננסיים שלך (הכנסות, הוצאות, חיסכון, "
    "ביטוחים, פנסיה וכו'). הסוכן יסדר את הנתונים לפי קטגוריות, ייצור מאזן "
    "מלא ויפיק דוח תובנות והמלצות."
)

defaults = {
    "fin_raw_table": None,
    "fin_organized_preview": None,
    "fin_result": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

MISSING_FIELD_LABELS = {
    "income": "הכנסות",
    "expenses": "הוצאות",
    "savings": "חיסכון",
    "emergency_fund": "קרן חירום",
    "pension_retirement": "פנסיה ופרישה",
    "insurance": "ביטוחים",
    "future_one_time": "הוצאות עתידיות חד-פעמיות",
    "free_capital": "הון חופשי",
}

uploaded_file = st.file_uploader("קובץ נתונים (Excel או CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"לא ניתן לקרוא את הקובץ: {e}")
        df = None

    if df is not None:
        st.subheader("תצוגה מקדימה של הנתונים שהועלו")
        st.dataframe(df, use_container_width=True)
        st.session_state["fin_raw_table"] = df.to_csv(index=False)

if st.session_state["fin_raw_table"] and st.session_state["fin_organized_preview"] is None:
    if st.button("🔍 הרץ ניתוח ראשוני", type="primary"):
        with st.spinner("מסדר את הנתונים..."):
            st.session_state["fin_organized_preview"] = organize_only(
                raw_table=st.session_state["fin_raw_table"],
            )

if st.session_state["fin_organized_preview"] and st.session_state["fin_result"] is None:
    missing = st.session_state["fin_organized_preview"].get("missing_fields", [])
    if missing:
        st.warning("חלק מהקטגוריות חסרות בקובץ שהועלה. אפשר להשלים אותן כאן (לא חובה):")
        with st.form("missing_fields_form"):
            additions = {}
            for field in missing:
                label = MISSING_FIELD_LABELS.get(field, field)
                additions[field] = st.text_area(f"{label} — תיאור/ערכים", key=f"manual_{field}")
            submitted = st.form_submit_button("המשך עם ההשלמות")
            skipped = st.form_submit_button("דלג והמשך בלי השלמות")

        if submitted or skipped:
            manual_additions = {k: v for k, v in additions.items() if v.strip()} if submitted else {}
            with st.spinner("מסדר ומנתח את הנתונים..."):
                organized = organize_only(
                    raw_table=st.session_state["fin_raw_table"],
                    manual_additions=manual_additions or None,
                ) if manual_additions else st.session_state["fin_organized_preview"]
                advice = advise_only(organized)
            st.session_state["fin_result"] = {"organized": organized, "advice": advice}
            st.rerun()
    else:
        with st.spinner("מנתח את הנתונים..."):
            organized = st.session_state["fin_organized_preview"]
            advice = advise_only(organized)
        st.session_state["fin_result"] = {"organized": organized, "advice": advice}
        st.rerun()

if st.session_state["fin_result"]:
    organized = st.session_state["fin_result"]["organized"]
    advice = st.session_state["fin_result"]["advice"]

    st.success("הניתוח הושלם!")

    summary = advice.get("balance_summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("הכנסה חודשית", summary.get("total_monthly_income"))
    c2.metric("הוצאות חודשיות", summary.get("total_monthly_expenses"))
    c3.metric("עודף/גירעון", summary.get("monthly_surplus_or_deficit"))
    c4.metric("אחוז חיסכון", f"{summary.get('savings_rate_percent')}%")

    st.markdown("## דוח תובנות והמלצות")
    st.markdown(advice.get("executive_summary_markdown", ""))

    with st.expander("📊 הנתונים המסודרים (JSON)"):
        st.json(organized)

    workbook_bytes = build_workbook(organized, advice)
    st.download_button(
        "⬇️ הורד דוח אקסל מלא",
        data=workbook_bytes,
        file_name="תכנון_פיננסי.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if st.button("🔄 התחל ניתוח חדש"):
        for k in defaults:
            st.session_state[k] = defaults[k]
        st.rerun()
