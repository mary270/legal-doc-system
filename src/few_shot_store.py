"""
Few-shot example store.

When an operator edits a draft and the improvement score is high (draft was good),
we save the (query, evidence, original_draft, edited_draft) tuple.

On future drafts, we retrieve the most similar stored example and inject it into
the prompt as a "gold standard" few-shot example — so the model sees a real
human-approved output before generating the new one.

This is what separates a real improvement loop from just storing preference strings.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_STORE_FILE = Path(__file__).parent.parent / "data" / "learned_preferences" / "few_shot_examples.json"
_MIN_SCORE_TO_STORE = 55   # only store examples where the AI was already reasonably good


def _load() -> list[dict]:
    _STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _STORE_FILE.exists():
        return []
    try:
        return json.loads(_STORE_FILE.read_text())
    except Exception:
        return []


def _save(examples: list[dict]) -> None:
    _STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STORE_FILE.write_text(json.dumps(examples, indent=2))


def save_example(
    query:          str,
    original_draft: str,
    edited_draft:   str,
    improvement_score: float,
    doc_names:      list[str] | None = None,
) -> bool:
    """
    Save a (query, original, edited) triple as a few-shot example.
    Only saved when improvement_score >= threshold (draft was already good quality).
    Returns True if saved.
    """
    if improvement_score < _MIN_SCORE_TO_STORE:
        log.info("Few-shot: score %.1f below threshold %.1f — not saving", improvement_score, _MIN_SCORE_TO_STORE)
        return False

    examples = _load()
    examples.append({
        "query":             query[:200],
        "original_draft":    original_draft[:3000],
        "edited_draft":      edited_draft[:3000],
        "improvement_score": improvement_score,
        "doc_names":         doc_names or [],
        "saved_at":          datetime.utcnow().isoformat(),
    })
    # Keep only the 20 best examples (by score)
    examples = sorted(examples, key=lambda x: x["improvement_score"], reverse=True)[:20]
    _save(examples)
    log.info("Few-shot example saved — score=%.1f, total=%d", improvement_score, len(examples))
    return True


def get_best_example(query: str, n: int = 1) -> list[dict]:
    """
    Return the n best-scoring few-shot examples.
    Simple keyword overlap used for relevance (no embeddings needed here).
    """
    examples = _load()
    if not examples:
        return []

    query_words = set(query.lower().split())

    def relevance(ex: dict) -> float:
        ex_words = set(ex["query"].lower().split())
        overlap  = len(query_words & ex_words) / max(len(query_words | ex_words), 1)
        # Blend overlap with quality score
        return overlap * 0.5 + (ex["improvement_score"] / 100) * 0.5

    ranked = sorted(examples, key=relevance, reverse=True)
    return ranked[:n]


def list_examples() -> list[dict]:
    return _load()


def delete_example(index: int) -> bool:
    examples = _load()
    if 0 <= index < len(examples):
        examples.pop(index)
        _save(examples)
        return True
    return False
