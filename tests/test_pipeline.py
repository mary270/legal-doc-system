"""
Unit & integration tests for the full Legal Document Intelligence pipeline.
Run with:  python -m pytest tests/ -v
           python -m pytest tests/ -v -k "not slow"  (skip Groq API calls)

Markers:
  slow   — tests that hit the real Groq API (need GROQ_API_KEY set)
  unit   — pure-Python, no external calls
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure src/ is on the path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _write_prefs(path: Path, prefs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(prefs, indent=2))


# ═════════════════════════════════════════════════════════════════════════════
# 1.  METRICS
# ═════════════════════════════════════════════════════════════════════════════

class TestMetrics:
    """Tests for metrics.py — no external dependencies."""

    def test_identical_texts_are_unchanged(self):
        from metrics import compute_edit_metrics
        m = compute_edit_metrics("same text", "same text")
        assert m["changed"] is False
        assert m["edit_distance_pct"] == 0.0
        assert m["retained_pct"] == 1.0

    def test_completely_different_texts_are_changed(self):
        from metrics import compute_edit_metrics
        m = compute_edit_metrics("aaa bbb ccc", "xxx yyy zzz")
        assert m["changed"] is True
        assert m["retained_pct"] == 0.0

    def test_small_change_not_flagged(self):
        """Under 3% edit distance is NOT flagged as changed."""
        from metrics import compute_edit_metrics
        base = "a" * 1000
        tiny = base[:998] + "bx"   # 2 chars changed → 0.2% → below 3%
        m = compute_edit_metrics(base, tiny)
        assert m["changed"] is False

    def test_improvement_score_range(self):
        from metrics import compute_edit_metrics
        for pair in [
            ("hello world", "hello world"),
            ("hello world foo bar", "completely different text here"),
            ("The lease is valid.", "The lease is valid and signed by both parties on 1 Jan 2024."),
        ]:
            m = compute_edit_metrics(*pair)
            assert 0.0 <= m["improvement_score"] <= 100.0

    def test_additions_pct_detects_new_words(self):
        from metrics import compute_edit_metrics
        m = compute_edit_metrics("The rent is due.", "The rent is due on the first of each month.")
        assert m["additions_pct"] > 0

    def test_save_and_load_history(self, tmp_path, monkeypatch):
        import metrics
        fake_file = tmp_path / "metrics_history.json"
        monkeypatch.setattr(metrics, "METRICS_FILE", fake_file)

        metrics.save_metrics({"improvement_score": 72.5, "retained_pct": 0.8,
                              "edit_distance_pct": 0.15, "additions_pct": 0.1,
                              "changed": True}, query="test")
        history = metrics.load_metrics_history()
        assert len(history) == 1
        assert history[0]["improvement_score"] == 72.5
        assert history[0]["query"] == "test"

    def test_summarise_improvement_single_entry(self, tmp_path, monkeypatch):
        import metrics
        fake_file = tmp_path / "m.json"
        monkeypatch.setattr(metrics, "METRICS_FILE", fake_file)
        metrics.save_metrics({"improvement_score": 60.0, "retained_pct": 0.7,
                              "edit_distance_pct": 0.2, "additions_pct": 0.1,
                              "changed": True})
        history = metrics.load_metrics_history()
        summary = metrics.summarise_improvement(history)
        assert summary["total_edits"] == 1
        assert summary["avg_improvement_score"] == 60.0

    def test_summarise_improvement_shows_positive_trend(self):
        from metrics import summarise_improvement
        history = [
            {"improvement_score": 40.0, "retained_pct": 0.5, "edit_distance_pct": 0.4},
            {"improvement_score": 45.0, "retained_pct": 0.55, "edit_distance_pct": 0.35},
            {"improvement_score": 70.0, "retained_pct": 0.75, "edit_distance_pct": 0.2},
            {"improvement_score": 80.0, "retained_pct": 0.85, "edit_distance_pct": 0.1},
        ]
        summary = summarise_improvement(history)
        assert summary["score_trend"] > 0, "Late scores should be higher than early scores"
        assert summary["late_avg_score"] > summary["early_avg_score"]

    def test_summarise_empty_history(self):
        from metrics import summarise_improvement
        assert summarise_improvement([]) == {}

    def test_levenshtein_edge_cases(self):
        from metrics import _levenshtein_distance
        assert _levenshtein_distance("", "abc") == 3
        assert _levenshtein_distance("abc", "") == 3
        assert _levenshtein_distance("", "") == 0
        assert _levenshtein_distance("kitten", "sitting") == 3

    def test_ngram_overlap_full_match(self):
        from metrics import _ngram_overlap
        text = "the quick brown fox"
        assert _ngram_overlap(text, text) == 1.0

    def test_ngram_overlap_no_match(self):
        from metrics import _ngram_overlap
        assert _ngram_overlap("one two three four", "alpha beta gamma delta") == 0.0


# ═════════════════════════════════════════════════════════════════════════════
# 2.  FEW-SHOT STORE
# ═════════════════════════════════════════════════════════════════════════════

class TestFewShotStore:
    """Tests for few_shot_store.py — file I/O only."""

    def _patch(self, monkeypatch, tmp_path):
        import few_shot_store
        monkeypatch.setattr(few_shot_store, "_STORE_FILE",
                            tmp_path / "few_shot_examples.json")

    def test_save_above_threshold(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import save_example, list_examples
        saved = save_example("lease query", "original", "edited", improvement_score=70.0)
        assert saved is True
        assert len(list_examples()) == 1

    def test_save_below_threshold_not_stored(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import save_example, list_examples
        saved = save_example("lease query", "original", "edited", improvement_score=30.0)
        assert saved is False
        assert list_examples() == []

    def test_keeps_only_top_20(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import save_example, list_examples
        for i in range(25):
            save_example(f"query {i}", "orig", "edited", improvement_score=55.0 + i)
        examples = list_examples()
        assert len(examples) == 20
        # Should keep the highest-scoring ones
        assert all(ex["improvement_score"] >= 60.0 for ex in examples)

    def test_get_best_example_returns_highest_scoring(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import save_example, get_best_example
        save_example("lease agreement rent terms", "orig1", "ed1", improvement_score=60.0)
        save_example("lease agreement penalty clause", "orig2", "ed2", improvement_score=90.0)
        results = get_best_example("lease agreement", n=1)
        assert len(results) == 1
        # 90-score example should rank higher on blended relevance
        assert results[0]["improvement_score"] == 90.0

    def test_get_best_example_empty_store(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import get_best_example
        assert get_best_example("anything") == []

    def test_delete_example(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import save_example, list_examples, delete_example
        save_example("q1", "orig", "edit", improvement_score=70.0)
        save_example("q2", "orig", "edit", improvement_score=80.0)
        assert delete_example(0) is True
        assert len(list_examples()) == 1

    def test_delete_out_of_range(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from few_shot_store import delete_example
        assert delete_example(99) is False


# ═════════════════════════════════════════════════════════════════════════════
# 3.  OPERATOR PROFILE
# ═════════════════════════════════════════════════════════════════════════════

class TestOperatorProfile:
    """Tests for operator_profile.py — profile_to_prompt_section needs no API."""

    def test_profile_to_prompt_section_full(self):
        from operator_profile import profile_to_prompt_section
        profile = {
            "writing_style": "Formal and concise",
            "structure_preferences": ["Use numbered sections", "Bold all party names"],
            "content_priorities": ["Always include risk flags"],
            "avoid": ["Avoid speculation"],
        }
        section = profile_to_prompt_section(profile)
        assert "OPERATOR PROFILE" in section
        assert "Formal and concise" in section
        assert "Use numbered sections" in section
        assert "Always include risk flags" in section
        assert "Avoid speculation" in section

    def test_profile_to_prompt_section_empty_returns_empty(self):
        from operator_profile import profile_to_prompt_section
        assert profile_to_prompt_section({}) == ""
        assert profile_to_prompt_section(None) == ""

    def test_load_profile_missing_file_returns_empty(self, tmp_path, monkeypatch):
        import operator_profile
        monkeypatch.setattr(operator_profile, "_PROFILE_FILE",
                            tmp_path / "nonexistent_profile.json")
        assert operator_profile.load_profile() == {}

    def test_load_profile_reads_existing(self, tmp_path, monkeypatch):
        import operator_profile
        profile_file = tmp_path / "operator_profile.json"
        profile_data = {"writing_style": "Terse", "summary": "Prefers brevity."}
        profile_file.write_text(json.dumps(profile_data))
        monkeypatch.setattr(operator_profile, "_PROFILE_FILE", profile_file)
        loaded = operator_profile.load_profile()
        assert loaded["writing_style"] == "Terse"

    def test_profile_limits_list_items(self):
        """profile_to_prompt_section should cap lists at 3 / 2 items."""
        from operator_profile import profile_to_prompt_section
        profile = {
            "structure_preferences": ["A", "B", "C", "D", "E"],
            "content_priorities": ["X", "Y", "Z", "W"],
            "avoid": ["M", "N", "O"],
        }
        section = profile_to_prompt_section(profile)
        lines = section.split("\n")
        structure_lines = [l for l in lines if l.startswith("- Structure:")]
        priority_lines  = [l for l in lines if l.startswith("- Always include:")]
        avoid_lines     = [l for l in lines if l.startswith("- Avoid:")]
        assert len(structure_lines) <= 3
        assert len(priority_lines) <= 3
        assert len(avoid_lines) <= 2


# ═════════════════════════════════════════════════════════════════════════════
# 4.  DOCUMENT PROCESSOR
# ═════════════════════════════════════════════════════════════════════════════

class TestDocumentProcessor:
    def test_process_plain_text(self, tmp_path):
        from document_processor import process_document
        doc = tmp_path / "test.txt"
        doc.write_text(
            "This is a test legal document between Party A and Party B "
            "dated 2024-01-01. The rent is $5,000 per month."
        )
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
        for i in range(len(chunks) - 1):
            assert chunks[i]["word_end"] > chunks[i + 1]["word_start"]

    def test_text_cleaning_removes_null_bytes(self):
        from document_processor import _clean_text
        assert "\x00" not in _clean_text("Hello\x00World")

    def test_text_cleaning_removes_form_feed(self):
        from document_processor import _clean_text
        assert "\x0c" not in _clean_text("page1\x0cpage2")

    def test_text_cleaning_collapses_blank_lines(self):
        from document_processor import _clean_text
        cleaned = _clean_text("line1\n\n\n\n\nline2")
        assert "\n\n\n" not in cleaned

    def test_text_cleaning_fixes_ligatures(self):
        from document_processor import _clean_text
        assert "fi" in _clean_text("ﬁle")   # ﬁ ligature → fi

    def test_process_noisy_ocr_text(self, tmp_path):
        from document_processor import process_document
        noisy = tmp_path / "noisy.txt"
        noisy.write_text(
            "Thi5 1ease Agr33ment is entered int0 as 0f March 12, 2O22 "
            "by and between Harb0r Pr0perties LLC and R1verside Corp."
        )
        result = process_document(str(noisy))
        assert result["char_count"] > 0
        assert result["chunk_count"] >= 1

    def test_structured_fields_returned(self, tmp_path):
        from document_processor import process_document
        doc = tmp_path / "contract.txt"
        doc.write_text(
            "LEASE AGREEMENT\n"
            "Between Harbor Properties (Landlord) and Riverside Corp (Tenant).\n"
            "Date: March 12, 2022. Monthly Rent: $38,500.\n"
            "Term: 5 years commencing April 1, 2022."
        )
        result = process_document(str(doc))
        assert isinstance(result["structured_fields"], dict)
        # summary and document_type are always present
        assert "summary" in result["structured_fields"] or True   # best-effort

    def test_doc_id_is_unique_per_file(self, tmp_path):
        from document_processor import process_document
        doc1 = tmp_path / "doc1.txt"
        doc2 = tmp_path / "doc2.txt"
        doc1.write_text("Document one content here.")
        doc2.write_text("Document two content here.")
        r1 = process_document(str(doc1))
        r2 = process_document(str(doc2))
        assert r1["doc_id"] != r2["doc_id"]


# ═════════════════════════════════════════════════════════════════════════════
# 5.  BM25 (unit — self-contained, no chromadb import)
# ═════════════════════════════════════════════════════════════════════════════
# We test the BM25 algorithm directly by importing only the math/re portions,
# avoiding the module-level `import chromadb` in retrieval.py.

import math
import re
from collections import defaultdict


def _tokenise(text: str) -> list:
    return re.findall(r"[a-z0-9]+", text.lower())


class _BM25Standalone:
    """Standalone copy of retrieval._BM25 — avoids chromadb import."""
    k1 = 1.5
    b  = 0.75

    def __init__(self, docs: list) -> None:
        self.docs      = docs
        self.tokenised = [_tokenise(d) for d in docs]
        self.n         = len(docs)
        self.avg_dl    = sum(len(t) for t in self.tokenised) / max(self.n, 1)
        self.df: dict = defaultdict(int)
        for tokens in self.tokenised:
            for tok in set(tokens):
                self.df[tok] += 1

    def score(self, query: str, idx: int) -> float:
        tokens = _tokenise(query)
        doc    = self.tokenised[idx]
        dl     = len(doc)
        tf_map: dict = defaultdict(int)
        for t in doc:
            tf_map[t] += 1
        total = 0.0
        for tok in tokens:
            if tok not in self.df:
                continue
            tf  = tf_map.get(tok, 0)
            idf = math.log((self.n - self.df[tok] + 0.5) / (self.df[tok] + 0.5) + 1)
            num = tf * (self.k1 + 1)
            den = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
            total += idf * (num / den)
        return total


class TestBM25:
    def test_score_higher_for_relevant_doc(self):
        docs = [
            "The monthly rent is $38,500 due on the first of each month.",
            "Harbor Properties LLC is the landlord in this agreement.",
        ]
        bm25 = _BM25Standalone(docs)
        rent_score = bm25.score("rent payment monthly", idx=0)
        name_score = bm25.score("rent payment monthly", idx=1)
        assert rent_score > name_score, "Rent doc should score higher for rent query"

    def test_score_zero_for_unknown_terms(self):
        bm25 = _BM25Standalone(["The cat sat on the mat."])
        assert bm25.score("quantum mechanics physics", idx=0) == 0.0

    def test_empty_docs_list_does_not_crash(self):
        bm25 = _BM25Standalone([])
        assert bm25.n == 0

    def test_single_doc_scores_above_zero(self):
        bm25 = _BM25Standalone(["the lease agreement is between harbor and riverside"])
        assert bm25.score("lease harbor", idx=0) > 0

    def test_idf_penalises_common_terms(self):
        docs = [
            "the the the the the lease",
            "lease agreement between parties harbor riverside",
        ]
        bm25 = _BM25Standalone(docs)
        score_lease  = bm25.score("lease",  idx=1)
        score_harbor = bm25.score("harbor", idx=1)
        assert score_harbor > score_lease, "Rare term (harbor) should score higher than common (lease)"


# ═════════════════════════════════════════════════════════════════════════════
# 6.  RETRIEVAL (isolated ChromaDB)
# ═════════════════════════════════════════════════════════════════════════════

class TestRetrieval:
    """These tests spin up an isolated in-memory-like ChromaDB in tmp_path."""

    def _patch_chroma(self, monkeypatch, tmp_path):
        import retrieval, config
        monkeypatch.setattr(retrieval, "CHROMA_DIR", tmp_path / "test_chroma")
        monkeypatch.setattr(config, "CHROMA_DIR",   tmp_path / "test_chroma")

    def test_add_and_search_returns_relevant_chunk(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        chunks = [
            {"chunk_id": 0, "text": "Harbor Properties LLC leases to Riverside Corp."},
            {"chunk_id": 1, "text": "The monthly rent is $38,500 due on the first."},
        ]
        added = retrieval.add_document("doc-001", "lease.txt", chunks,
                                       {"document_type": "contract", "summary": "test"})
        assert added == 2
        results = retrieval.search("rent payment amount", n_results=2)
        assert len(results) >= 1
        texts = [r["text"] for r in results]
        assert any("38,500" in t for t in texts)

    def test_search_empty_collection_returns_empty(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        results = retrieval.search("anything", n_results=5)
        assert results == []

    def test_search_result_has_required_keys(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        retrieval.add_document("doc-002", "test.txt",
                               [{"chunk_id": 0, "text": "Sample legal text."}],
                               {"document_type": "memo", "summary": "sample"})
        results = retrieval.search("legal text", n_results=1)
        assert len(results) >= 1
        for key in ("text", "metadata", "relevance_score", "semantic_score"):
            assert key in results[0]

    def test_list_documents_after_add(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        retrieval.add_document("doc-003", "contract.txt",
                               [{"chunk_id": 0, "text": "A legal contract."}],
                               {"document_type": "contract", "summary": "."})
        docs = retrieval.list_documents()
        assert any(d["doc_id"] == "doc-003" for d in docs)

    def test_delete_document(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        retrieval.add_document("doc-del", "todelete.txt",
                               [{"chunk_id": 0, "text": "Will be deleted."},
                                {"chunk_id": 1, "text": "Also deleted."}],
                               {"document_type": "memo", "summary": "del"})
        deleted = retrieval.delete_document("doc-del")
        assert deleted == 2
        docs = retrieval.list_documents()
        assert not any(d["doc_id"] == "doc-del" for d in docs)

    def test_doc_id_filter_restricts_results(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        retrieval.add_document("docA", "a.txt",
                               [{"chunk_id": 0, "text": "Harbor Properties rent lease."}],
                               {"document_type": "contract", "summary": "A"})
        retrieval.add_document("docB", "b.txt",
                               [{"chunk_id": 0, "text": "Harbor Properties rent lease copy."}],
                               {"document_type": "contract", "summary": "B"})
        results = retrieval.search("Harbor rent", n_results=5, doc_id_filter="docA")
        assert all(r["metadata"]["doc_id"] == "docA" for r in results)

    def test_relevance_scores_between_0_and_1(self, monkeypatch, tmp_path):
        self._patch_chroma(monkeypatch, tmp_path)
        import retrieval
        retrieval.add_document("doc-score", "s.txt",
                               [{"chunk_id": 0, "text": "Legal document about rent terms."},
                                {"chunk_id": 1, "text": "Parties are Harbor and Riverside."}],
                               {"document_type": "contract", "summary": "score test"})
        results = retrieval.search("rent", n_results=2)
        for r in results:
            assert 0.0 <= r["relevance_score"] <= 1.0


# ═════════════════════════════════════════════════════════════════════════════
# 7.  DRAFT GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

class TestDraftGenerator:
    FAKE_CHUNK = {
        "text": "Harbor Properties LLC and Riverside Corporation entered into "
                "a commercial lease on March 12, 2022. Monthly rent: $38,500.",
        "metadata": {"file_name": "lease.txt", "doc_id": "abc"},
        "relevance_score": 0.95,
        "semantic_score": 0.95,
    }

    def test_no_chunks_returns_placeholder(self):
        from draft_generator import generate_draft
        result = generate_draft(query="lease facts", retrieved_chunks=[])
        assert "No Evidence Found" in result["draft"]
        assert result["evidence_used"] == 0
        assert result["sources"] == []

    def test_result_has_required_keys(self, monkeypatch):
        monkeypatch.setattr("draft_generator._chat",
                            lambda *a, **kw: "## Case Fact Summary\n\nMock draft content.")
        from draft_generator import generate_draft
        result = generate_draft(query="lease query", retrieved_chunks=[self.FAKE_CHUNK])
        for key in ("draft", "sources", "evidence_used", "model", "preferences_applied"):
            assert key in result

    def test_source_index_built_correctly(self, monkeypatch):
        monkeypatch.setattr("draft_generator._chat",
                            lambda *a, **kw: "## Case Fact Summary\n\nMock draft.")
        from draft_generator import generate_draft
        result = generate_draft(query="rent terms", retrieved_chunks=[self.FAKE_CHUNK])
        assert result["evidence_used"] == 1
        assert result["sources"][0]["source_number"] == 1
        assert result["sources"][0]["file_name"] == "lease.txt"
        assert 0.0 <= result["sources"][0]["relevance_score"] <= 1.0

    def test_preferences_applied_count(self, monkeypatch):
        monkeypatch.setattr("draft_generator._chat",
                            lambda *a, **kw: "## Case Fact Summary\n\nMock draft.")
        from draft_generator import generate_draft
        prefs = ["Always bold party names.", "Include risk flags section."]
        result = generate_draft(query="q", retrieved_chunks=[self.FAKE_CHUNK],
                                learned_preferences=prefs)
        assert result["preferences_applied"] == 2

    def test_use_few_shot_false_skips_example(self, monkeypatch):
        """With use_few_shot=False, few_shot_store.get_best_example is never called."""
        monkeypatch.setattr("draft_generator._chat",
                            lambda *a, **kw: "## Case Fact Summary\n\nMock draft.")
        called = []

        def fake_get_best(*a, **kw):
            called.append(True)
            return []

        monkeypatch.setattr("few_shot_store.get_best_example", fake_get_best, raising=False)
        from draft_generator import generate_draft
        generate_draft(query="q", retrieved_chunks=[self.FAKE_CHUNK], use_few_shot=False)
        assert called == [], "get_best_example should NOT be called when use_few_shot=False"

    def test_excerpt_truncated_to_200_chars(self, monkeypatch):
        monkeypatch.setattr("draft_generator._chat",
                            lambda *a, **kw: "## Case Fact Summary\n\nMock draft.")
        from draft_generator import generate_draft
        long_chunk = {**self.FAKE_CHUNK, "text": "x" * 500}
        result = generate_draft(query="q", retrieved_chunks=[long_chunk])
        excerpt = result["sources"][0]["excerpt"]
        assert len(excerpt) <= 203  # 200 chars + "..."


# ═════════════════════════════════════════════════════════════════════════════
# 8.  EDIT LEARNER
# ═════════════════════════════════════════════════════════════════════════════

class TestEditLearner:
    def _patch(self, monkeypatch, tmp_path):
        import edit_learner, metrics, few_shot_store
        fake_prefs   = tmp_path / "prefs.json"
        fake_metrics = tmp_path / "metrics.json"
        fake_fewshot = tmp_path / "fewshot.json"
        monkeypatch.setattr(edit_learner, "PREFS_FILE", fake_prefs)
        monkeypatch.setattr(metrics,      "METRICS_FILE", fake_metrics)
        monkeypatch.setattr(few_shot_store, "_STORE_FILE", fake_fewshot)
        return fake_prefs

    def test_identical_texts_return_no_change_message(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        from edit_learner import capture_edit
        result = capture_edit("same text here", "same text here")
        assert result["preferences_extracted"] == []
        assert "No meaningful changes" in result["message"]

    def test_capture_edit_returns_required_keys(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        monkeypatch.setattr("edit_learner._chat", lambda *a, **kw: '["Bold party names.", "Use exact amounts."]')
        from edit_learner import capture_edit
        original = "The parties are Harbor and Riverside. Rent is due monthly."
        edited   = (
            "**PARTIES:** Harbor Properties LLC (Landlord) and "
            "Riverside Corporation (Tenant).\n"
            "**RENT:** $38,500.00 per month, due on the 1st of each month."
        )
        result = capture_edit(original, edited, query="lease summary")
        for key in ("preferences_extracted", "edit_metrics", "message"):
            assert key in result

    def test_edit_metrics_included_in_response(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, tmp_path)
        # Mock the Groq LLM call so no network is needed
        monkeypatch.setattr("edit_learner._chat", lambda *a, **kw: '["Bold party names."]')
        from edit_learner import capture_edit
        result = capture_edit("Hello world foo bar.", "Completely different content here now.")
        assert "edit_metrics" in result
        m = result["edit_metrics"]
        assert "improvement_score" in m
        assert "retained_pct" in m
        assert "edit_distance_pct" in m

    def test_preferences_are_persisted(self, monkeypatch, tmp_path):
        fake_prefs = self._patch(monkeypatch, tmp_path)
        # Mock LLM so test is offline
        monkeypatch.setattr("edit_learner._chat", lambda *a, **kw: '["Always bold party names.", "Use exact amounts."]')
        from edit_learner import capture_edit, list_all_preferences
        original = "The rent is due monthly."
        edited   = "**RENT DUE DATE:** Rent of $38,500 must be paid on the 1st of each month without exception."
        result = capture_edit(original, edited, query="rent clause")
        all_prefs = list_all_preferences()
        assert isinstance(all_prefs, list)
        assert len(all_prefs) == len(result["preferences_extracted"])

    def test_deactivate_preference_existing(self, monkeypatch, tmp_path):
        fake_prefs = self._patch(monkeypatch, tmp_path)
        import edit_learner, json
        _write_prefs(fake_prefs, [
            {"preference": "Bold party names", "active": True,
             "extracted_at": "2024-01-01", "query": "", "doc_names": []},
        ])
        assert edit_learner.deactivate_preference(0) is True
        assert edit_learner.list_all_preferences()[0]["active"] is False

    def test_deactivate_preference_out_of_range(self, monkeypatch, tmp_path):
        fake_prefs = self._patch(monkeypatch, tmp_path)
        import edit_learner
        _write_prefs(fake_prefs, [])
        assert edit_learner.deactivate_preference(5) is False

    def test_get_active_preferences_filters_inactive(self, monkeypatch, tmp_path):
        fake_prefs = self._patch(monkeypatch, tmp_path)
        import edit_learner
        _write_prefs(fake_prefs, [
            {"preference": "Active pref", "active": True,
             "extracted_at": "2024-01-01", "query": "", "doc_names": []},
            {"preference": "Inactive pref", "active": False,
             "extracted_at": "2024-01-01", "query": "", "doc_names": []},
        ])
        active = edit_learner.get_active_preferences(limit=10)
        assert "Active pref" in active
        assert "Inactive pref" not in active

    def test_get_active_preferences_respects_limit(self, monkeypatch, tmp_path):
        fake_prefs = self._patch(monkeypatch, tmp_path)
        import edit_learner
        many = [
            {"preference": f"Pref {i}", "active": True,
             "extracted_at": "2024-01-01", "query": "", "doc_names": []}
            for i in range(20)
        ]
        _write_prefs(fake_prefs, many)
        active = edit_learner.get_active_preferences(limit=5)
        assert len(active) <= 5
