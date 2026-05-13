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
_MODEL = "llama-3.3-70b-versatile"

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

    response = _client.chat.completions.create(
        model=_MODEL,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    draft_text = response.choices[0].message.content

    return {
        "draft": draft_text,
        "sources": source_index,
        "evidence_used": len(retrieved_chunks),
        "model": _MODEL,
        "preferences_applied": len(learned_preferences) if learned_preferences else 0,
    }
