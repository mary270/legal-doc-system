"""
Operator preference profile.

Aggregates all learned preferences and edit history into a structured profile
that answers: "What does this operator consistently want in their drafts?"

Used to:
1. Show the operator a summary of what the system has learned about them
2. Generate a personalised system prompt section for draft generation
3. Track which preference categories are most frequently edited
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from groq import Groq

log = logging.getLogger(__name__)

try:
    from config import GROQ_API_KEY, LLM_MODELS
except ImportError:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    LLM_MODELS   = [{"name": "llama-3.3-70b-versatile", "char_budget": 60000, "max_out": 1024}]

_client       = Groq(api_key=GROQ_API_KEY)
_PROFILE_FILE = Path(__file__).parent.parent / "data" / "learned_preferences" / "operator_profile.json"

_PROFILE_PROMPT = """You are analysing a set of preferences extracted from an operator's edits to AI-generated legal drafts.

Preferences:
{preferences}

Produce a structured operator profile as a JSON object with:
{{
  "writing_style": "one sentence describing preferred tone/formality",
  "structure_preferences": ["list of structural habits"],
  "content_priorities": ["what they always include"],
  "common_additions": ["what they regularly add that AI misses"],
  "avoid": ["things they consistently remove"],
  "summary": "2-sentence plain English description of this operator's style"
}}

Return valid JSON only.
"""


def _chat(prompt: str) -> str:
    from groq import RateLimitError, BadRequestError
    for m in LLM_MODELS:
        try:
            resp = _client.chat.completions.create(
                model=m["name"], max_tokens=800,
                messages=[
                    {"role": "system", "content": "Legal AI analyst. Return valid JSON only."},
                    {"role": "user",   "content": prompt[:m["char_budget"]]},
                ],
            )
            return resp.choices[0].message.content.strip()
        except (RateLimitError, BadRequestError):
            if m == LLM_MODELS[-1]:
                raise
    return "{}"


def build_profile(preferences: list[dict]) -> dict[str, Any]:
    """
    Generate an operator profile from stored preferences.
    Saves and returns the profile.
    """
    active = [p["preference"] for p in preferences if p.get("active", True)]
    if not active:
        return {}

    pref_text = "\n".join(f"- {p}" for p in active)
    raw = _chat(_PROFILE_PROMPT.format(preferences=pref_text))
    raw = re.sub(r"^```json?\s*", "", raw)
    raw = re.sub(r"\s*```$",      "", raw)

    try:
        profile = json.loads(raw)
    except Exception:
        profile = {"summary": "Could not parse profile.", "raw": raw}

    _PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PROFILE_FILE.write_text(json.dumps(profile, indent=2))
    log.info("Operator profile built from %d preferences", len(active))
    return profile


def load_profile() -> dict[str, Any]:
    if not _PROFILE_FILE.exists():
        return {}
    try:
        return json.loads(_PROFILE_FILE.read_text())
    except Exception:
        return {}


def profile_to_prompt_section(profile: dict) -> str:
    """Convert profile into a prompt instruction block for draft generation."""
    if not profile:
        return ""
    lines = ["OPERATOR PROFILE (apply these characteristics to this draft):"]
    if profile.get("writing_style"):
        lines.append(f"- Style: {profile['writing_style']}")
    for item in profile.get("structure_preferences", [])[:3]:
        lines.append(f"- Structure: {item}")
    for item in profile.get("content_priorities", [])[:3]:
        lines.append(f"- Always include: {item}")
    for item in profile.get("avoid", [])[:2]:
        lines.append(f"- Avoid: {item}")
    return "\n".join(lines)
