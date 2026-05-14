"""
Improvement metrics — quantifies how much each operator edit improved the draft.
Answers the key reviewer question: "Did future outputs improve meaningfully?"

Tracks:
  - edit_distance_pct   : % of draft characters changed (lower = AI needed fewer corrections)
  - retained_pct        : % of AI draft content kept by operator (higher = AI was more accurate)
  - additions_pct       : % of final draft that was new content added by operator
  - improvement_score   : composite 0-100 score (higher = draft was closer to what operator wanted)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

try:
    from config import METRICS_FILE
except ImportError:
    METRICS_FILE = Path(__file__).parent.parent / "data" / "learned_preferences" / "metrics_history.json"


# ── Core text similarity helpers ───────────────────────────────────────────────

def _levenshtein_distance(a: str, b: str) -> int:
    """Character-level edit distance (optimised for memory with two-row DP)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Work on shorter strings to save memory; cap at 5000 chars for speed
    a, b = a[:5000], b[:5000]
    prev = list(range(len(b) + 1))
    for ch_a in a:
        curr = [prev[0] + 1]
        for j, ch_b in enumerate(b):
            curr.append(min(prev[j] + (0 if ch_a == ch_b else 1),
                            curr[-1] + 1,
                            prev[j + 1] + 1))
        prev = curr
    return prev[-1]


def _token_overlap(a: str, b: str) -> float:
    """Jaccard similarity on word tokens — fast proxy for retained content."""
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)


def _ngram_overlap(a: str, b: str, n: int = 3) -> float:
    """N-gram precision: fraction of AI n-grams that survived into the edited draft."""
    def ngrams(text: str) -> set[str]:
        words = text.lower().split()
        return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}

    ai_grams  = ngrams(a)
    ed_grams  = ngrams(b)
    if not ai_grams:
        return 1.0
    return len(ai_grams & ed_grams) / len(ai_grams)


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_edit_metrics(original: str, edited: str) -> dict[str, Any]:
    """
    Compute all edit quality metrics between the AI draft and the operator's version.

    Returns a dict with:
      edit_distance_pct   float  0-1   (lower = less correction needed)
      retained_pct        float  0-1   (higher = more AI content kept)
      additions_pct       float  0-1   (how much new content operator added)
      improvement_score   float  0-100 (composite; higher = draft was already good)
      changed             bool         (were there meaningful changes at all?)
    """
    orig_len = max(len(original), 1)
    edit_len = max(len(edited), 1)

    # Raw edit distance (capped for speed)
    dist = _levenshtein_distance(original, edited)
    edit_distance_pct = round(min(dist / orig_len, 1.0), 4)

    # Retained content — n-gram overlap
    retained_pct = round(_ngram_overlap(original, edited, n=3), 4)

    # Additions — words in edited not in original
    orig_words = set(original.lower().split())
    edit_words = set(edited.lower().split())
    new_words  = edit_words - orig_words
    additions_pct = round(len(new_words) / max(len(edit_words), 1), 4)

    # Composite improvement score (0-100)
    # High retained + low edit distance = draft was already good
    improvement_score = round(
        (retained_pct * 60) +                           # 60% weight on retention
        ((1 - min(edit_distance_pct, 1)) * 40),         # 40% weight on low edit distance
        1
    )

    changed = edit_distance_pct > 0.03  # ignore tiny typo fixes

    return {
        "edit_distance_pct": edit_distance_pct,
        "retained_pct":      retained_pct,
        "additions_pct":     additions_pct,
        "improvement_score": improvement_score,
        "changed":           changed,
    }


def save_metrics(metrics: dict[str, Any], query: str = "") -> None:
    """Append a metrics snapshot to the history file."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = _load_history()
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "query":     query[:100],
        **metrics,
    })
    METRICS_FILE.write_text(json.dumps(history, indent=2))
    log.info("Metrics saved — improvement_score=%.1f retained=%.0f%%",
             metrics.get("improvement_score", 0),
             metrics.get("retained_pct", 0) * 100)


def load_metrics_history() -> list[dict[str, Any]]:
    return _load_history()


def _load_history() -> list[dict[str, Any]]:
    if not METRICS_FILE.exists():
        return []
    try:
        return json.loads(METRICS_FILE.read_text())
    except Exception:
        return []


def summarise_improvement(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate metrics across all edits to show trend."""
    if not history:
        return {}

    scores    = [h["improvement_score"] for h in history if "improvement_score" in h]
    retained  = [h["retained_pct"]      for h in history if "retained_pct"      in h]
    edits     = [h["edit_distance_pct"] for h in history if "edit_distance_pct" in h]

    def avg(lst: list) -> float:
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    # Compare first half vs second half to show trend
    mid = max(len(scores) // 2, 1)
    early_score = avg(scores[:mid])
    late_score  = avg(scores[mid:]) if len(scores) > 1 else early_score
    trend = round(late_score - early_score, 1)

    return {
        "total_edits":          len(history),
        "avg_improvement_score": avg(scores),
        "avg_retained_pct":      avg(retained),
        "avg_edit_distance_pct": avg(edits),
        "score_trend":           trend,          # positive = improving over time
        "early_avg_score":       early_score,
        "late_avg_score":        late_score,
    }
