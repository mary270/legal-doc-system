"""
Edit learner — captures operator edits, extracts generalizable preferences,
tracks quantitative improvement metrics, and feeds learned signals back into
future draft generation.

Key design: semantic extraction (not syntactic diff).
Claude/LLaMA analyses WHAT changed and WHY, producing reusable rules.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from groq import Groq

from metrics import compute_edit_metrics, save_metrics

try:
    from config import GROQ_API_KEY, LLM_MODELS, PREFS_FILE, MAX_ACTIVE_PREFERENCES
except ImportError:
    GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
    LLM_MODELS             = [
        {"name": "llama-3.3-70b-versatile", "char_budget": 60_000, "max_out": 512},
        {"name": "gemma2-9b-it",            "char_budget": 20_000, "max_out": 512},
        {"name": "llama-3.1-8b-instant",    "char_budget": 12_000, "max_out": 512},
    ]
    PREFS_FILE             = Path(__file__).parent.parent / "data" / "learned_preferences" / "preferences.json"
    MAX_ACTIVE_PREFERENCES = 10

log    = logging.getLogger(__name__)
_client= Groq(api_key=GROQ_API_KEY)

_ANALYZE_PROMPT = """You are analysing how a human legal analyst edited an AI-generated draft.

Identify GENERALIZABLE preferences that should apply to ALL future drafts.
Focus on patterns that transfer across documents, not just this specific case.

ORIGINAL AI DRAFT:
{original}

OPERATOR-EDITED VERSION:
{edited}

Look for:
- Tone / formality changes
- Structural changes (sections added, removed, reordered)
- Content emphasis (what was highlighted or de-emphasised)
- Citation style
- Boilerplate the operator always adds
- Things the operator always removes

You MUST return a JSON array of up to 5 concise preference strings (each under 90 chars).
Example: ["Always include a Risk Flags section", "Use exact dollar amounts not approximations"]
Return [] only if edits are purely cosmetic typo fixes.
Return the JSON array only — no explanation, no markdown.
"""


# ── LLM helper ─────────────────────────────────────────────────────────────────

def _chat(messages: list[dict], max_tokens: int = 512) -> str:
    from groq import RateLimitError, BadRequestError
    for model_cfg in LLM_MODELS:
        budget  = model_cfg["char_budget"]
        trimmed = [
            {**m, "content": m["content"][:budget]}
            if m["role"] == "user" and len(m["content"]) > budget else m
            for m in messages
        ]
        try:
            resp = _client.chat.completions.create(
                model=model_cfg["name"],
                max_tokens=max_tokens,
                messages=trimmed,
            )
            return resp.choices[0].message.content.strip()
        except (RateLimitError, BadRequestError):
            log.warning("Model %s unavailable, trying next…", model_cfg["name"])
            if model_cfg == LLM_MODELS[-1]:
                raise
            continue
    return "[]"


# ── Preferences store ──────────────────────────────────────────────────────────

def _load_preferences() -> list[dict[str, Any]]:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PREFS_FILE.exists():
        return []
    try:
        return json.loads(PREFS_FILE.read_text())
    except Exception:
        return []


def _save_preferences(prefs: list[dict[str, Any]]) -> None:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(prefs, indent=2))


# ── Public API ─────────────────────────────────────────────────────────────────

def capture_edit(
    original_draft: str,
    edited_draft:   str,
    query:          str = "",
    doc_names:      list[str] | None = None,
) -> dict[str, Any]:
    """
    Main entry point called when an operator submits an edited draft.

    1. Computes quantitative edit metrics (edit distance, retained %, score)
    2. Uses LLM to extract generalizable style/content preferences
    3. Persists both metrics and preferences

    Returns dict with metrics + extracted preferences.
    """
    # Step 1 — quantitative metrics
    edit_metrics = compute_edit_metrics(original_draft, edited_draft)
    log.info(
        "Edit captured — improvement_score=%.1f  retained=%.0f%%  edit_dist=%.0f%%",
        edit_metrics["improvement_score"],
        edit_metrics["retained_pct"] * 100,
        edit_metrics["edit_distance_pct"] * 100,
    )

    if not edit_metrics["changed"]:
        return {
            "preferences_extracted": [],
            "edit_metrics":          edit_metrics,
            "message":               "No meaningful changes detected (edit < 3%).",
        }

    # Persist metrics history
    save_metrics({**edit_metrics, "query": query})

    # Step 2 — semantic preference extraction
    prompt = _ANALYZE_PROMPT.format(
        original=original_draft[:3000],
        edited=edited_draft[:3000],
    )
    raw = _chat(
        messages=[
            {"role": "system", "content": "Legal AI trainer. Respond with a JSON array only."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=512,
    )

    raw = re.sub(r"^```json?\s*", "", raw)
    raw = re.sub(r"\s*```$",      "", raw)
    try:
        new_prefs: list[str] = json.loads(raw)
        if not isinstance(new_prefs, list):
            new_prefs = []
    except Exception:
        new_prefs = []

    # Step 3 — persist preferences
    all_prefs  = _load_preferences()
    timestamp  = datetime.utcnow().isoformat()
    for pref in new_prefs:
        all_prefs.append({
            "preference":   pref,
            "extracted_at": timestamp,
            "query":        query[:100],
            "doc_names":    doc_names or [],
            "active":       True,
            "improvement_score_at_capture": edit_metrics["improvement_score"],
        })
    _save_preferences(all_prefs)

    log.info("Extracted %d preferences; total stored: %d", len(new_prefs), len(all_prefs))
    return {
        "preferences_extracted": new_prefs,
        "edit_metrics":          edit_metrics,
        "total_stored":          len(all_prefs),
        "message":               f"Extracted {len(new_prefs)} preferences. "
                                 f"Draft retained {edit_metrics['retained_pct']*100:.0f}% of AI content.",
    }


def get_active_preferences(limit: int = MAX_ACTIVE_PREFERENCES) -> list[str]:
    """Return latest active preferences for injection into the next draft prompt."""
    all_prefs = _load_preferences()
    active    = [p for p in all_prefs if p.get("active", True)]
    seen: list[str] = []
    for pref in reversed(active):
        text = pref["preference"]
        if not any(text[:30] in s for s in seen):
            seen.append(text)
        if len(seen) >= limit:
            break
    return seen


def list_all_preferences() -> list[dict[str, Any]]:
    return _load_preferences()


def deactivate_preference(index: int) -> bool:
    prefs = _load_preferences()
    if 0 <= index < len(prefs):
        prefs[index]["active"] = False
        _save_preferences(prefs)
        log.info("Deactivated preference #%d", index)
        return True
    return False
