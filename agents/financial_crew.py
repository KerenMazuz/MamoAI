"""
Financial planning pipeline orchestration.

  Agent 1 (FinancialOrganizer) -> Agent 2 (FinancialAdvisor)
"""
from agents.agent_financial_organizer import FinancialOrganizer
from agents.agent_financial_advisor import FinancialAdvisor


def organize_only(raw_table: str, manual_additions: dict | None = None) -> dict:
    """Run Agent 1 alone — used to detect missing_fields before running Agent 2."""
    organizer = FinancialOrganizer()
    return organizer.organize(raw_table=raw_table, manual_additions=manual_additions)


def advise_only(organized: dict) -> dict:
    """Run Agent 2 alone on an already-organized dataset."""
    advisor = FinancialAdvisor()
    return advisor.advise(organized_data=organized)


def run_financial_pipeline(raw_table: str, manual_additions: dict | None = None) -> dict:
    """
    Run Agent 1 -> Agent 2 sequentially.

    Args:
        raw_table: uploaded financial data, rendered as text
        manual_additions: optional dict of user-filled values for missing categories

    Returns:
        {
            "organized": dict,    # Agent 1 output
            "advice": dict,       # Agent 2 output
        }
    """
    organizer = FinancialOrganizer()
    organized = organizer.organize(raw_table=raw_table, manual_additions=manual_additions)

    advisor = FinancialAdvisor()
    advice = advisor.advise(organized_data=organized)

    return {
        "organized": organized,
        "advice": advice,
    }
