RTL_CSS = """
<style>
    /* Global RTL */
    .stApp { direction: rtl; }
    .stMarkdown, .stText { direction: rtl; text-align: right; }
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 15px; }
    .stTextInput input { direction: rtl; text-align: right; }
    .stSelectbox label, .stRadio label { direction: rtl; }
    .stAlert { direction: rtl; text-align: right; }
    div[data-testid="stSidebar"] { direction: rtl; }
    div[data-testid="stSidebar"] .stRadio label { text-align: right; }

    /* Phase headers */
    .phase-header {
        padding: 12px 16px;
        border-radius: 8px;
        margin: 16px 0 8px 0;
        font-weight: 600;
        font-size: 16px;
        direction: rtl;
    }
    .phase-a { background: #E1F5EE; color: #085041; border-right: 4px solid #1B7A63; }
    .phase-b { background: #EEEDFE; color: #3C3489; border-right: 4px solid #6B63D0; }
    .phase-c { background: #FAEEDA; color: #633806; border-right: 4px solid #C87520; }

    /* Hypothesis cards */
    .hypothesis-card {
        background: #F8F9FA;
        border: 1px solid #DEE2E6;
        border-right: 4px solid #4A90D9;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        direction: rtl;
    }
    .hypothesis-title {
        font-weight: 600;
        color: #1A3A5C;
        font-size: 15px;
        margin-bottom: 8px;
    }

    /* Question cards */
    .question-card {
        background: #FAFBFF;
        border: 1px solid #C8D8F0;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        direction: rtl;
    }
    .question-tag {
        font-size: 11px;
        color: #666;
        background: #E8EEF8;
        padding: 2px 8px;
        border-radius: 12px;
        margin-right: 6px;
    }

    /* Intervention card */
    .intervention-card {
        background: #F0F9F4;
        border: 1px solid #B8DCC8;
        border-radius: 8px;
        padding: 14px;
        margin: 10px 0;
        direction: rtl;
    }

    /* Context card */
    .context-card {
        background: #FFF8E7;
        border: 1px solid #F0D080;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        direction: rtl;
    }

    /* Patient ID badge */
    .patient-id-badge {
        font-size: 22px;
        font-weight: 700;
        color: #1A3A5C;
        background: #E8F0FB;
        padding: 8px 20px;
        border-radius: 8px;
        display: inline-block;
        letter-spacing: 2px;
    }

    /* Anchor pill */
    .anchor-pill {
        display: inline-block;
        background: #E7F7EE;
        color: #1B6B3A;
        border: 1px solid #A8D8BB;
        border-radius: 16px;
        padding: 3px 12px;
        margin: 3px;
        font-size: 13px;
    }

    /* Tab content */
    .stTabs [data-baseweb="tab"] { direction: rtl; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
"""
