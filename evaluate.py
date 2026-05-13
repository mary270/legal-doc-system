#!/usr/bin/env python3
"""
Evaluation script — measures system performance against the rubric.
Run with: python evaluate.py

Outputs an evaluation report to data/sample_outputs/evaluation_report.md
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
_MODEL = "llama-3.3-70b-versatile"


def score_grounding(draft: str, source_texts: list[str]) -> dict:
    """Use Claude as a judge to evaluate grounding quality."""
    sources_block = "\n\n---\n".join(source_texts[:5])
    prompt = f"""You are evaluating an AI-generated legal draft for grounding quality.

SOURCE DOCUMENTS:
{sources_block[:3000]}

GENERATED DRAFT:
{draft[:2000]}

Rate the following on a scale of 1-10:
1. Grounding score: Are factual claims supported by the source documents?
2. Citation quality: Are inline citations present and accurate?
3. Hallucination risk: Does the draft invent facts not in the sources? (10 = no hallucination)
4. Completeness: Does the draft surface the key facts from the sources?

Return JSON only:
{{"grounding": N, "citations": N, "hallucination_control": N, "completeness": N, "overall_comment": "one sentence"}}
"""
    resp = _client.chat.completions.create(
        model=_MODEL,
        max_tokens=300,
        messages=[
            {"role": "system", "content": "You are an evaluation judge. Respond with valid JSON only, no markdown fences."},
            {"role": "user", "content": prompt},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    import re
    raw = re.sub(r"^```json?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def run_evaluation():
    from document_processor import process_document
    from retrieval import add_document, search
    from draft_generator import generate_draft
    from edit_learner import capture_edit, get_active_preferences

    OUTPUT_DIR = Path(__file__).parent / "data" / "sample_outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)
    SAMPLE_DIR = Path(__file__).parent / "data" / "sample_documents"

    report_lines = [
        "# Legal Document AI System — Evaluation Report",
        f"\nGenerated: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "\n---\n",
    ]

    scores = {}

    # ── 1. Document Processing ─────────────────────────────────────────────
    report_lines.append("## 1. Document Processing\n")
    sample_files = list(SAMPLE_DIR.glob("*.txt"))
    processed = []
    start = time.time()
    for f in sample_files:
        result = process_document(str(f))
        processed.append(result)
        add_document(result["doc_id"], result["file_name"], result["chunks"], result["structured_fields"])
        report_lines.append(f"### {result['file_name']}")
        report_lines.append(f"- Characters extracted: {result['char_count']}")
        report_lines.append(f"- Chunks created: {result['chunk_count']}")
        report_lines.append(f"- Document type detected: `{result['structured_fields'].get('document_type', 'unknown')}`")
        report_lines.append(f"- Parties: {result['structured_fields'].get('parties', [])}")
        report_lines.append(f"- Summary: {result['structured_fields'].get('summary', 'N/A')}")
        report_lines.append("")

    elapsed = time.time() - start
    report_lines.append(f"**Processing time:** {elapsed:.1f}s for {len(sample_files)} documents")
    scores["document_processing"] = {
        "files_processed": len(sample_files),
        "avg_chunks_per_doc": sum(r["chunk_count"] for r in processed) / max(len(processed), 1),
        "all_have_summaries": all(r["structured_fields"].get("summary") for r in processed),
    }
    report_lines.append(f"\n**Score indicators:** {json.dumps(scores['document_processing'], indent=2)}\n")

    # ── 2. Retrieval Quality ───────────────────────────────────────────────
    report_lines.append("\n## 2. Retrieval and Grounding\n")
    test_queries = [
        ("Rent amount and payment terms", ["$38,500", "monthly", "rent"]),
        ("Default allegations and cure periods", ["default", "cure", "30 days"]),
        ("Dispute over unauthorized sublease", ["sublease", "Greenfield", "consent"]),
        ("Tenant's dispute of rent default", ["wire transfer", "bank", "WR-"]),
    ]

    retrieval_scores = []
    for query, expected_keywords in test_queries:
        results = search(query, n_results=5)
        combined = " ".join(r["text"] for r in results).lower()
        hits = sum(1 for kw in expected_keywords if kw.lower() in combined)
        precision = hits / len(expected_keywords)
        retrieval_scores.append(precision)
        report_lines.append(f"- **Query:** {query}")
        top_score = results[0]['relevance_score'] if results else 0
        report_lines.append(f"  - Top result relevance: {top_score:.3f}")
        report_lines.append(f"  - Keyword precision: {precision:.0%} ({hits}/{len(expected_keywords)} keywords found)")
        report_lines.append("")

    avg_retrieval = sum(retrieval_scores) / len(retrieval_scores)
    report_lines.append(f"**Average keyword precision:** {avg_retrieval:.0%}")
    scores["retrieval"] = {"avg_keyword_precision": avg_retrieval}

    # ── 3. Draft Quality ───────────────────────────────────────────────────
    report_lines.append("\n## 3. Draft Generation Quality\n")
    query = "Summarize the key facts, parties, obligations, and disputes in the Harbor v. Riverside lease matter."
    chunks = search(query, n_results=10)
    draft_result = generate_draft(query=query, retrieved_chunks=chunks)

    source_texts = [c["text"] for c in chunks]
    grounding = score_grounding(draft_result["draft"], source_texts)
    report_lines.append(f"**Query:** {query}")
    report_lines.append(f"**Draft length:** {len(draft_result['draft'])} characters")
    report_lines.append(f"**Evidence used:** {draft_result['evidence_used']} passages")
    report_lines.append(f"\n**Claude-judged grounding scores:**")
    report_lines.append(f"- Grounding: {grounding.get('grounding', 'N/A')}/10")
    report_lines.append(f"- Citation quality: {grounding.get('citations', 'N/A')}/10")
    report_lines.append(f"- Hallucination control: {grounding.get('hallucination_control', 'N/A')}/10")
    report_lines.append(f"- Completeness: {grounding.get('completeness', 'N/A')}/10")
    report_lines.append(f"- Comment: {grounding.get('overall_comment', '')}")
    scores["draft_quality"] = grounding

    # Save draft
    (OUTPUT_DIR / "eval_draft.md").write_text(draft_result["draft"], encoding="utf-8")
    report_lines.append(f"\nFull draft saved to: `data/sample_outputs/eval_draft.md`")

    # ── 4. Edit Learning ───────────────────────────────────────────────────
    report_lines.append("\n## 4. Improvement from Operator Edits\n")

    simulated_edit = draft_result["draft"] + """

---
**RISK FLAGS** *(operator addition)*
- Signatory authority: Verify Harrington's current authority at Harbor Properties — COO memo suggests he may have departed in early 2023.
- Notice defect: Incorrect email for Chen. Certified mail receipt must be confirmed independently.
- Rent dispute: DO NOT treat rent as unpaid until wire transfer references WR-20230628-447 and WR-20230731-512 are verified with Harbor's bank.
- Always include exact wire reference numbers when payment records are disputed.
"""

    learn1 = capture_edit(
        original_draft=draft_result["draft"],
        edited_draft=simulated_edit,
        query=query,
    )

    # Second edit — style preference
    simulated_edit_2 = draft_result["draft"].replace(
        "## Case Fact Summary",
        "## CASE FACT SUMMARY — CONFIDENTIAL\n**PRIVILEGE: ATTORNEY-CLIENT**"
    ).replace("Not established", "**NOT ESTABLISHED IN RECORD**")

    learn2 = capture_edit(
        original_draft=draft_result["draft"],
        edited_draft=simulated_edit_2,
        query=query,
    )

    report_lines.append(f"**Edit 1 (content additions):** {len(learn1['preferences_extracted'])} preferences extracted")
    for p in learn1['preferences_extracted']:
        report_lines.append(f"  - {p}")
    report_lines.append(f"\n**Edit 2 (style/formatting):** {len(learn2['preferences_extracted'])} preferences extracted")
    for p in learn2['preferences_extracted']:
        report_lines.append(f"  - {p}")

    # Generate improved draft and score it
    prefs = get_active_preferences()
    improved = generate_draft(query=query, retrieved_chunks=chunks, learned_preferences=prefs)
    improved_grounding = score_grounding(improved["draft"], source_texts)

    report_lines.append(f"\n**Improved draft (with {len(prefs)} preferences applied):**")
    report_lines.append(f"- Grounding: {improved_grounding.get('grounding', 'N/A')}/10")
    report_lines.append(f"- Hallucination control: {improved_grounding.get('hallucination_control', 'N/A')}/10")
    report_lines.append(f"- Comment: {improved_grounding.get('overall_comment', '')}")

    (OUTPUT_DIR / "improved_draft.md").write_text(improved["draft"], encoding="utf-8")
    scores["edit_learning"] = {
        "total_preferences_learned": len(prefs),
        "preferences": prefs,
        "original_grounding": grounding.get("grounding"),
        "improved_grounding": improved_grounding.get("grounding"),
    }

    # ── Summary ────────────────────────────────────────────────────────────
    report_lines.append("\n## Summary Scores\n")
    report_lines.append("| Dimension | Result |")
    report_lines.append("|-----------|--------|")
    report_lines.append(f"| Documents processed | {scores['document_processing']['files_processed']} |")
    report_lines.append(f"| Avg retrieval precision | {scores['retrieval']['avg_keyword_precision']:.0%} |")
    report_lines.append(f"| Draft grounding (Claude judge) | {scores['draft_quality'].get('grounding', 'N/A')}/10 |")
    report_lines.append(f"| Hallucination control | {scores['draft_quality'].get('hallucination_control', 'N/A')}/10 |")
    report_lines.append(f"| Preferences learned | {scores['edit_learning']['total_preferences_learned']} |")
    orig_g = scores['edit_learning'].get('original_grounding') or 0
    impr_g = scores['edit_learning'].get('improved_grounding') or 0
    delta = impr_g - orig_g if orig_g and impr_g else "N/A"
    report_lines.append(f"| Grounding improvement | {delta} |")

    report_text = "\n".join(report_lines)
    report_path = OUTPUT_DIR / "evaluation_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"\nEvaluation report saved to: {report_path}")


if __name__ == "__main__":
    run_evaluation()
