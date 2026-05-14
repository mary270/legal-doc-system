"""
FastAPI REST API — Legal Document Intelligence System
Full endpoint coverage: documents, drafts, feedback, preferences, metrics, profile, few-shot, config.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

log = logging.getLogger(__name__)

app = FastAPI(
    title="Legal Document Intelligence — Pearson Specter Litt",
    description=(
        "AI pipeline for legal document ingestion, grounded draft generation, "
        "and continuous improvement from operator edits."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lazy imports — avoid loading heavy models at import time
def _processor():
    from document_processor import process_document
    return process_document

def _retrieval():
    from retrieval import add_document, search, list_documents, delete_document
    return add_document, search, list_documents, delete_document

def _drafting():
    from draft_generator import generate_draft
    return generate_draft

def _learning():
    from edit_learner import capture_edit, get_active_preferences, list_all_preferences, deactivate_preference
    return capture_edit, get_active_preferences, list_all_preferences, deactivate_preference


# ── Request / Response models ──────────────────────────────────────────────────

class DraftRequest(BaseModel):
    query:         str
    n_results:     int = 8
    doc_id_filter: str | None = None
    use_few_shot:  bool = True
    use_profile:   bool = True

class EditFeedbackRequest(BaseModel):
    original_draft: str
    edited_draft:   str
    query:          str = ""
    doc_names:      list[str] = []

class DeactivateRequest(BaseModel):
    index: int


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "service": "legal-doc-system", "version": "2.0.0"}


@app.get("/config", tags=["System"])
def get_config() -> dict:
    """Return current system configuration (non-sensitive values only)."""
    try:
        from config import (CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL,
                            DEFAULT_N_RESULTS, HYBRID_SEMANTIC_WEIGHT,
                            HYBRID_BM25_WEIGHT, MAX_ACTIVE_PREFERENCES,
                            COLLECTION_NAME, LLM_MODELS)
        return {
            "chunking":   {"chunk_size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP},
            "retrieval":  {"embed_model": EMBED_MODEL, "collection": COLLECTION_NAME,
                           "default_n": DEFAULT_N_RESULTS,
                           "semantic_weight": HYBRID_SEMANTIC_WEIGHT,
                           "bm25_weight": HYBRID_BM25_WEIGHT},
            "llm_models": [m["name"] for m in LLM_MODELS],
            "learning":   {"max_active_preferences": MAX_ACTIVE_PREFERENCES},
        }
    except ImportError:
        return {"note": "config.py not found — using defaults"}


# ── Document endpoints ─────────────────────────────────────────────────────────

@app.post("/documents/upload", tags=["Documents"],
          summary="Upload and process a legal document (PDF, image, text)")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    process_document = _processor()
    add_document, *_ = _retrieval()

    suffix = Path(file.filename or "upload.txt").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = process_document(tmp_path)
        dest   = _UPLOAD_DIR / f"{result['doc_id']}{suffix}"
        shutil.copy(tmp_path, dest)

        chunks_added = add_document(
            doc_id=result["doc_id"],
            file_name=file.filename or "upload",
            chunks=result["chunks"],
            structured_fields=result["structured_fields"],
        )
        log.info("Uploaded and indexed: %s — %d chunks", file.filename, chunks_added)
        return {
            "doc_id":          result["doc_id"],
            "file_name":       result["file_name"],
            "char_count":      result["char_count"],
            "chunk_count":     result["chunk_count"],
            "chunks_indexed":  chunks_added,
            "structured_fields": result["structured_fields"],
        }
    finally:
        os.unlink(tmp_path)


@app.get("/documents", tags=["Documents"], summary="List all indexed documents")
def get_documents() -> list[dict[str, Any]]:
    _, _, list_documents, _ = _retrieval()
    return list_documents()


@app.delete("/documents/{doc_id}", tags=["Documents"], summary="Remove a document")
def remove_document(doc_id: str) -> dict[str, Any]:
    _, _, _, delete_document = _retrieval()
    deleted = delete_document(doc_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"doc_id": doc_id, "chunks_removed": deleted}


# ── Retrieval endpoint ─────────────────────────────────────────────────────────

@app.post("/retrieval/search", tags=["Retrieval"],
          summary="Hybrid BM25 + semantic search over indexed documents")
def retrieval_search(query: str, n_results: int = 8, doc_id_filter: str | None = None) -> dict:
    _, search, _, _ = _retrieval()
    chunks = search(query, n_results=n_results, doc_id_filter=doc_id_filter)
    return {"query": query, "n_results": len(chunks), "results": chunks}


# ── Draft endpoints ────────────────────────────────────────────────────────────

@app.post("/drafts/generate", tags=["Drafts"],
          summary="Generate a grounded case fact summary with citations")
def generate(req: DraftRequest) -> dict[str, Any]:
    _, search, _, _ = _retrieval()
    generate_draft   = _drafting()
    _, get_active_preferences, _, _ = _learning()

    chunks = search(req.query, n_results=req.n_results, doc_id_filter=req.doc_id_filter)
    prefs  = get_active_preferences()
    result = generate_draft(
        query=req.query,
        retrieved_chunks=chunks,
        learned_preferences=prefs,
        use_few_shot=req.use_few_shot,
        use_profile=req.use_profile,
    )
    result["query"] = req.query
    return result


@app.post("/drafts/feedback", tags=["Drafts"],
          summary="Submit operator edits — extracts preferences + computes improvement metrics")
def submit_feedback(req: EditFeedbackRequest) -> dict[str, Any]:
    capture_edit, *_ = _learning()
    return capture_edit(
        original_draft=req.original_draft,
        edited_draft=req.edited_draft,
        query=req.query,
        doc_names=req.doc_names,
    )


# ── Preferences endpoints ──────────────────────────────────────────────────────

@app.get("/preferences", tags=["Learning"], summary="List all learned operator preferences")
def get_preferences() -> list[dict[str, Any]]:
    _, _, list_all_preferences, _ = _learning()
    return list_all_preferences()


@app.get("/preferences/active", tags=["Learning"], summary="Get active preferences injected into drafts")
def get_active_prefs(limit: int = 10) -> dict:
    _, get_active_preferences, _, _ = _learning()
    return {"preferences": get_active_preferences(limit=limit)}


@app.post("/preferences/deactivate", tags=["Learning"], summary="Deactivate a learned preference")
def deactivate(req: DeactivateRequest) -> dict:
    _, _, _, deactivate_preference = _learning()
    if not deactivate_preference(req.index):
        raise HTTPException(status_code=404, detail="Index out of range")
    return {"deactivated": True, "index": req.index}


# ── Metrics endpoints ──────────────────────────────────────────────────────────

@app.get("/metrics", tags=["Metrics"], summary="Full edit metrics history")
def get_metrics() -> list[dict[str, Any]]:
    from metrics import load_metrics_history
    return load_metrics_history()


@app.get("/metrics/summary", tags=["Metrics"],
         summary="Aggregated improvement metrics — shows learning trend")
def get_metrics_summary() -> dict[str, Any]:
    from metrics import load_metrics_history, summarise_improvement
    return summarise_improvement(load_metrics_history())


# ── Few-shot endpoints ─────────────────────────────────────────────────────────

@app.get("/few-shot", tags=["Learning"], summary="List stored few-shot gold examples")
def get_few_shot() -> list[dict[str, Any]]:
    from few_shot_store import list_examples
    return list_examples()


@app.delete("/few-shot/{index}", tags=["Learning"], summary="Delete a few-shot example")
def delete_few_shot(index: int) -> dict:
    from few_shot_store import delete_example
    if not delete_example(index):
        raise HTTPException(status_code=404, detail="Index out of range")
    return {"deleted": True, "index": index}


# ── Operator profile endpoints ─────────────────────────────────────────────────

@app.get("/profile", tags=["Learning"], summary="Get the current operator preference profile")
def get_profile() -> dict[str, Any]:
    from operator_profile import load_profile
    profile = load_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not built yet. POST /profile/build first.")
    return profile


@app.post("/profile/build", tags=["Learning"],
          summary="Rebuild operator profile from all stored preferences")
def build_profile_endpoint() -> dict[str, Any]:
    from operator_profile import build_profile
    _, _, list_all_preferences, _ = _learning()
    prefs   = list_all_preferences()
    profile = build_profile(prefs)
    if not profile:
        raise HTTPException(status_code=400, detail="No preferences available to build profile.")
    return profile
