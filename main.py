#!/usr/bin/env python3
"""
Main entry point — run the full end-to-end pipeline demo.
Demonstrates: document processing, retrieval, draft generation, edit learning.

Usage:
    python main.py demo          # Run full pipeline on sample documents
    python main.py api           # Start FastAPI server
    python main.py ui            # Start Streamlit UI
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def run_demo():
    from document_processor import process_document
    from retrieval import add_document, search
    from draft_generator import generate_draft
    from edit_learner import capture_edit, get_active_preferences

    SAMPLE_DIR = Path(__file__).parent / "data" / "sample_documents"
    OUTPUT_DIR = Path(__file__).parent / "data" / "sample_outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print("LEGAL DOCUMENT AI SYSTEM — END-TO-END DEMO")
    print("=" * 70)

    # ── Step 1: Process documents ──────────────────────────────────────────
    print("\n[1/4] DOCUMENT PROCESSING")
    print("-" * 40)

    sample_files = list(SAMPLE_DIR.glob("*.txt")) + list(SAMPLE_DIR.glob("*.pdf"))
    processed_docs = []

    for file_path in sample_files:
        print(f"  Processing: {file_path.name} ...", end=" ", flush=True)
        result = process_document(str(file_path))
        processed_docs.append(result)

        # Index into vector store
        chunks_added = add_document(
            doc_id=result["doc_id"],
            file_name=result["file_name"],
            chunks=result["chunks"],
            structured_fields=result["structured_fields"],
        )
        print(f"OK ({chunks_added} chunks indexed)")
        print(f"     Type: {result['structured_fields'].get('document_type', 'unknown')}")
        print(f"     Summary: {result['structured_fields'].get('summary', '')[:80]}...")

        # Save extraction output
        out_file = OUTPUT_DIR / f"{file_path.stem}_extracted.json"
        with open(out_file, "w") as f:
            json.dump({
                "file_name": result["file_name"],
                "char_count": result["char_count"],
                "chunk_count": result["chunk_count"],
                "structured_fields": result["structured_fields"],
                "text_preview": result["raw_text"][:500],
            }, f, indent=2)

    # ── Step 2: Retrieval ──────────────────────────────────────────────────
    print("\n[2/4] RETRIEVAL TEST")
    print("-" * 40)
    query = "What are the key facts about the lease dispute between Riverside and Harbor?"
    print(f"  Query: {query}")
    chunks = search(query, n_results=5)
    print(f"  Retrieved {len(chunks)} relevant passages:")
    for c in chunks[:3]:
        print(f"    [{c['relevance_score']:.3f}] {c['metadata']['file_name']} — {c['text'][:80]}...")

    # ── Step 3: Draft generation ───────────────────────────────────────────
    print("\n[3/4] DRAFT GENERATION")
    print("-" * 40)
    print("  Generating grounded case fact summary...", end=" ", flush=True)
    all_chunks = search(query, n_results=10)
    draft_result = generate_draft(query=query, retrieved_chunks=all_chunks)
    print("OK")
    print(f"  Draft length: {len(draft_result['draft'])} chars")
    print(f"  Evidence passages used: {draft_result['evidence_used']}")

    draft_output = OUTPUT_DIR / "sample_draft.md"
    with open(draft_output, "w", encoding="utf-8") as f:
        f.write(draft_result["draft"])
        f.write("\n\n---\n## Sources\n")
        for src in draft_result["sources"]:
            f.write(f"\n**[Source {src['source_number']}]** {src['file_name']} (relevance: {src['relevance_score']:.3f})\n")
            f.write(f"> {src['excerpt']}\n")
    print(f"  Draft saved to: {draft_output}")

    # ── Step 4: Edit learning ──────────────────────────────────────────────
    print("\n[4/4] EDIT LEARNING (simulated operator edit)")
    print("-" * 40)

    simulated_edit = draft_result["draft"] + """

---
**RISK FLAGS** *(added by operator)*
- Unauthorized signatory risk: Jonathan K. Harrington may have departed Harbor Properties in early 2023. If he was no longer authorized, the original Lease may have procedural validity issues.
- Notice delivery defect: Harbor's notice cited an incorrect email address for Tenant's COO. Certified mail receipt status should be confirmed.
- Rent dispute: Tenant claims rent was paid via wire transfer. Wire reference numbers must be verified against Harbor's bank records before any default can be treated as established.

*Attorney review required — do not rely on this draft for legal advice.*
"""

    print("  Submitting simulated operator edit...", end=" ", flush=True)
    learn_result = capture_edit(
        original_draft=draft_result["draft"],
        edited_draft=simulated_edit,
        query=query,
        doc_names=[c["metadata"]["file_name"] for c in all_chunks],
    )
    print("OK")
    print(f"  Preferences extracted: {len(learn_result['preferences_extracted'])}")
    for p in learn_result["preferences_extracted"]:
        print(f"    - {p}")

    # Generate improved draft
    if learn_result["preferences_extracted"]:
        print("\n  Generating improved draft with learned preferences...", end=" ", flush=True)
        prefs = get_active_preferences()
        improved = generate_draft(query=query, retrieved_chunks=all_chunks, learned_preferences=prefs)
        print("OK")
        improved_output = OUTPUT_DIR / "improved_draft.md"
        with open(improved_output, "w", encoding="utf-8") as f:
            f.write(f"<!-- Preferences applied: {prefs} -->\n\n")
            f.write(improved["draft"])
        print(f"  Improved draft saved to: {improved_output}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE. Check data/sample_outputs/ for all artifacts.")
    print("=" * 70)


def run_api():
    import uvicorn
    print("Starting FastAPI server at http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    os.chdir(Path(__file__).parent / "src")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


def run_ui():
    import subprocess
    print("Starting Streamlit UI...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(Path(__file__).parent / "src" / "app.py"),
        "--server.port", "8501",
    ])


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if command == "demo":
        run_demo()
    elif command == "api":
        run_api()
    elif command == "ui":
        run_ui()
    else:
        print(f"Unknown command: {command}. Use: demo | api | ui")
        sys.exit(1)
