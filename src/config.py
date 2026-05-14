"""
Central configuration — all tuneable parameters in one place.
Import this instead of hardcoding values anywhere in the codebase.
"""
from __future__ import annotations
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
DATA_DIR    = ROOT / "data"
CHROMA_DIR  = DATA_DIR / "chroma_db"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "sample_outputs"
PREFS_FILE  = DATA_DIR / "learned_preferences" / "preferences.json"
METRICS_FILE= DATA_DIR / "learned_preferences" / "metrics_history.json"

for _d in [CHROMA_DIR, UPLOADS_DIR, OUTPUTS_DIR, PREFS_FILE.parent]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Groq / LLM ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Fallback chain: try models in order; each has its own daily + TPM quota
LLM_MODELS = [
    {"name": "llama-3.3-70b-versatile", "char_budget": 60_000, "max_out": 2048},
    {"name": "gemma2-9b-it",            "char_budget": 20_000, "max_out": 1500},
    {"name": "llama-3.1-8b-instant",    "char_budget": 12_000, "max_out":  800},
]

# ── Document processing ────────────────────────────────────────────────────────
CHUNK_SIZE    = 800    # words per chunk
CHUNK_OVERLAP = 150    # word overlap between adjacent chunks
OCR_THRESHOLD = 50     # chars — pages with fewer chars get OCR'd
OCR_RESOLUTION= 200    # DPI for page rasterisation

SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".png", ".jpg", ".jpeg",
    ".tiff", ".tif", ".bmp", ".md", ".rtf",
}

# ── Retrieval ──────────────────────────────────────────────────────────────────
COLLECTION_NAME       = "legal_documents"
EMBED_MODEL           = "all-MiniLM-L6-v2"
DEFAULT_N_RESULTS     = 8
HYBRID_SEMANTIC_WEIGHT= 0.65   # weight for semantic score in hybrid search
HYBRID_BM25_WEIGHT    = 0.35   # weight for BM25 keyword score

# ── Edit learning ──────────────────────────────────────────────────────────────
MAX_ACTIVE_PREFERENCES = 10    # how many preferences to inject into a prompt
MIN_EDIT_DISTANCE_PCT  = 0.03  # ignore edits smaller than 3% — likely typo fixes

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
