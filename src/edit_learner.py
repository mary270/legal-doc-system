"""
Edit learner: captures operator edits to AI drafts, extracts reusable style/content
preferences using Groq (LLaMA 3), and stores them so future drafts improve automatically.

This is NOT a diff tool. It extracts semantic patterns — things like tone preferences,
structural choices, and content emphasis — that generalize across different documents.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
_MODEL = "llama-3.3-70b-versatile"

_PREFS_FILE = Path(__file__).parent.parent / "data" / "learned_preferences" / "preferences.json"

_ANALYZE_PROMPT = """You are analyzing how a human legal analyst edited an AI-generated draft.

Your job: identify GENERALIZABLE preferences that should be applied to ALL future drafts.
Focus on patterns that would improve any legal summary, not just this specific document.

ORIGINAL AI DRAFT:
{original}

OPERATOR-EDITED VERSION:
{edited}

Identify up to 5 specific, actionable preferences. Focus on:
- Tone and formality changes (e.g., "use more formal language", "avoid hedging phrases")
- Structural changes (e.g., "lead with parties, not dates", "always include a risk flag section")
- Content emphasis (e.g., "always highlight missing signatures", "include exact dollar amounts")
- Citation style (e.g., "cite page numbers not just document names")
- What the operator added, removed, or substantially rewrote

You MUST return a JSON array. Even small edits reveal preferences.
Look carefully at every addition, deletion, and rewrite.

Example output:
["Use formal legal tone, avoid casual phrasing", "Always include a Risk Flags section", "Highlight wire reference numbers when payment is disputed"]

Return the JSON array directly, no explanation, no markdown fences.
"""


def _load_preferences() -> list[dict[str, Any]]:
    _PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _PREFS_FILE.exists():
        return []
    with open(_PREFS_FILE) as f:
        return json.load(f)


def _save_preferences(prefs: list[dict[str, Any]]) -> None:
    _PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_PREFS_FILE, "w") as f:
        json.dump(prefs, f, indent=2)


def capture_edit(
    original_draft: str,
    edited_draft: str,
    query: str = "",
    doc_names: list[str] | None = None,
) -> dict[str, Any]:
    """
    Analyze what an operator changed in a draft and extract reusable preferences.
    Returns extracted preferences and saves them persistently.
    """
    if original_draft.strip() == edited_draft.strip():
        return {"preferences_extracted": [], "message": "No changes detected."}

    prompt = _ANALYZE_PROMPT.format(
        original=original_draft[:3000],
        edited=edited_draft[:3000],
    )

    response = _client.chat.completions.create(
        model=_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "system",
                "content": "You are a legal AI trainer. Always respond with a valid JSON array only, no markdown.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        new_prefs: list[str] = json.loads(raw)
        if not isinstance(new_prefs, list):
            new_prefs = []
    except Exception:
        new_prefs = []

    # Load existing, append new entries with timestamp
    all_prefs = _load_preferences()
    timestamp = datetime.utcnow().isoformat()

    for pref in new_prefs:
        all_prefs.append({
            "preference": pref,
            "extracted_at": timestamp,
            "query": query,
            "doc_names": doc_names or [],
            "active": True,
        })

    _save_preferences(all_prefs)

    return {
        "preferences_extracted": new_prefs,
        "total_stored": len(all_prefs),
        "message": f"Extracted {len(new_prefs)} preferences from this edit.",
    }


def get_active_preferences(limit: int = 10) -> list[str]:
    """
    Return the most recently learned active preferences to inject into new drafts.
    """
    all_prefs = _load_preferences()
    active = [p for p in all_prefs if p.get("active", True)]
    seen: list[str] = []
    for pref in reversed(active):  # newest first
        text = pref["preference"]
        if not any(text[:30] in s for s in seen):
            seen.append(text)
        if len(seen) >= limit:
            break
    return seen


def list_all_preferences() -> list[dict[str, Any]]:
    return _load_preferences()


def deactivate_preference(index: int) -> bool:
    """Mark a preference as inactive so it won't be used in future drafts."""
    prefs = _load_preferences()
    if 0 <= index < len(prefs):
        prefs[index]["active"] = False
        _save_preferences(prefs)
        return True
    return False
