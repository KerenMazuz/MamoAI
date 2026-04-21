"""
Pipeline orchestration.

Architecture:
  - Agent 2 (MemoryDeepener) runs OUTSIDE this file, driven by Streamlit UI.
  - This module runs Agents 3 & 4 after all phases are complete.
  - Agent 1 load/save is called directly from app.py.
"""
from typing import List

from agents.agent_lens_interpreter import LensInterpreter
from agents.agent_session_planner import SessionPlanner
from rag.retriever import retrieve


def run_analysis_pipeline(
    enriched_package: dict,
    track: str,
    patient_history: dict,
    qa_data: dict = None,
) -> dict:
    """
    Run Agent 3 → Agent 4 sequentially.

    Args:
        enriched_package: MemoryDeepener.get_structured_output()
        track: selected therapeutic track
        patient_history: load_patient_context() output

    Returns:
        {
            "interpretation": dict,   # Agent 3 output
            "plan": dict,             # Agent 4 output
        }
    """
    enriched_memory = enriched_package.get("enriched_memory", "")
    countertransference = enriched_package.get("countertransference", {})

    # Build a combined query for RAG retrieval
    ct_text = ""
    if isinstance(countertransference, dict):
        ct_text = " ".join(str(v) for v in countertransference.values())
    rag_query = f"{enriched_memory[:300]} {ct_text[:200]}"

    # Retrieve relevant chunks from ChromaDB
    rag_chunks: List[str] = retrieve(query=rag_query, track=track, n_results=5)

    # Agent 3: interpret
    interpreter = LensInterpreter()
    interpretation = interpreter.interpret(
        enriched_package=enriched_package,
        track=track,
        rag_chunks=rag_chunks,
    )

    # Agent 4: plan
    planner = SessionPlanner()
    plan = planner.plan(
        interpretation=interpretation,
        enriched_package=enriched_package,
        patient_history=patient_history,
        track=track,
        qa_data=qa_data,
        rag_chunks=rag_chunks,
    )

    return {
        "interpretation": interpretation,
        "plan": plan,
    }
