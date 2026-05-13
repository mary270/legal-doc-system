"""
Pearson Specter Litt — Legal Document AI
Professional Streamlit UI. No emojis. Enterprise-grade design.
Run: streamlit run src/app.py
"""
from __future__ import annotations

import os
import sys
import time
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import streamlit as st

st.set_page_config(
    page_title="PSL Legal AI — Document Intelligence",
    page_icon="assets/favicon.png" if Path("assets/favicon.png").exists() else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, sans-serif;
    background: #080b10;
    color: #d4d8e0;
    font-size: 14px;
    line-height: 1.6;
}
.stApp { background: #080b10; }
.block-container { padding: 0 2.5rem 3rem 2.5rem !important; max-width: 1400px !important; }
#MainMenu, footer, header, [data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0c1018 !important;
    border-right: 1px solid #1c2230 !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] .block-container { padding: 0 1.2rem 2rem 1.2rem !important; }
[data-testid="stSidebar"] * { color: #a8b0bf !important; }

/* ── Topbar wordmark ── */
.wordmark {
    padding: 1.6rem 0 1.4rem 0;
    border-bottom: 1px solid #1c2230;
    margin-bottom: 1.4rem;
}
.wordmark-firm {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.05rem;
    color: #c8a84b !important;
    letter-spacing: 0.04em;
    line-height: 1.2;
}
.wordmark-sub {
    font-size: 0.68rem;
    color: #4a5568 !important;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* ── Sidebar section labels ── */
.sidebar-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #4a5568 !important;
    margin: 1.2rem 0 0.6rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1c2230;
}

/* ── Stat pills ── */
.stat-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.stat-pill {
    flex: 1;
    background: #111620;
    border: 1px solid #1c2230;
    border-radius: 6px;
    padding: 0.6rem 0.5rem;
    text-align: center;
}
.stat-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 500;
    color: #c8a84b !important;
    line-height: 1;
}
.stat-lbl {
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a5568 !important;
    margin-top: 0.25rem;
}

/* ── Document list items ── */
.doc-item {
    background: #111620;
    border: 1px solid #1c2230;
    border-radius: 6px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.4rem;
    transition: border-color 0.15s;
}
.doc-item:hover { border-color: #c8a84b; }
.doc-name {
    font-size: 0.8rem;
    font-weight: 500;
    color: #d4d8e0 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.doc-meta { font-size: 0.68rem; color: #4a5568 !important; margin-top: 0.2rem; }

/* ── Type badges ── */
.badge {
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    margin-right: 0.3rem;
}
.b-contract { background: rgba(59,130,246,0.12); color: #60a5fa !important; border: 1px solid rgba(59,130,246,0.25); }
.b-notice   { background: rgba(239,68,68,0.1);  color: #f87171 !important; border: 1px solid rgba(239,68,68,0.2); }
.b-memo     { background: rgba(34,197,94,0.1);  color: #4ade80 !important; border: 1px solid rgba(34,197,94,0.2); }
.b-deed     { background: rgba(200,168,75,0.12); color: #c8a84b !important; border: 1px solid rgba(200,168,75,0.25); }
.b-other    { background: rgba(100,116,139,0.12);color: #94a3b8 !important; border: 1px solid rgba(100,116,139,0.25); }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #111620 !important;
    border: 1.5px dashed #1c2230 !important;
    border-radius: 8px !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #c8a84b !important; }
[data-testid="stFileUploader"] * { color: #6b7380 !important; font-size: 0.8rem !important; }

/* ── Page header ── */
.page-header {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #1c2230;
    margin-bottom: 1.8rem;
}
.page-title {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 2rem;
    color: #e8e8e8;
    font-weight: 400;
    letter-spacing: -0.01em;
    line-height: 1.2;
    margin: 0;
}
.page-title span { color: #c8a84b; }
.page-desc {
    font-size: 0.82rem;
    color: #64748b;
    margin: 0.5rem 0 0 0;
    letter-spacing: 0.02em;
}

/* ── Pipeline breadcrumb ── */
.pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 1.6rem;
    background: #0c1018;
    border: 1px solid #1c2230;
    border-radius: 6px;
    overflow: hidden;
    width: fit-content;
}
.pipe-step {
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.45rem 1rem;
    color: #4a5568;
    border-right: 1px solid #1c2230;
    white-space: nowrap;
}
.pipe-step.done   { color: #4ade80; }
.pipe-step.active { color: #c8a84b; background: rgba(200,168,75,0.07); }
.pipe-step:last-child { border-right: none; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1c2230 !important;
    border-radius: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.4rem !important;
    margin-right: 0.2rem !important;
    transition: all 0.15s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #d4d8e0 !important; }
.stTabs [aria-selected="true"] {
    color: #c8a84b !important;
    border-bottom: 2px solid #c8a84b !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 1.5rem 0 0 0 !important; }

/* ── Primary button ── */
.stButton > button {
    background: #c8a84b !important;
    color: #0a0a0a !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 5px !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.15s !important;
    width: 100% !important;
    text-shadow: none !important;
    -webkit-font-smoothing: antialiased !important;
}
.stButton > button:hover {
    background: #dfc06a !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(200,168,75,0.3) !important;
    color: #0a0a0a !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button[disabled] {
    background: #1c2230 !important;
    color: #4a5568 !important;
    transform: none !important;
    box-shadow: none !important;
}
/* Sidebar button — slightly lighter gold so text pops on dark sidebar */
[data-testid="stSidebar"] .stButton > button {
    background: #d4b05a !important;
    color: #080808 !important;
    font-weight: 800 !important;
    border: 1.5px solid #e8c878 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #e2c46e !important;
    color: #080808 !important;
}

/* ── Hide the progress bar text label (looks messy) ── */
.stProgress p, [data-testid="stProgressBarMessage"] { display: none !important; }

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    color: #c8a84b !important;
    border: 1px solid #c8a84b !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.45rem 1.2rem !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(200,168,75,0.08) !important;
}

/* ── Text inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #0c1018 !important;
    border: 1px solid #1c2230 !important;
    border-radius: 6px !important;
    color: #d4d8e0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    transition: border-color 0.15s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #c8a84b !important;
    box-shadow: 0 0 0 2px rgba(200,168,75,0.1) !important;
    outline: none !important;
}
label[data-testid="stWidgetLabel"] > div > p { color: #64748b !important; font-size: 0.72rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }

/* ── Slider ── */
[data-testid="stSlider"] > div > div > div > div { background: #c8a84b !important; }

/* ── Draft panel ── */
.draft-panel {
    background: #0c1018;
    border: 1px solid #1c2230;
    border-radius: 8px;
    padding: 1.8rem 2rem;
    font-size: 0.87rem;
    line-height: 1.75;
    min-height: 400px;
}
.draft-panel h2 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    color: #e8e8e8;
    font-weight: 400;
    border-bottom: 1px solid #1c2230;
    padding-bottom: 0.6rem;
    margin: 1.2rem 0 0.8rem 0;
}
.draft-panel h3 {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #c8a84b;
    margin: 1.4rem 0 0.5rem 0;
}
.draft-panel strong { color: #d4d8e0; font-weight: 600; }
.draft-panel em     { color: #64748b; font-style: italic; }
.draft-panel p      { color: #a8b0bf; margin: 0.4rem 0; }
.draft-panel li     { color: #a8b0bf; margin: 0.25rem 0; }
.draft-panel hr     { border-color: #1c2230; margin: 1rem 0; }

/* ── Source cards ── */
.source-panel-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #4a5568;
    margin-bottom: 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1c2230;
}
.source-item {
    background: #0c1018;
    border: 1px solid #1c2230;
    border-left: 2px solid #c8a84b;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    transition: border-left-color 0.15s;
}
.source-item:hover { border-left-color: #4ade80; }
.source-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.35rem;
}
.source-ref {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    color: #c8a84b !important;
}
.source-score-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    background: rgba(74,222,128,0.1);
    color: #4ade80 !important;
    border: 1px solid rgba(74,222,128,0.2);
    border-radius: 3px;
    padding: 0.1rem 0.45rem;
}
.source-filename {
    font-size: 0.7rem;
    color: #4a5568 !important;
    margin-bottom: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
}
.source-excerpt {
    font-size: 0.75rem;
    color: #64748b !important;
    line-height: 1.5;
    font-style: italic;
}
.score-track {
    height: 2px;
    background: #1c2230;
    border-radius: 2px;
    margin: 0.4rem 0 0.5rem 0;
}
.score-fill {
    height: 2px;
    border-radius: 2px;
    background: linear-gradient(90deg, #c8a84b, #4ade80);
}

/* ── Info banner ── */
.info-banner {
    background: #0c1018;
    border: 1px solid #1c2230;
    border-left: 2px solid #c8a84b;
    border-radius: 6px;
    padding: 0.75rem 1.1rem;
    font-size: 0.8rem;
    color: #a8b0bf;
    margin-bottom: 1.2rem;
    line-height: 1.5;
}
.info-banner strong { color: #c8a84b; }

/* ── Metric grid ── */
.metric-grid { display: flex; gap: 0.8rem; margin-bottom: 1.6rem; }
.metric-box {
    flex: 1;
    background: #0c1018;
    border: 1px solid #1c2230;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    transition: border-color 0.15s;
}
.metric-box:hover { border-color: #c8a84b; }
.metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 500;
    color: #c8a84b;
    line-height: 1;
}
.metric-lbl {
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a5568;
    margin-top: 0.35rem;
}

/* ── Preference rows ── */
.pref-row {
    background: #0c1018;
    border: 1px solid #1c2230;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.4rem;
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
}
.pref-indicator {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #4ade80;
    flex-shrink: 0;
    margin-top: 0.45rem;
}
.pref-indicator.inactive { background: #1c2230; }
.pref-body { flex: 1; }
.pref-text { font-size: 0.82rem; color: #d4d8e0; line-height: 1.4; }
.pref-meta { font-size: 0.68rem; color: #4a5568; margin-top: 0.25rem; font-family: 'JetBrains Mono', monospace; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: #0c1018;
    border: 1px solid #1c2230;
    border-radius: 8px;
}
.empty-title { font-size: 0.95rem; font-weight: 600; color: #d4d8e0; margin: 1rem 0 0.4rem 0; }
.empty-desc  { font-size: 0.8rem; color: #4a5568; }
.empty-icon  { font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase; color: #4a5568; font-family: 'JetBrains Mono', monospace; }

/* ── Edit layout ── */
.col-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #4a5568;
    margin-bottom: 0.5rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1c2230;
}
.col-label.active { color: #c8a84b; border-color: #c8a84b; }

/* ── Alert overrides ── */
.stSuccess > div { background: rgba(74,222,128,0.07) !important; border: 1px solid rgba(74,222,128,0.2) !important; border-radius: 6px !important; color: #4ade80 !important; }
.stInfo    > div { background: rgba(200,168,75,0.07)  !important; border: 1px solid rgba(200,168,75,0.2)  !important; border-radius: 6px !important; color: #c8a84b !important; }
.stWarning > div { background: rgba(251,191,36,0.07)  !important; border: 1px solid rgba(251,191,36,0.2)  !important; border-radius: 6px !important; }
.stError   > div { background: rgba(239,68,68,0.07)   !important; border: 1px solid rgba(239,68,68,0.2)   !important; border-radius: 6px !important; }

/* ── Progress bar ── */
.stProgress > div > div { background: #c8a84b !important; border-radius: 2px !important; }
.stProgress > div { background: #1c2230 !important; border-radius: 2px !important; height: 3px !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0c1018 !important;
    border: 1px solid #1c2230 !important;
    border-radius: 6px !important;
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
}
.streamlit-expanderContent {
    background: #0c1018 !important;
    border: 1px solid #1c2230 !important;
    border-top: none !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080b10; }
::-webkit-scrollbar-thumb { background: #1c2230; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #c8a84b; }
</style>
""", unsafe_allow_html=True)

# ── Imports ────────────────────────────────────────────────────────────────────
from groq import RateLimitError, BadRequestError

from document_processor import process_document
from retrieval import add_document, search, list_documents, delete_document
from draft_generator import generate_draft
from edit_learner import capture_edit, get_active_preferences, list_all_preferences, deactivate_preference


def _show_rate_limit_error(exc: Exception) -> None:
    """Show a clean, actionable rate-limit message instead of a Python traceback."""
    import re
    msg = str(exc)
    # Try to pull the retry-after time from the error message
    match = re.search(r"try again in ([\d.]+[smh]+)", msg, re.I)
    wait  = match.group(1) if match else "a few minutes"
    st.markdown(f"""
    <div style="background:rgba(239,68,68,0.07); border:1px solid rgba(239,68,68,0.25);
                border-left:3px solid #f87171; border-radius:6px;
                padding:1rem 1.2rem; font-size:0.83rem; color:#d4d8e0; line-height:1.6;">
        <div style="font-weight:700; color:#f87171; margin-bottom:0.4rem;">
            Groq API — Daily Token Limit Reached
        </div>
        The free Groq tier allows 100,000 tokens per day. Your daily quota is used up.<br>
        <strong style="color:#c8a84b;">You have two options:</strong>
        <ul style="margin:0.6rem 0 0.4rem 1rem; color:#a8b0bf;">
            <li><strong>Wait {wait}</strong> — the quota resets automatically, then try again.</li>
            <li><strong>Get a new API key</strong> — create a second free account at
                <a href="https://console.groq.com" target="_blank"
                   style="color:#c8a84b;">console.groq.com</a>,
                copy the new key, and paste it in <code style="color:#4ade80;">.env</code>
                replacing the current one.</li>
        </ul>
        <div style="font-size:0.72rem; color:#4a5568; margin-top:0.5rem; font-family:monospace;">
            {msg[:180]}
        </div>
    </div>
    """, unsafe_allow_html=True)

SUPPORTED_TYPES = ["pdf", "txt", "png", "jpg", "jpeg", "tiff", "tif", "bmp",
                   "docx", "md", "csv", "rtf"]

# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "last_draft": "",
    "last_query": "",
    "last_sources": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Helpers ────────────────────────────────────────────────────────────────────
def badge(doc_type: str) -> str:
    cls = {"contract": "b-contract", "notice": "b-notice",
           "memo": "b-memo", "deed": "b-deed"}.get(doc_type, "b-other")
    return f'<span class="badge {cls}">{doc_type}</span>'

def score_bar(score: float) -> str:
    return f'<div class="score-track"><div class="score-fill" style="width:{score*100:.0f}%"></div></div>'


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Wordmark
    st.markdown("""
    <div class="wordmark">
        <div class="wordmark-firm">Pearson Specter Litt</div>
        <div class="wordmark-sub">Legal Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    docs        = list_documents()
    all_prefs   = list_all_preferences()
    active_prefs = [p for p in all_prefs if p.get("active", True)]

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-pill">
            <div class="stat-num">{len(docs)}</div>
            <div class="stat-lbl">Documents</div>
        </div>
        <div class="stat-pill">
            <div class="stat-num">{len(active_prefs)}</div>
            <div class="stat-lbl">Preferences</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="sidebar-label">Upload Document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "drop_zone",
        type=SUPPORTED_TYPES,
        label_visibility="collapsed",
    )

    if uploaded:
        file_size = f"{uploaded.size / 1024:.1f} KB"
        suffix    = Path(uploaded.name).suffix.upper().lstrip(".")
        st.markdown(f"""
        <div class="doc-item" style="border-color:#c8a84b;">
            <div class="doc-name">{uploaded.name}</div>
            <div class="doc-meta">{suffix} &nbsp;·&nbsp; {file_size}</div>
        </div>""", unsafe_allow_html=True)

        if st.button("Process and Index", use_container_width=True):
            ext = Path(uploaded.name).suffix or ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                shutil.copyfileobj(uploaded, tmp)
                tmp_path = tmp.name
            with st.spinner("Extracting and indexing…"):
                try:
                    result  = process_document(tmp_path)
                    n_added = add_document(
                        doc_id=result["doc_id"],
                        file_name=uploaded.name,
                        chunks=result["chunks"],
                        structured_fields=result["structured_fields"],
                    )
                    fields = result["structured_fields"]
                    st.success(f"Indexed {n_added} chunks from {uploaded.name}")
                    st.markdown(f"""
                    <div class="doc-item">
                        <div style="margin-bottom:0.3rem;">{badge(fields.get('document_type','other'))}</div>
                        <div class="doc-meta">{fields.get('summary','')[:120]}</div>
                    </div>""", unsafe_allow_html=True)
                except RateLimitError as exc:
                    _show_rate_limit_error(exc)
                except Exception as exc:
                    st.error(f"Processing failed: {exc}")
                finally:
                    os.unlink(tmp_path)
            st.rerun()

    # Document library
    st.markdown('<div class="sidebar-label">Document Library</div>', unsafe_allow_html=True)
    if not docs:
        st.markdown('<div class="doc-meta" style="text-align:center;padding:1rem 0;">No documents indexed.</div>', unsafe_allow_html=True)
    else:
        for doc in docs:
            st.markdown(f"""
            <div class="doc-item">
                <div class="doc-name">{doc['file_name']}</div>
                <div style="margin:0.25rem 0;">{badge(doc.get('document_type','other'))}</div>
                <div class="doc-meta">{doc.get('summary','')[:80]}…</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

# Page header
st.markdown("""
<div class="page-header">
    <h1 class="page-title">Document <span>Intelligence</span></h1>
    <p class="page-desc">
        Ingest · Extract · Retrieve · Draft · Improve — grounded in source documents.
    </p>
</div>
""", unsafe_allow_html=True)

# Pipeline tracker
steps_done = sum([
    len(docs) > 0,
    len(docs) > 0,
    bool(st.session_state.last_draft),
    len(active_prefs) > 0,
])
step_defs = [
    ("01", "Ingest"),
    ("02", "Index"),
    ("03", "Draft"),
    ("04", "Learn"),
]
pipe_html = '<div class="pipeline">'
for i, (num, label) in enumerate(step_defs):
    cls = "done" if i < steps_done else ("active" if i == steps_done else "")
    pipe_html += f'<div class="pipe-step {cls}">{num} &nbsp; {label}</div>'
pipe_html += "</div>"
st.markdown(pipe_html, unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["Generate Draft", "Edit and Learn", "Intelligence Hub"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Generate Draft
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not docs:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">— no documents —</div>
            <div class="empty-title">Nothing indexed yet</div>
            <div class="empty-desc">Upload a PDF, Word document, image, or text file using the sidebar.</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Query row
        col_q, col_c = st.columns([3, 1])
        with col_q:
            st.markdown('<div class="col-label">Matter or question</div>', unsafe_allow_html=True)
            query = st.text_area(
                "query",
                placeholder="Describe the matter — e.g. Summarise all key facts, parties, obligations and disputes in this matter.",
                height=100,
                label_visibility="collapsed",
            )
        with col_c:
            st.markdown('<div class="col-label">Evidence passages</div>', unsafe_allow_html=True)
            n_results = st.slider("n", 3, 15, 8, label_visibility="collapsed")
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
            generate_btn = st.button("Run Analysis", disabled=not query, use_container_width=True)

        if generate_btn and query:
            with st.spinner("Retrieving evidence and generating draft — this takes a few seconds…"):
                try:
                    chunks  = search(query, n_results=n_results)
                    learned = get_active_preferences()
                    result  = generate_draft(
                        query=query,
                        retrieved_chunks=chunks,
                        learned_preferences=learned,
                    )
                    st.session_state.last_draft   = result["draft"]
                    st.session_state.last_query   = query
                    st.session_state.last_sources = result["sources"]
                    if learned:
                        st.info(f"{len(learned)} learned preferences applied to this draft.")
                except RateLimitError as e:
                    _show_rate_limit_error(e)
                except BadRequestError as e:
                    _show_rate_limit_error(e)
                except Exception as e:
                    st.error(f"Generation failed: {e}")

        if st.session_state.last_draft:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            col_d, col_s = st.columns([3, 2], gap="large")

            with col_d:
                st.markdown('<div class="col-label">Generated draft</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="draft-panel">{st.session_state.last_draft}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                st.download_button(
                    label="Download as Markdown",
                    data=st.session_state.last_draft,
                    file_name="case_fact_summary.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            with col_s:
                st.markdown('<div class="source-panel-label">Evidence retrieved</div>', unsafe_allow_html=True)
                for src in st.session_state.last_sources:
                    score = src["relevance_score"]
                    st.markdown(f"""
                    <div class="source-item">
                        <div class="source-top">
                            <span class="source-ref">Source {src['source_number']}</span>
                            <span class="source-score-chip">{score:.0%}</span>
                        </div>
                        <div class="source-filename">{src['file_name']}</div>
                        {score_bar(score)}
                        <div class="source-excerpt">"{src['excerpt'][:180]}…"</div>
                    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Edit and Learn
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.last_draft:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">— no draft —</div>
            <div class="empty-title">No draft to review</div>
            <div class="empty-desc">Generate a draft first, then return here to edit it.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-banner">
            <strong>How this works:</strong>
            Edit the draft on the right as you would in practice.
            On submission, the system analyses what changed and extracts
            <strong>generalizable preferences</strong> that are automatically applied to all future drafts —
            not just this document.
        </div>""", unsafe_allow_html=True)

        col_o, col_e = st.columns(2, gap="large")

        with col_o:
            st.markdown('<div class="col-label">Original AI draft — read only</div>', unsafe_allow_html=True)
            st.text_area(
                "orig",
                value=st.session_state.last_draft,
                height=540,
                disabled=True,
                label_visibility="collapsed",
            )

        with col_e:
            st.markdown('<div class="col-label active">Your edited version</div>', unsafe_allow_html=True)
            edited = st.text_area(
                "edited",
                value=st.session_state.last_draft,
                height=540,
                label_visibility="collapsed",
                key="edited_draft_key",
            )

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            submit = st.button("Submit Edits and Train", use_container_width=True)
        with col_b2:
            if st.button("Reset", use_container_width=True):
                st.rerun()

        if submit:
            if edited.strip() == st.session_state.last_draft.strip():
                st.warning("No changes detected.")
            else:
                with st.spinner("Analysing edits…"):
                    doc_names = list({s["file_name"] for s in st.session_state.last_sources})
                    result = capture_edit(
                        original_draft=st.session_state.last_draft,
                        edited_draft=edited,
                        query=st.session_state.last_query,
                        doc_names=doc_names,
                    )
                if result["preferences_extracted"]:
                    st.success(f"{len(result['preferences_extracted'])} preferences extracted and saved.")
                    for pref in result["preferences_extracted"]:
                        st.markdown(f"""
                        <div class="pref-row">
                            <div class="pref-indicator"></div>
                            <div class="pref-body">
                                <div class="pref-text">{pref}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info(result.get("message", "No preferences extracted."))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Intelligence Hub
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    all_prefs    = list_all_preferences()
    active_list  = [p for p in all_prefs if p.get("active", True)]
    inactive_list= [p for p in all_prefs if not p.get("active", True)]

    # Metrics
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-box">
            <div class="metric-val">{len(docs)}</div>
            <div class="metric-lbl">Documents indexed</div>
        </div>
        <div class="metric-box">
            <div class="metric-val">{len(active_list)}</div>
            <div class="metric-lbl">Active preferences</div>
        </div>
        <div class="metric-box">
            <div class="metric-val">{len(all_prefs)}</div>
            <div class="metric-lbl">Total learned</div>
        </div>
        <div class="metric-box">
            <div class="metric-val">{"Yes" if active_list else "No"}</div>
            <div class="metric-lbl">AI personalised</div>
        </div>
    </div>""", unsafe_allow_html=True)

    col_p, col_d = st.columns([3, 2], gap="large")

    # Preferences
    with col_p:
        st.markdown('<div class="source-panel-label">Learned preferences</div>', unsafe_allow_html=True)
        if not all_prefs:
            st.markdown("""
            <div class="empty-state" style="padding:2rem;">
                <div class="empty-icon">— no preferences —</div>
                <div class="empty-title">No preferences learned yet</div>
                <div class="empty-desc">Edit a draft and submit it to begin training.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for i, pref in enumerate(all_prefs):
                is_active = pref.get("active", True)
                date_str  = pref.get("extracted_at", "")[:10]
                query_str = pref.get("query", "")[:55]
                ind_cls   = "" if is_active else " inactive"
                st.markdown(f"""
                <div class="pref-row" style="{'opacity:0.4;' if not is_active else ''}">
                    <div class="pref-indicator{ind_cls}"></div>
                    <div class="pref-body">
                        <div class="pref-text">{pref['preference']}</div>
                        <div class="pref-meta">{date_str} &nbsp;·&nbsp; {query_str}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                if is_active:
                    if st.button(f"Deactivate", key=f"d_{i}", help="Remove from future drafts"):
                        deactivate_preference(i)
                        st.rerun()

            if inactive_list:
                with st.expander(f"Inactive ({len(inactive_list)})"):
                    for p in inactive_list:
                        st.markdown(f"""
                        <div class="pref-row">
                            <div class="pref-indicator inactive"></div>
                            <div class="pref-text" style="color:#4a5568;">{p['preference']}</div>
                        </div>""", unsafe_allow_html=True)

    # Document library
    with col_d:
        st.markdown('<div class="source-panel-label">Indexed documents</div>', unsafe_allow_html=True)
        if not docs:
            st.markdown('<div class="doc-meta" style="color:#4a5568;text-align:center;padding:2rem 0;">No documents indexed.</div>', unsafe_allow_html=True)
        else:
            for doc in docs:
                st.markdown(f"""
                <div class="doc-item">
                    <div class="doc-name">{doc['file_name']}</div>
                    <div style="margin:0.3rem 0;">{badge(doc.get('document_type','other'))}</div>
                    <div class="doc-meta">{doc.get('summary','')[:110]}…</div>
                </div>""", unsafe_allow_html=True)
