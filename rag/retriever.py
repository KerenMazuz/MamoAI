"""Query ChromaDB for relevant chunks given a track and a query string."""
from typing import List

import chromadb
from chromadb.config import Settings

from config import CHROMA_PATH


def _get_client() -> chromadb.Client:
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def retrieve(query: str, track: str, n_results: int = 5) -> List[str]:
    """
    Query the track-specific collection and the shared collection.
    Returns a deduplicated list of relevant text chunks.
    """
    client = _get_client()
    results = []

    for collection_name in [track, "shared"]:
        try:
            collection = client.get_collection(name=collection_name)
            count = collection.count()
            if count == 0:
                continue
            actual_n = min(n_results, count)
            res = collection.query(query_texts=[query], n_results=actual_n)
            docs = res.get("documents", [[]])[0]
            results.extend(docs)
        except Exception:
            # Collection doesn't exist yet — skip gracefully
            pass

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for doc in results:
        key = doc[:100]
        if key not in seen:
            seen.add(key)
            unique.append(doc)

    return unique


def collection_stats() -> dict:
    """Return document counts per collection for diagnostics."""
    client = _get_client()
    stats = {}
    for name in ["psychodynamic", "narrative", "strengths", "shared"]:
        try:
            col = client.get_collection(name=name)
            stats[name] = col.count()
        except Exception:
            stats[name] = 0
    return stats
