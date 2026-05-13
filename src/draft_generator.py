"""
Draft generator: produces grounded case fact summaries anchored to retrieved evidence.
Each claim in the output is tied to a specific source chunk.
Uses Groq (LLaMA 3) for generation.
"""
from __future__ import annotations

import os
from typing import Any

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

# Fallback chain: each model has its own daily quota and TPM limit
# gemma2-9b-it has 15k TPM — handles larger prompts than llama-3.1-8b (6k TPM)
_MODELS = [
    ("llama-3.3-70b-versatile", 2048),   # primary — best quality
    ("gemma2-9b-it",            1500),   # fallback 1 — 15k TPM, handles big prompts
    ("llama-3.1-8b-instant",     800),   # fallback 2 — smallest, strict truncation
]


def _truncate_prompt(messages: list, max_chars: int) -> list:
    """Trim the user message content so the total prompt fits within max_chars."""
    result = []
    for m in messages:
        if m["role"] == "user" and len(m["content"]) > max_chars:
            result.append({**m, "content": m["content"][:max_chars] + "\n\n[Evidence truncated to fit model limits]"})
        else:
            result.append(m)
    return result


def _chat(messages: list, system: str, max_tokens: int) -> str:
    """Try each model in fallback order, shrinking the prompt for smaller models."""
    from groq import RateLimitError, BadRequestError

    # Char budgets per model (rough: 1 token ≈ 4 chars)
    char_budgets = {
        "llama-3.3-70b-versatile": 60000,
        "gemma2-9b-it":            20000,
        "llama-3.1-8b-instant":    12000,
    }

    for model, out_tokens in _MODELS:
        budget   = char_budgets.get(model, 16000)
        trimmed  = _truncate_prompt(messages, budget)
        try:
            resp = _client.chat.completions.create(
                model=model,
                max_tokens=min(max_tokens, out_tokens),
                messages=[{"role": "system", "content": system}] + trimmed,
            )
            return resp.choices[0].message.content
        except (RateLimitError, BadRequestError):
            if model == _MODELS[-1][0]:
                raise
            continue
    return ""

_SYSTEM_PROMPT = """You are a senior legal analyst at Pearson Specter Litt preparing internal case fact summaries.

Your summaries must be:
1. GROUNDED — every factual claim must cite the evidence passage that supports it, using [Source N] inline.
2. STRUCTURED — use the section headers provided.
3. HONEST — if a fact is absent from the evidence, write "Not established in provided documents" rather than inferring.
4. CONCISE — write for a busy attorney who needs the facts fast.

Do not invent facts. Do not speculate beyond what the evidence supports."""

_DRAFT_TEMPLATE = """Generate a Case Fact Summary for the query below, using ONLY the evidence passages provided.

QUERY / MATTER:
{query}

EVIDENCE PASSAGES (cite as [Source 1], [Source 2], etc.):
{evidence_block}

{preference_block}

Produce the summary in this structure:

## Case Fact Summary
**Matter:** [one-line description]
**Prepared by:** AI Analyst (First-Pass Draft)
**Documents reviewed:** {doc_names}

---

### 1. Parties Involved
[Who are the parties? Cite sources.]

### 2. Core Facts
[Key facts with inline citations, e.g. "The lease was signed on 12 March 2022 [Source 1]."]

### 3. Key Dates & Deadlines
[Chronological list of important dates found in the documents.]

### 4. Obligations & Terms
[Material obligations, conditions, or terms identified.]

### 5. Open Issues / Gaps
[Facts requested but NOT found in the provided documents.]

### 6. Analyst Notes
[Any ambiguities, OCR quality issues, or caveats about the source material.]

---
*This is an AI-generated first-pass draft. Attorney review required before use.*
"""


def generate_draft(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
    learned_preferences: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate a grounded case fact summary.
    Returns dict with draft text, sources used, and model metadata.
    """
    if not retrieved_chunks:
        return {
            "draft": "# No Evidence Found\n\nNo relevant passages were retrieved for this query. Please upload relevant documents first.",
            "sources": [],
            "evidence_used": 0,
        }

    # Build evidence block with numbered citations
    evidence_lines = []
    source_index = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        meta = chunk.get("metadata", {})
        file_name = meta.get("file_name", "Unknown")
        score = chunk.get("relevance_score", 0)
        evidence_lines.append(
            f"[Source {i}] (from: {file_name}, relevance: {score:.2f})\n{chunk['text']}"
        )
        source_index.append({
            "source_number": i,
            "file_name": file_name,
            "relevance_score": score,
            "excerpt": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
        })

    evidence_block = "\n\n---\n\n".join(evidence_lines)

    # Unique document names
    doc_names = ", ".join(
        sorted({c.get("metadata", {}).get("file_name", "Unknown") for c in retrieved_chunks})
    )

    # Learned preferences block
    if learned_preferences:
        pref_text = "OPERATOR STYLE PREFERENCES (learned from prior edits — apply these):\n"
        pref_text += "\n".join(f"- {p}" for p in learned_preferences)
        preference_block = pref_text
    else:
        preference_block = ""

    prompt = _DRAFT_TEMPLATE.format(
        query=query,
        evidence_block=evidence_block,
        doc_names=doc_names,
        preference_block=preference_block,
    )

    draft_text = _chat(
        messages=[{"role": "user", "content": prompt}],
        system=_SYSTEM_PROMPT,
        max_tokens=2048,
    )

    return {
        "draft": draft_text,
        "sources": source_index,
        "evidence_used": len(retrieved_chunks),
        "model": "groq/llama-3",
        "preferences_applied": len(learned_preferences) if learned_preferences else 0,
    }
