# סוכן תכנון פיננסי

כלי עצמאי (לא תלוי ב-MamoAI/Memo) להעלאת נתונים פיננסיים (אקסל/CSV, כולל דוחות עסקאות כרטיס אשראי) וקבלת תכנון תקציב מסודר + דוח תובנות והמלצות בעברית, עם מיקוד בהגדלת הזרימה לקרן חיסכון שמשמשת כ"הלוואה עתידית לעצמי".

## הרצה

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
streamlit run app.py
```

## מבנה

```
financial-planning-agent/
├── app.py                          # Streamlit UI
├── config.py                       # API key + model config
├── agents/
│   ├── agent_financial_organizer.py  # Agent 1: מסדר נתונים
│   ├── agent_financial_advisor.py    # Agent 2: יועץ/תובנות
│   └── financial_crew.py             # אורקסטרציה
├── excel/
│   └── excel_builder.py            # בניית קובץ אקסל פלט
└── prompts/
    ├── financial_organizer_system.txt
    └── financial_advisor_system.txt
```
