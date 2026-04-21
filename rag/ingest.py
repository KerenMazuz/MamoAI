"""
Ingests PDF files from the 'RAG data/' directory into ChromaDB.
Run once (idempotent): python -m rag.ingest
"""
import os
import re
import hashlib
from pathlib import Path
from typing import List, Tuple

import chromadb
from chromadb.config import Settings

from config import (
    CHROMA_PATH,
    RAG_DATA_PATH,
    PDF_COLLECTION_MAP,
    DEFAULT_CHUNK_SIZE,
    LARGE_FILE_CHUNK_SIZE,
    CHUNK_OVERLAP,
    LARGE_FILES,
)


def _get_chroma_client() -> chromadb.Client:
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def _extract_text_pymupdf(pdf_path: str) -> str:
    """Primary extractor using PyMuPDF (fitz)."""
    import fitz  # pymupdf
    text_parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _extract_text_pdfplumber(pdf_path: str) -> str:
    """Fallback extractor using pdfplumber for problematic encodings."""
    import pdfplumber
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_text(pdf_path: str) -> str:
    """Extract text from PDF, falling back to pdfplumber if needed."""
    try:
        text = _extract_text_pymupdf(pdf_path)
        # Check if extracted text looks garbled (low ratio of recognizable chars)
        if text and len(text) > 100:
            recognizable = sum(1 for c in text if c.isalpha() or c.isspace() or '\u0590' <= c <= '\u05FF')
            if recognizable / len(text) > 0.3:
                return text
    except Exception:
        pass

    try:
        return _extract_text_pdfplumber(pdf_path)
    except Exception as e:
        print(f"  WARNING: Could not extract text from {pdf_path}: {e}")
        return ""


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks by approximate token count (1 token ≈ 4 chars)."""
    char_size = chunk_size * 4
    char_overlap = overlap * 4

    chunks = []
    start = 0
    while start < len(text):
        end = start + char_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += char_size - char_overlap

    return chunks


def _file_hash(pdf_path: str) -> str:
    h = hashlib.md5()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _already_ingested(collection, source_file: str) -> bool:
    """Check if this file has already been ingested by looking for its metadata."""
    try:
        results = collection.get(where={"source_file": source_file}, limit=1)
        return len(results["ids"]) > 0
    except Exception:
        return False


def ingest_all(force: bool = False):
    """Ingest all PDFs from RAG data/ into ChromaDB. Idempotent unless force=True."""
    client = _get_chroma_client()
    rag_dir = Path(RAG_DATA_PATH)

    if not rag_dir.exists():
        print(f"RAG data directory not found: {rag_dir}")
        return

    pdf_files = list(rag_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in RAG data/")
        return

    print(f"Found {len(pdf_files)} PDF files to process...")

    for pdf_path in pdf_files:
        filename = pdf_path.name
        collection_name = PDF_COLLECTION_MAP.get(filename)

        if not collection_name:
            print(f"  SKIP (no collection mapping): {filename}")
            continue

        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        if not force and _already_ingested(collection, filename):
            print(f"  SKIP (already ingested): {filename}")
            continue

        print(f"  Processing: {filename} -> {collection_name}")
        text = _extract_text(str(pdf_path))

        if not text.strip():
            print(f"    WARNING: No text extracted from {filename}")
            continue

        chunk_size = LARGE_FILE_CHUNK_SIZE if filename in LARGE_FILES else DEFAULT_CHUNK_SIZE
        chunks = _chunk_text(text, chunk_size, CHUNK_OVERLAP)

        if not chunks:
            print(f"    WARNING: No chunks generated from {filename}")
            continue

        # Ingest in batches of 100
        batch_size = 100
        total_chunks = len(chunks)
        for batch_start in range(0, total_chunks, batch_size):
            batch = chunks[batch_start: batch_start + batch_size]
            ids = [f"{filename}_{batch_start + i}" for i in range(len(batch))]
            metadatas = [
                {
                    "source_file": filename,
                    "track": collection_name,
                    "chunk_index": batch_start + i,
                }
                for i in range(len(batch))
            ]
            collection.add(documents=batch, ids=ids, metadatas=metadatas)

        print(f"    Ingested {total_chunks} chunks into '{collection_name}'")

    # Also ensure the shared collection exists for retriever
    client.get_or_create_collection(name="shared", metadata={"hnsw:space": "cosine"})
    print("Ingestion complete.")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    ingest_all(force=force)
