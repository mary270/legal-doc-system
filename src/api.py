"""
FastAPI REST API for the legal document drafting system.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from document_processor import process_document
from retrieval import add_document, search, list_documents, delete_document
from draft_generator import generate_draft
from edit_learner import capture_edit, get_active_preferences, list_all_preferences, deactivate_preference

app = FastAPI(
    title="Legal Document Drafting System",
    description="Pearson Specter Litt — AI-powered legal document ingestion and grounded drafting",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Request / Response models ──────────────────────────────────────────────────

class DraftRequest(BaseModel):
    query: str
    n_results: int = 8
    doc_id_filter: str | None = None


class EditFeedbackRequest(BaseModel):
    original_draft: str
    edited_draft: str
    query: str = ""
    doc_names: list[str] = []


class DeactivateRequest(BaseModel):
    index: int


# ── Document endpoints ─────────────────────────────────────────────────────────

@app.post("/documents/upload", summary="Upload and process a legal document")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "doc.txt").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = process_document(tmp_path)
        # Persist a copy for reference
        dest = _UPLOAD_DIR / f"{result['doc_id']}{suffix}"
        shutil.copy(tmp_path, dest)
        result["stored_path"] = str(dest)

        # Index into vector store
        chunks_added = add_document(
            doc_id=result["doc_id"],
            file_name=file.filename or "upload",
            chunks=result["chunks"],
            structured_fields=result["structured_fields"],
        )
        result["chunks_indexed"] = chunks_added

        # Don't return full raw text in API response (can be large)
        result.pop("chunks", None)
        return result
    finally:
        os.unlink(tmp_path)


@app.get("/documents", summary="List all processed documents")
def get_documents() -> list[dict[str, Any]]:
    return list_documents()


@app.delete("/documents/{doc_id}", summary="Remove a document from the store")
def remove_document(doc_id: str) -> dict[str, Any]:
    deleted = delete_document(doc_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"doc_id": doc_id, "chunks_removed": deleted}


# ── Draft endpoints ────────────────────────────────────────────────────────────

@app.post("/drafts/generate", summary="Generate a grounded case fact summary")
def generate(req: DraftRequest) -> dict[str, Any]:
    chunks = search(req.query, n_results=req.n_results, doc_id_filter=req.doc_id_filter)
    preferences = get_active_preferences()
    result = generate_draft(query=req.query, retrieved_chunks=chunks, learned_preferences=preferences)
    result["query"] = req.query
    result["retrieved_chunks"] = len(chunks)
    return result


@app.post("/drafts/feedback", summary="Submit operator edits to improve future drafts")
def submit_feedback(req: EditFeedbackRequest) -> dict[str, Any]:
    return capture_edit(
        original_draft=req.original_draft,
        edited_draft=req.edited_draft,
        query=req.query,
        doc_names=req.doc_names,
    )


# ── Preferences endpoints ──────────────────────────────────────────────────────

@app.get("/preferences", summary="List all learned operator preferences")
def get_preferences() -> list[dict[str, Any]]:
    return list_all_preferences()


@app.post("/preferences/deactivate", summary="Deactivate a learned preference")
def deactivate(req: DeactivateRequest) -> dict[str, Any]:
    success = deactivate_preference(req.index)
    if not success:
        raise HTTPException(status_code=404, detail="Preference index out of range")
    return {"deactivated": True, "index": req.index}


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "legal-doc-system"}
