# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Legal Document AI System                    │
│                      Pearson Specter Litt                       │
└─────────────────────────────────────────────────────────────────┘

                          ┌──────────┐
                          │  Input   │
                          │  Files   │
                          │ PDF/IMG  │
                          │  /TXT    │
                          └────┬─────┘
                               │
                    ┌──────────▼──────────┐
                    │  Document Processor  │
                    │  ─────────────────  │
                    │  pdfplumber (text)   │
                    │  pytesseract (OCR)   │
                    │  Groq (LLaMA 3) (fields)     │
                    │                     │
                    │  Output:            │
                    │  • cleaned text     │
                    │  • structured JSON  │
                    │  • text chunks      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Vector Store      │
                    │  ─────────────────  │
                    │  ChromaDB (local)    │
                    │  MiniLM embeddings   │
                    │  cosine similarity   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
   ┌──────────▼─────┐  ┌───────▼──────┐  ┌─────▼──────────┐
   │    Retrieval    │  │    Draft     │  │  Edit Learner  │
   │  ────────────  │  │  Generator   │  │  ────────────  │
   │  semantic top-K│→ │  ─────────── │  │  Groq (LLaMA 3) judge  │
   │  with scores   │  │  Groq (LLaMA 3) LLM  │  │  extracts      │
   │                │  │  + [Source N]│  │  preferences   │
   │                │  │  citations   │  │  from diffs    │
   └────────────────┘  └───────┬──────┘  └─────┬──────────┘
                               │                │
                    ┌──────────▼──────────┐      │
                    │     Draft Output     │      │
                    │  ─────────────────  │      │
                    │  • structured text  │      │
                    │  • inline citations │      │
                    │  • source index     │      │
                    └──────────┬──────────┘      │
                               │                 │
                    ┌──────────▼──────────┐       │
                    │   Operator Review   │       │
                    │  ─────────────────  │       │
                    │  edits draft        │       │
                    │  submits feedback   │───────┘
                    └─────────────────────┘

                    Learned preferences stored in
                    data/learned_preferences/preferences.json
                    and injected into future prompts
```

---

## Component Breakdown

### 1. Document Processor (`src/document_processor.py`)

**Strategy:** Layered extraction with graceful degradation.

1. **PDF files**: Try `pdfplumber` for digital text. If a page yields < 50 characters, fall back to `pytesseract` OCR on that page's rasterized image.
2. **Image files**: Direct `pytesseract` OCR.
3. **Text files**: Direct read with UTF-8 fallback.
4. **Cleaning**: Remove null bytes, collapse whitespace, fix OCR ligature artifacts.
5. **Structured field extraction**: Single Groq (LLaMA 3) API call with a strict JSON schema prompt. Extracts: document type, parties, dates, subject, obligations, jurisdiction, reference number, summary.
6. **Chunking**: 800-word chunks with 150-word overlap — enough context per chunk without diluting embedding signal.

**Tradeoff:** Groq (LLaMA 3) for field extraction adds latency (~1-2s per doc) but is far more robust than regex over noisy OCR output. For high-volume production use, consider running field extraction async.

---

### 2. Retrieval Layer (`src/retrieval.py`)

**Strategy:** Local ChromaDB with sentence-transformers embeddings, no external embedding API dependency.

- **Model**: `all-MiniLM-L6-v2` — fast, ~80MB, good legal text performance, runs on CPU.
- **Distance metric**: Cosine similarity (suited for semantic search).
- **Persistence**: ChromaDB PersistentClient writes to `data/chroma_db/` — survives restarts.
- **Per-document filtering**: Optional `doc_id_filter` for scoped retrieval when the operator is focused on one matter.
- **Result format**: Each hit includes text, metadata (file name, doc type, summary), and a relevance score (0-1).

**Tradeoff:** Local embeddings vs. OpenAI/Anthropic embeddings. Local is zero-cost and private, but slightly lower quality on legal domain text. In production, consider Voyage AI legal embeddings or Cohere for better precision.

---

### 3. Draft Generator (`src/draft_generator.py`)

**Strategy:** Strict grounding via prompt design. The prompt explicitly forbids inventing facts and requires `[Source N]` inline citations for every factual claim.

- **Draft type chosen**: Case Fact Summary — best balance of usefulness and groundability for legal intake workflows.
- **Structure enforced**: Six fixed sections (Parties, Core Facts, Key Dates, Obligations, Open Issues, Analyst Notes) ensuring consistent output operators can rely on.
- **Unsupported facts**: If a section cannot be filled from evidence, the system writes "Not established in provided documents" — explicit about gaps rather than hallucinating.
- **Preference injection**: Learned preferences prepended as a bulleted instruction block in the prompt. This is few-shot style preference steering.

**Tradeoff:** Fixed structure vs. freeform generation. Fixed structure is more consistent and easier to audit but less flexible. Given the legal context, consistency wins.

---

### 4. Edit Learner (`src/edit_learner.py`)

**Strategy:** Semantic preference extraction, not syntactic diff.

When an operator edits a draft:
1. Both drafts (original + edited) sent to Groq (LLaMA 3).
2. Groq (LLaMA 3) is asked: *"What generalizable style/content preferences do these edits reveal?"*
3. Extracted preferences (e.g., "Always include wire reference numbers when payment is disputed") stored as JSON with timestamp.
4. On next generation, the N most recent active preferences are injected into the prompt.
5. Operators can deactivate preferences they no longer want applied.

**Why this beats a diff:** A diff tells you *what* changed. Groq (LLaMA 3) tells you *why* it matters and how to generalize it. A change like adding "CONFIDENTIAL — ATTORNEY-CLIENT PRIVILEGE" headers reveals a preference for privilege marking that applies to all future drafts, not just this document.

**Tradeoff:** Relies on Groq (LLaMA 3) for preference quality. Occasionally may over-generalize or extract trivial preferences. Mitigation: deactivate endpoint lets operators prune bad preferences. In production, add a human-in-the-loop review step for new preferences.

---

## Data Flow (Happy Path)

```
1. Operator uploads messy PDF
2. pdfplumber extracts text; OCR fills sparse pages
3. Groq (LLaMA 3) extracts structured fields → stored in result dict
4. Text split into chunks → embedded → stored in ChromaDB
5. Operator enters query: "Summarize the lease dispute"
6. ChromaDB returns top-8 relevant chunks with scores
7. Active operator preferences retrieved from preferences.json
8. Groq (LLaMA 3) generates structured draft with [Source N] citations
9. Operator edits the draft in Streamlit UI
10. Edits submitted → Groq (LLaMA 3) extracts N preferences
11. Preferences saved → applied to all future drafts
```

---

## Assumptions and Tradeoffs

| Decision | Rationale |
|----------|-----------|
| Case Fact Summary as draft type | Clearest demonstration of grounding; most generally useful for legal intake |
| Local embeddings (MiniLM) | Zero cost, zero API calls, works offline, private |
| ChromaDB (local) | No infrastructure required; persists across restarts; trivial setup |
| Groq (LLaMA 3) for field extraction | Regex fails on noisy OCR; Groq (LLaMA 3) handles ambiguity gracefully |
| Preference injection vs. fine-tuning | Fine-tuning requires data scale and infrastructure; preference injection works day-one with minimal edits |
| 800-word chunks, 150-word overlap | Balances semantic coherence per chunk vs. coverage; standard for RAG pipelines |
| Strict "not established" language | Legal context demands epistemic honesty over confident-sounding outputs |
| JSON preferences file | Simple, inspectable, portable; no DB required for V1 |

---

## Scaling Path (Production Considerations)

1. **Document processing**: Add async processing queue (Celery/Redis) for concurrent uploads
2. **Embeddings**: Swap MiniLM for domain-specific legal embeddings (Voyage AI, Cohere)
3. **Vector store**: Move from ChromaDB local to Pinecone/Weaviate for multi-user scale
4. **Preference learning**: Add human review gate before preferences go active
5. **Draft quality**: Add a second Groq (LLaMA 3) pass to verify citation accuracy before serving
6. **Auth**: Add per-matter access control (attorneys only see their cases)
7. **Audit trail**: Log every draft generation with its evidence and preferences for compliance
