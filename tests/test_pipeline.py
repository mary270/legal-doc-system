"""
Integration tests for the full pipeline.
Run with: python -m pytest tests/ -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ── Document Processor ─────────────────────────────────────────────────────────

class TestDocumentProcessor:
    def test_process_plain_text(self, tmp_path):
        from document_processor import process_document
        doc = tmp_path / "test.txt"
        doc.write_text("This is a test legal document between Party A and Party B dated 2024-01-01.")
        result = process_document(str(doc))
        assert result["doc_id"]
        assert result["raw_text"]
        assert len(result["chunks"]) >= 1
        assert "structured_fields" in result

    def test_chunk_overlap(self, tmp_path):
        from document_processor import _chunk_text
        long_text = " ".join(["word"] * 2000)
        chunks = _chunk_text(long_text, chunk_size=800, overlap=150)
        assert len(chunks) > 1
        # Verify overlap: end of chunk N overlaps start of chunk N+1
        for i in range(len(chunks) - 1):
            assert chunks[i]["word_end"] > chunks[i + 1]["word_start"]

    def test_text_cleaning(self):
        from document_processor import _clean_text
        dirty = "Hello\x00World\x0c\n\n\n\nTest\nﬁle"
        clean = _clean_text(dirty)
        assert "\x00" not in clean
        assert "\x0c" not in clean
        assert "\n\n\n" not in clean
        assert "fi" in clean  # ligature fix

    def test_process_noisy_text(self, tmp_path):
        from document_processor import process_document
        # Simulate OCR noise
        noisy = tmp_path / "noisy.txt"
        noisy.write_text(
            "Thi5 1ease Agr33ment is entered int0 as 0f March 12, 2O22 "
            "by and between Harb0r Pr0perties LLC and R1verside Corp."
        )
        result = process_document(str(noisy))
        assert result["char_count"] > 0
        assert result["chunk_count"] >= 1


# ── Retrieval ──────────────────────────────────────────────────────────────────

class TestRetrieval:
    def test_add_and_search(self, tmp_path):
        # Use isolated chroma DB for tests
        import chromadb
        from chromadb.utils import embedding_functions
        import retrieval

        original_path = retrieval._CHROMA_PATH
        retrieval._CHROMA_PATH = str(tmp_path / "test_chroma")

        try:
            chunks = [
                {"chunk_id": 0, "text": "Harbor Properties LLC leases office space to Riverside Corp."},
                {"chunk_id": 1, "text": "The monthly rent is $38,500 due on the first of each month."},
            ]
            added = retrieval.add_document("test-doc-1", "test.txt", chunks, {"document_type": "contract", "summary": "test"})
            assert added == 2

            results = retrieval.search("rent payment amount", n_results=2)
            assert len(results) >= 1
            assert any("38,500" in r["text"] for r in results)
        finally:
            retrieval._CHROMA_PATH = original_path

    def test_empty_search(self, tmp_path):
        import retrieval
        retrieval._CHROMA_PATH = str(tmp_path / "empty_chroma")
        results = retrieval.search("anything", n_results=5)
        assert results == []


# ── Draft Generator ────────────────────────────────────────────────────────────

class TestDraftGenerator:
    def test_no_chunks_returns_placeholder(self):
        from draft_generator import generate_draft
        result = generate_draft(query="test query", retrieved_chunks=[])
        assert "No Evidence Found" in result["draft"]
        assert result["evidence_used"] == 0

    def test_draft_with_chunks(self):
        from draft_generator import generate_draft
        fake_chunks = [{
            "text": "Harbor Properties LLC and Riverside Corporation entered into a lease on March 12, 2022.",
            "metadata": {"file_name": "lease.txt", "doc_id": "abc"},
            "relevance_score": 0.95,
        }]
        result = generate_draft(query="Summarize the lease facts", retrieved_chunks=fake_chunks)
        assert result["draft"]
        assert result["evidence_used"] == 1
        assert len(result["sources"]) == 1


# ── Edit Learner ───────────────────────────────────────────────────────────────

class TestEditLearner:
    def test_no_change_detected(self, tmp_path, monkeypatch):
        import edit_learner
        monkeypatch.setattr(edit_learner, "_PREFS_FILE", tmp_path / "prefs.json")
        result = edit_learner.capture_edit("same text", "same text")
        assert result["preferences_extracted"] == []
        assert "No changes" in result["message"]

    def test_preferences_persist(self, tmp_path, monkeypatch):
        import edit_learner
        monkeypatch.setattr(edit_learner, "_PREFS_FILE", tmp_path / "prefs.json")
        # Simulate a real-looking edit
        original = "The parties are Harbor and Riverside.\nRent is due monthly."
        edited = "**PARTIES:** Harbor Properties LLC (Landlord) and Riverside Corporation (Tenant).\n**RENT:** $38,500.00 per month, due on the 1st."
        result = edit_learner.capture_edit(original, edited, query="lease facts")
        # Should extract preferences (Claude call)
        assert "preferences_extracted" in result
        all_prefs = edit_learner.list_all_preferences()
        assert len(all_prefs) == len(result["preferences_extracted"])

    def test_deactivate_preference(self, tmp_path, monkeypatch):
        import edit_learner
        pref_file = tmp_path / "prefs.json"
        monkeypatch.setattr(edit_learner, "_PREFS_FILE", pref_file)
        # Manually write a preference
        import json
        pref_file.write_text(json.dumps([{"preference": "Test pref", "extracted_at": "2024-01-01", "query": "", "doc_names": [], "active": True}]))
        success = edit_learner.deactivate_preference(0)
        assert success
        prefs = edit_learner.list_all_preferences()
        assert not prefs[0]["active"]
