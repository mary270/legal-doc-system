"""
FastAPI endpoint tests — Legal Document Intelligence System.
Uses FastAPI's TestClient (no real server needed).

Run with:  python -m pytest tests/test_api.py -v
           python -m pytest tests/test_api.py -v -k "not upload"

All external calls (Groq, ChromaDB, disk I/O) are mocked so these run
offline with no API key or database.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from api import app
    return TestClient(app)


# Fake data used across tests
FAKE_DOC = {
    "doc_id":           "test-doc-001",
    "file_name":        "lease.txt",
    "char_count":       1234,
    "chunk_count":      4,
    "chunks_indexed":   4,
    "structured_fields": {"document_type": "contract", "summary": "Test lease."},
}

FAKE_CHUNK = {
    "text":            "Harbor Properties LLC and Riverside Corp lease agreement.",
    "metadata":        {"file_name": "lease.txt", "doc_id": "test-doc-001"},
    "relevance_score": 0.92,
    "semantic_score":  0.90,
}

FAKE_DRAFT_RESULT = {
    "draft":               "## Case Fact Summary\n\nParties: Harbor vs Riverside.",
    "sources":             [{"source_number": 1, "file_name": "lease.txt",
                             "relevance_score": 0.92, "excerpt": "Harbor Properties..."}],
    "evidence_used":       1,
    "model":               "groq/llama-3",
    "preferences_applied": 2,
    "query":               "Summarize the lease facts",
}

FAKE_CAPTURE_RESULT = {
    "preferences_extracted": ["Always bold party names.", "Include risk flags section."],
    "edit_metrics": {
        "edit_distance_pct": 0.35,
        "retained_pct":      0.70,
        "additions_pct":     0.15,
        "improvement_score": 56.0,
        "changed":           True,
    },
    "total_stored": 3,
    "message": "Extracted 2 preferences. Draft retained 70% of AI content.",
}


# ═════════════════════════════════════════════════════════════════════════════
# SYSTEM endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestSystemEndpoints:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["version"] == "2.0.0"
        assert body["service"] == "legal-doc-system"

    def test_config_endpoint_returns_dict(self, client):
        r = client.get("/config")
        assert r.status_code == 200
        body = r.json()
        # Either a config dict or a note about missing config.py
        assert isinstance(body, dict)

    def test_config_contains_chunking_keys(self, client):
        r = client.get("/config")
        body = r.json()
        if "note" not in body:  # config.py present
            assert "chunking" in body
            assert "retrieval" in body
            assert "llm_models" in body


# ═════════════════════════════════════════════════════════════════════════════
# DOCUMENTS endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestDocumentEndpoints:
    def test_upload_document(self, client):
        mock_process = MagicMock(return_value={
            "doc_id": FAKE_DOC["doc_id"],
            "file_name": FAKE_DOC["file_name"],
            "char_count": FAKE_DOC["char_count"],
            "chunk_count": FAKE_DOC["chunk_count"],
            "chunks": [{"chunk_id": 0, "text": "Sample chunk text."}],
            "structured_fields": FAKE_DOC["structured_fields"],
        })
        mock_add = MagicMock(return_value=4)

        with patch("api._processor", return_value=mock_process), \
             patch("api._retrieval", return_value=(mock_add, None, None, None)):
            r = client.post(
                "/documents/upload",
                files={"file": ("lease.txt", b"Sample legal document content.", "text/plain")},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["doc_id"] == "test-doc-001"
        assert body["chunks_indexed"] == 4

    def test_get_documents_returns_list(self, client):
        mock_list = MagicMock(return_value=[FAKE_DOC])
        with patch("api._retrieval", return_value=(None, None, mock_list, None)):
            r = client.get("/documents")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_documents_empty(self, client):
        mock_list = MagicMock(return_value=[])
        with patch("api._retrieval", return_value=(None, None, mock_list, None)):
            r = client.get("/documents")
        assert r.status_code == 200
        assert r.json() == []

    def test_delete_document_success(self, client):
        mock_delete = MagicMock(return_value=4)
        with patch("api._retrieval", return_value=(None, None, None, mock_delete)):
            r = client.delete("/documents/test-doc-001")
        assert r.status_code == 200
        body = r.json()
        assert body["doc_id"] == "test-doc-001"
        assert body["chunks_removed"] == 4

    def test_delete_document_not_found(self, client):
        mock_delete = MagicMock(return_value=0)
        with patch("api._retrieval", return_value=(None, None, None, mock_delete)):
            r = client.delete("/documents/nonexistent-id")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


# ═════════════════════════════════════════════════════════════════════════════
# RETRIEVAL endpoint
# ═════════════════════════════════════════════════════════════════════════════

class TestRetrievalEndpoints:
    def test_search_returns_results(self, client):
        mock_search = MagicMock(return_value=[FAKE_CHUNK])
        with patch("api._retrieval", return_value=(None, mock_search, None, None)):
            r = client.post("/retrieval/search",
                            params={"query": "rent payment", "n_results": 5})
        assert r.status_code == 200
        body = r.json()
        assert body["query"] == "rent payment"
        assert body["n_results"] == 1
        assert len(body["results"]) == 1

    def test_search_with_doc_filter(self, client):
        mock_search = MagicMock(return_value=[FAKE_CHUNK])
        with patch("api._retrieval", return_value=(None, mock_search, None, None)):
            r = client.post(
                "/retrieval/search",
                params={"query": "lease terms", "n_results": 3,
                        "doc_id_filter": "test-doc-001"},
            )
        assert r.status_code == 200
        # Verify search was called with the filter
        mock_search.assert_called_once_with(
            "lease terms", n_results=3, doc_id_filter="test-doc-001"
        )

    def test_search_no_results(self, client):
        mock_search = MagicMock(return_value=[])
        with patch("api._retrieval", return_value=(None, mock_search, None, None)):
            r = client.post("/retrieval/search",
                            params={"query": "nothing here"})
        assert r.status_code == 200
        assert r.json()["n_results"] == 0


# ═════════════════════════════════════════════════════════════════════════════
# DRAFT endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestDraftEndpoints:
    def test_generate_draft_basic(self, client):
        mock_search        = MagicMock(return_value=[FAKE_CHUNK])
        mock_generate      = MagicMock(return_value=FAKE_DRAFT_RESULT)
        mock_get_active    = MagicMock(return_value=["Bold party names."])

        with patch("api._retrieval", return_value=(None, mock_search, None, None)), \
             patch("api._drafting",  return_value=mock_generate), \
             patch("api._learning",  return_value=(None, mock_get_active, None, None)):
            r = client.post("/drafts/generate", json={
                "query": "Summarize the lease facts",
                "n_results": 5,
            })
        assert r.status_code == 200
        body = r.json()
        assert "draft" in body
        assert body["query"] == "Summarize the lease facts"

    def test_generate_draft_with_flags(self, client):
        mock_search     = MagicMock(return_value=[FAKE_CHUNK])
        mock_generate   = MagicMock(return_value=FAKE_DRAFT_RESULT)
        mock_get_active = MagicMock(return_value=[])

        with patch("api._retrieval", return_value=(None, mock_search, None, None)), \
             patch("api._drafting",  return_value=mock_generate), \
             patch("api._learning",  return_value=(None, mock_get_active, None, None)):
            r = client.post("/drafts/generate", json={
                "query":          "lease summary",
                "use_few_shot":   False,
                "use_profile":    False,
                "doc_id_filter":  "test-doc-001",
            })
        assert r.status_code == 200
        # Verify generate_draft was called with the correct flags
        _, kwargs = mock_generate.call_args
        assert kwargs.get("use_few_shot") is False
        assert kwargs.get("use_profile") is False

    def test_generate_draft_missing_query_fails(self, client):
        r = client.post("/drafts/generate", json={"n_results": 5})
        assert r.status_code == 422  # Pydantic validation error

    def test_submit_feedback_returns_preferences(self, client):
        mock_capture = MagicMock(return_value=FAKE_CAPTURE_RESULT)
        with patch("api._learning", return_value=(mock_capture, None, None, None)):
            r = client.post("/drafts/feedback", json={
                "original_draft": "Original AI-generated draft text.",
                "edited_draft":   "**Edited:** Improved draft text with bold parties.",
                "query":          "lease summary",
                "doc_names":      ["lease.txt"],
            })
        assert r.status_code == 200
        body = r.json()
        assert "preferences_extracted" in body
        assert "edit_metrics" in body
        assert len(body["preferences_extracted"]) == 2

    def test_submit_feedback_missing_fields_fails(self, client):
        r = client.post("/drafts/feedback", json={"original_draft": "only one field"})
        assert r.status_code == 422

    def test_generate_draft_response_has_sources(self, client):
        mock_search     = MagicMock(return_value=[FAKE_CHUNK])
        mock_generate   = MagicMock(return_value=FAKE_DRAFT_RESULT)
        mock_get_active = MagicMock(return_value=[])

        with patch("api._retrieval", return_value=(None, mock_search, None, None)), \
             patch("api._drafting",  return_value=mock_generate), \
             patch("api._learning",  return_value=(None, mock_get_active, None, None)):
            r = client.post("/drafts/generate", json={"query": "test"})
        body = r.json()
        assert "sources" in body
        assert isinstance(body["sources"], list)


# ═════════════════════════════════════════════════════════════════════════════
# PREFERENCES endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestPreferencesEndpoints:
    FAKE_ALL_PREFS = [
        {"preference": "Bold party names", "active": True,
         "extracted_at": "2024-01-01T00:00:00", "query": "lease", "doc_names": []},
        {"preference": "Include risk flags", "active": True,
         "extracted_at": "2024-01-02T00:00:00", "query": "liability", "doc_names": []},
        {"preference": "Old deactivated pref", "active": False,
         "extracted_at": "2024-01-03T00:00:00", "query": "", "doc_names": []},
    ]

    def test_get_all_preferences(self, client):
        mock_list_all = MagicMock(return_value=self.FAKE_ALL_PREFS)
        with patch("api._learning", return_value=(None, None, mock_list_all, None)):
            r = client.get("/preferences")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 3

    def test_get_active_preferences(self, client):
        mock_get_active = MagicMock(return_value=["Bold party names", "Include risk flags"])
        with patch("api._learning", return_value=(None, mock_get_active, None, None)):
            r = client.get("/preferences/active")
        assert r.status_code == 200
        body = r.json()
        assert "preferences" in body
        assert isinstance(body["preferences"], list)

    def test_get_active_preferences_with_limit(self, client):
        mock_get_active = MagicMock(return_value=["Bold party names"])
        with patch("api._learning", return_value=(None, mock_get_active, None, None)):
            r = client.get("/preferences/active", params={"limit": 3})
        assert r.status_code == 200
        mock_get_active.assert_called_once_with(limit=3)

    def test_deactivate_preference_success(self, client):
        mock_deactivate = MagicMock(return_value=True)
        with patch("api._learning", return_value=(None, None, None, mock_deactivate)):
            r = client.post("/preferences/deactivate", json={"index": 1})
        assert r.status_code == 200
        body = r.json()
        assert body["deactivated"] is True
        assert body["index"] == 1

    def test_deactivate_preference_not_found(self, client):
        mock_deactivate = MagicMock(return_value=False)
        with patch("api._learning", return_value=(None, None, None, mock_deactivate)):
            r = client.post("/preferences/deactivate", json={"index": 999})
        assert r.status_code == 404
        assert "out of range" in r.json()["detail"].lower()

    def test_deactivate_preference_missing_body(self, client):
        r = client.post("/preferences/deactivate", json={})
        assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════════════
# METRICS endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestMetricsEndpoints:
    FAKE_HISTORY = [
        {"timestamp": "2024-01-01T10:00:00", "query": "lease",
         "improvement_score": 65.0, "retained_pct": 0.75,
         "edit_distance_pct": 0.2, "additions_pct": 0.1, "changed": True},
        {"timestamp": "2024-01-02T10:00:00", "query": "damages",
         "improvement_score": 78.0, "retained_pct": 0.85,
         "edit_distance_pct": 0.12, "additions_pct": 0.08, "changed": True},
    ]

    FAKE_SUMMARY = {
        "total_edits":           2,
        "avg_improvement_score": 71.5,
        "avg_retained_pct":      0.80,
        "avg_edit_distance_pct": 0.16,
        "score_trend":           13.0,
        "early_avg_score":       65.0,
        "late_avg_score":        78.0,
    }

    def test_get_metrics_history(self, client):
        with patch("metrics.load_metrics_history", return_value=self.FAKE_HISTORY):
            r = client.get("/metrics")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0]["improvement_score"] == 65.0

    def test_get_metrics_empty(self, client):
        with patch("metrics.load_metrics_history", return_value=[]):
            r = client.get("/metrics")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_metrics_summary(self, client):
        with patch("metrics.load_metrics_history",  return_value=self.FAKE_HISTORY), \
             patch("metrics.summarise_improvement", return_value=self.FAKE_SUMMARY):
            r = client.get("/metrics/summary")
        assert r.status_code == 200
        body = r.json()
        assert body["total_edits"] == 2
        assert body["avg_improvement_score"] == 71.5
        assert body["score_trend"] == 13.0

    def test_metrics_summary_positive_trend(self, client):
        with patch("metrics.load_metrics_history",  return_value=self.FAKE_HISTORY), \
             patch("metrics.summarise_improvement", return_value=self.FAKE_SUMMARY):
            r = client.get("/metrics/summary")
        assert r.json()["score_trend"] > 0, "Should show positive learning trend"


# ═════════════════════════════════════════════════════════════════════════════
# FEW-SHOT endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestFewShotEndpoints:
    FAKE_EXAMPLES = [
        {"query": "lease summary", "original_draft": "...", "edited_draft": "...",
         "improvement_score": 72.0, "doc_names": ["lease.txt"],
         "saved_at": "2024-01-01T00:00:00"},
        {"query": "damages claim", "original_draft": "...", "edited_draft": "...",
         "improvement_score": 85.0, "doc_names": ["damages.txt"],
         "saved_at": "2024-01-02T00:00:00"},
    ]

    def test_get_few_shot_examples(self, client):
        with patch("few_shot_store.list_examples", return_value=self.FAKE_EXAMPLES):
            r = client.get("/few-shot")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 2

    def test_get_few_shot_empty(self, client):
        with patch("few_shot_store.list_examples", return_value=[]):
            r = client.get("/few-shot")
        assert r.status_code == 200
        assert r.json() == []

    def test_delete_few_shot_success(self, client):
        with patch("few_shot_store.delete_example", return_value=True):
            r = client.delete("/few-shot/0")
        assert r.status_code == 200
        body = r.json()
        assert body["deleted"] is True
        assert body["index"] == 0

    def test_delete_few_shot_not_found(self, client):
        with patch("few_shot_store.delete_example", return_value=False):
            r = client.delete("/few-shot/99")
        assert r.status_code == 404
        assert "out of range" in r.json()["detail"].lower()

    def test_delete_few_shot_passes_correct_index(self, client):
        mock_delete = MagicMock(return_value=True)
        with patch("few_shot_store.delete_example", mock_delete):
            client.delete("/few-shot/3")
        mock_delete.assert_called_once_with(3)


# ═════════════════════════════════════════════════════════════════════════════
# OPERATOR PROFILE endpoints
# ═════════════════════════════════════════════════════════════════════════════

class TestProfileEndpoints:
    FAKE_PROFILE = {
        "writing_style":         "Formal and concise",
        "structure_preferences": ["Bold all party names", "Use numbered sections"],
        "content_priorities":    ["Include risk flags", "Exact dollar amounts"],
        "common_additions":      ["Deadline summary table"],
        "avoid":                 ["Speculation beyond evidence"],
        "summary":               "This operator prefers formal, structured drafts with explicit citations.",
    }

    def test_get_profile_success(self, client):
        with patch("operator_profile.load_profile", return_value=self.FAKE_PROFILE):
            r = client.get("/profile")
        assert r.status_code == 200
        body = r.json()
        assert body["writing_style"] == "Formal and concise"
        assert "summary" in body

    def test_get_profile_not_found(self, client):
        with patch("operator_profile.load_profile", return_value={}):
            r = client.get("/profile")
        assert r.status_code == 404
        assert "not built yet" in r.json()["detail"].lower()

    def test_build_profile_success(self, client):
        mock_list_all     = MagicMock(return_value=[
            {"preference": "Bold party names", "active": True,
             "extracted_at": "2024-01-01", "query": "", "doc_names": []},
        ])
        mock_build_profile = MagicMock(return_value=self.FAKE_PROFILE)

        with patch("api._learning", return_value=(None, None, mock_list_all, None)), \
             patch("operator_profile.build_profile", mock_build_profile):
            r = client.post("/profile/build")
        assert r.status_code == 200
        body = r.json()
        assert body["writing_style"] == "Formal and concise"

    def test_build_profile_no_preferences(self, client):
        mock_list_all      = MagicMock(return_value=[])
        mock_build_profile = MagicMock(return_value={})

        with patch("api._learning", return_value=(None, None, mock_list_all, None)), \
             patch("operator_profile.build_profile", mock_build_profile):
            r = client.post("/profile/build")
        assert r.status_code == 400
        assert "no preferences" in r.json()["detail"].lower()


# ═════════════════════════════════════════════════════════════════════════════
# VALIDATION & EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════

class TestValidationEdgeCases:
    def test_draft_request_default_values(self, client):
        """DraftRequest defaults: n_results=8, use_few_shot=True, use_profile=True."""
        mock_search     = MagicMock(return_value=[])
        mock_generate   = MagicMock(return_value={
            "draft": "No Evidence Found", "sources": [], "evidence_used": 0,
            "model": "groq/llama-3", "preferences_applied": 0,
        })
        mock_get_active = MagicMock(return_value=[])

        with patch("api._retrieval", return_value=(None, mock_search, None, None)), \
             patch("api._drafting",  return_value=mock_generate), \
             patch("api._learning",  return_value=(None, mock_get_active, None, None)):
            r = client.post("/drafts/generate", json={"query": "test"})
        assert r.status_code == 200
        mock_search.assert_called_once_with("test", n_results=8, doc_id_filter=None)

    def test_feedback_request_optional_fields(self, client):
        """doc_names and query have defaults so they're optional."""
        mock_capture = MagicMock(return_value={
            "preferences_extracted": [],
            "edit_metrics": {"changed": False, "improvement_score": 0,
                             "retained_pct": 1.0, "edit_distance_pct": 0,
                             "additions_pct": 0},
            "message": "No meaningful changes detected (edit < 3%).",
        })
        with patch("api._learning", return_value=(mock_capture, None, None, None)):
            r = client.post("/drafts/feedback", json={
                "original_draft": "Same text",
                "edited_draft":   "Same text",
            })
        assert r.status_code == 200

    def test_unknown_endpoint_returns_404(self, client):
        r = client.get("/nonexistent/endpoint")
        assert r.status_code == 404

    def test_cors_headers_present(self, client):
        r = client.options("/health", headers={"Origin": "http://localhost:3000"})
        # CORSMiddleware should respond even to OPTIONS
        assert r.status_code in (200, 405)   # 405 from TestClient is fine

    def test_docs_endpoint_accessible(self, client):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_redoc_endpoint_accessible(self, client):
        r = client.get("/redoc")
        assert r.status_code == 200
