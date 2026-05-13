# Legal Document AI System
### Pearson Specter Litt — Document Understanding, Grounded Drafting & Improvement from Edits

> AI-powered pipeline that ingests messy legal documents, extracts structured information, retrieves grounded evidence, generates case fact summaries, and improves over time from operator edits.

---

## Quick Start

### 1. Clone and install

```bash
cd legal-doc-system
pip install -r requirements.txt
```

### 2. Set your API key

Get a **free** Groq API key at [console.groq.com](https://console.groq.com)

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

### 3. Run the full demo

```bash
python main.py demo
```

### 4. Launch the Streamlit UI

```bash
python main.py ui
# Opens at http://localhost:8501
```

### 5. Launch the REST API

```bash
python main.py api
# Opens at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 6. Run evaluation

```bash
python evaluate.py
# Outputs data/sample_outputs/evaluation_report.md
```

### 7. Run tests

```bash
pip install pytest
pytest tests/ -v
```

---

## What it does

| Step | What happens |
|------|-------------|
| **Upload** | PDF, image, or text file uploaded |
| **Extract** | `pdfplumber` extracts text; `pytesseract` OCRs scanned pages |
| **Structure** | Claude pulls parties, dates, obligations, summary into JSON |
| **Index** | Text chunked (800 words, 150-word overlap) and embedded into ChromaDB |
| **Retrieve** | Semantic search finds the most relevant passages for a query |
| **Draft** | Claude generates a grounded case fact summary with `[Source N]` citations |
| **Edit** | Operator edits the draft in the UI |
| **Learn** | Claude analyzes what changed → extracts reusable preferences → stored persistently |
| **Improve** | Next draft automatically applies learned preferences |

---

## Project structure

```
legal-doc-system/
├── src/
│   ├── document_processor.py   # OCR + text extraction + field extraction
│   ├── retrieval.py            # ChromaDB vector store + semantic search
│   ├── draft_generator.py      # Grounded draft generation with citations
│   ├── edit_learner.py         # Operator edit analysis + preference storage
│   ├── api.py                  # FastAPI REST API
│   └── app.py                  # Streamlit UI
├── data/
│   ├── sample_documents/       # Sample legal documents (messy/OCR-like)
│   ├── sample_outputs/         # Generated drafts, extractions, eval report
│   ├── learned_preferences/    # Persisted operator preferences (JSON)
│   └── chroma_db/              # Vector store (auto-created)
├── tests/
│   └── test_pipeline.py        # Integration tests
├── main.py                     # Entry point (demo / api / ui)
├── evaluate.py                 # Evaluation script
├── requirements.txt
└── .env.example
```

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `groq` | Groq API (LLaMA 3.3 70B) for field extraction, draft generation, edit analysis |
| `chromadb` | Persistent local vector store |
| `sentence-transformers` | Local embeddings (`all-MiniLM-L6-v2`) |
| `pdfplumber` | PDF text extraction |
| `pytesseract` | OCR for scanned/image pages |
| `Pillow` | Image handling |
| `fastapi` + `uvicorn` | REST API |
| `streamlit` | Web UI |
| `python-dotenv` | Environment variable loading |

> **Note:** `pytesseract` requires [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on the system. If not installed, the system falls back to pdfplumber-only extraction.

---

## Sample documents included

| File | Type | Description |
|------|------|-------------|
| `commercial_lease_riverside.txt` | Contract | OCR-noisy commercial lease with intentional degradation |
| `default_notice_harbor_v_riverside.txt` | Legal notice | Handwritten-style notice with ambiguous dates |
| `tenant_response_memo.txt` | Internal memo | Fax-scanned memo disputing the default |

---

## REST API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload and process a document |
| `GET` | `/documents` | List all indexed documents |
| `DELETE` | `/documents/{doc_id}` | Remove a document |
| `POST` | `/drafts/generate` | Generate a grounded draft |
| `POST` | `/drafts/feedback` | Submit operator edits to improve future drafts |
| `GET` | `/preferences` | List all learned preferences |
| `POST` | `/preferences/deactivate` | Deactivate a specific preference |
| `GET` | `/health` | Health check |

---

## Assumptions and tradeoffs

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture overview and tradeoff discussion.
