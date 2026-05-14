"""
Pearson Specter Litt — Legal Document Intelligence
Professional Streamlit UI — high contrast, fully readable, enterprise design.
Run: streamlit run src/app.py
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("app")

import streamlit as st

st.set_page_config(
    page_title="PSL — Legal Document Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;600&display=swap');

/* ─── Base ─── */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}
.stApp { background-color: #0d1117 !important; }
.block-container { padding: 1.5rem 2rem 3rem 2rem !important; max-width: 1440px !important; }
#MainMenu, footer, header { display: none !important; }

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #30363d !important;
}
[data-testid="stSidebar"] .block-container { padding: 1rem !important; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ─── Typography ─── */
h1,h2,h3 { color: #f0f6fc !important; }
p, li     { color: #c9d1d9 !important; }
label, .stMarkdown p { color: #8b949e !important; font-size: 0.78rem !important; }

/* ─── Wordmark ─── */
.wordmark {
    padding: 1.2rem 0 1rem 0;
    border-bottom: 1px solid #30363d;
    margin-bottom: 1.2rem;
}
.wm-firm {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.1rem;
    color: #f0c040 !important;
    letter-spacing: 0.02em;
}
.wm-sub {
    font-size: 0.65rem;
    color: #8b949e !important;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 0.15rem;
}

/* ─── Section label ─── */
.sec-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #8b949e !important;
    margin: 1.2rem 0 0.5rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #30363d;
}

/* ─── Stat pills ─── */
.stat-row { display:flex; gap:0.5rem; margin-bottom:1rem; }
.stat-pill {
    flex:1; background:#1c2128; border:1px solid #30363d;
    border-radius:6px; padding:0.7rem 0.5rem; text-align:center;
}
.stat-num {
    font-family:'JetBrains Mono',monospace;
    font-size:1.5rem; font-weight:700;
    color:#f0c040 !important; line-height:1;
}
.stat-lbl {
    font-size:0.62rem; letter-spacing:0.1em;
    text-transform:uppercase; color:#8b949e !important; margin-top:0.2rem;
}

/* ─── Doc cards ─── */
.doc-card {
    background:#1c2128; border:1px solid #30363d;
    border-radius:6px; padding:0.65rem 0.85rem;
    margin-bottom:0.4rem; transition: border-color 0.15s;
}
.doc-card:hover { border-color:#f0c040; }
.doc-name { font-size:0.8rem; font-weight:600; color:#e6edf3 !important;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.doc-meta { font-size:0.68rem; color:#8b949e !important; margin-top:0.2rem; }

/* ─── Badges ─── */
.badge {
    display:inline-block; font-size:0.6rem; font-weight:700;
    letter-spacing:0.1em; text-transform:uppercase;
    padding:0.12rem 0.45rem; border-radius:3px; margin-right:0.25rem;
}
.b-contract { background:rgba(56,139,253,0.15); color:#79c0ff !important; border:1px solid rgba(56,139,253,0.3); }
.b-notice   { background:rgba(248,81,73,0.15);  color:#ff7b72 !important; border:1px solid rgba(248,81,73,0.3); }
.b-memo     { background:rgba(63,185,80,0.15);  color:#7ee787 !important; border:1px solid rgba(63,185,80,0.3); }
.b-deed     { background:rgba(240,192,64,0.15); color:#f0c040 !important; border:1px solid rgba(240,192,64,0.3); }
.b-other    { background:rgba(139,148,158,0.15);color:#8b949e !important; border:1px solid rgba(139,148,158,0.3); }

/* ─── File uploader ─── */
[data-testid="stFileUploader"] {
    background:#1c2128 !important; border:1.5px dashed #30363d !important;
    border-radius:8px !important;
}
[data-testid="stFileUploader"]:hover { border-color:#f0c040 !important; }
[data-testid="stFileUploader"] * { color:#8b949e !important; font-size:0.8rem !important; }

/* ─── Page header ─── */
.page-hdr {
    padding:1.5rem 0 1.2rem 0;
    border-bottom:1px solid #30363d;
    margin-bottom:1.5rem;
}
.page-title {
    font-family:'DM Serif Display',serif;
    font-size:1.9rem; font-weight:400;
    color:#f0f6fc !important; margin:0;
}
.page-title span { color:#f0c040; }
.page-sub { font-size:0.82rem; color:#8b949e !important; margin:0.4rem 0 0 0; }

/* ─── Pipeline steps ─── */
.pipeline { display:flex; margin-bottom:1.5rem; gap:0; width:fit-content; }
.pipe-step {
    font-size:0.67rem; font-weight:600; letter-spacing:0.1em;
    text-transform:uppercase; padding:0.4rem 1rem;
    background:#161b22; color:#8b949e !important;
    border:1px solid #30363d; border-right:none;
}
.pipe-step:first-child { border-radius:6px 0 0 6px; }
.pipe-step:last-child  { border-radius:0 6px 6px 0; border-right:1px solid #30363d; }
.pipe-step.done   { color:#7ee787 !important; background:rgba(63,185,80,0.08); }
.pipe-step.active { color:#f0c040 !important; background:rgba(240,192,64,0.08); border-color:#f0c040; }

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    background:transparent !important; border-bottom:1px solid #30363d !important;
    gap:0 !important; padding:0 !important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; color:#8b949e !important;
    border:none !important; border-bottom:2px solid transparent !important;
    border-radius:0 !important; font-size:0.78rem !important;
    font-weight:600 !important; letter-spacing:0.06em !important;
    text-transform:uppercase !important; padding:0.65rem 1.3rem !important;
}
.stTabs [data-baseweb="tab"]:hover { color:#c9d1d9 !important; }
.stTabs [aria-selected="true"] {
    color:#f0c040 !important;
    border-bottom:2px solid #f0c040 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding:1.5rem 0 0 0 !important; }

/* ─── Buttons ─── */
.stButton > button {
    background:#1f6feb !important; color:#ffffff !important;
    font-weight:700 !important; font-size:0.78rem !important;
    letter-spacing:0.07em !important; text-transform:uppercase !important;
    border:none !important; border-radius:5px !important;
    padding:0.55rem 1.3rem !important; width:100% !important;
    transition:all 0.15s !important;
    text-shadow:none !important;
    -webkit-font-smoothing:antialiased !important;
}
.stButton > button:hover {
    background:#388bfd !important; color:#ffffff !important;
    box-shadow:0 3px 14px rgba(31,111,235,0.45) !important;
    transform:translateY(-1px) !important;
}
.stButton > button:active {
    background:#1158c7 !important; color:#ffffff !important;
    transform:translateY(0) !important;
}
.stButton > button[disabled] {
    background:#21262d !important; color:#484f58 !important;
    transform:none !important; box-shadow:none !important;
}
[data-testid="stSidebar"] .stButton > button {
    background:#1f6feb !important; color:#ffffff !important;
    font-weight:800 !important;
    box-shadow:0 2px 8px rgba(31,111,235,0.3) !important;
}

/* ─── Download button ─── */
[data-testid="stDownloadButton"] > button {
    background:transparent !important; color:#388bfd !important;
    border:1px solid #388bfd !important; font-size:0.74rem !important;
    font-weight:600 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background:rgba(31,111,235,0.12) !important; color:#ffffff !important;
}

/* ─── Inputs ─── */
.stTextArea textarea, .stTextInput input {
    background:#161b22 !important; border:1px solid #30363d !important;
    color:#e6edf3 !important; border-radius:6px !important;
    font-size:0.85rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color:#f0c040 !important;
    box-shadow:0 0 0 2px rgba(240,192,64,0.15) !important;
}
.stTextArea label, .stTextInput label { color:#8b949e !important; }

/* ─── Slider ─── */
[data-testid="stSlider"] > div > div > div > div { background:#f0c040 !important; }

/* ─── Draft output panel ─── */
.draft-panel {
    background:#161b22; border:1px solid #30363d; border-radius:8px;
    padding:1.6rem 1.8rem; font-size:0.87rem; line-height:1.8;
    min-height:420px; color:#c9d1d9;
}
.draft-panel h2 {
    font-family:'DM Serif Display',serif; font-size:1.15rem;
    color:#f0f6fc !important; font-weight:400;
    border-bottom:1px solid #30363d; padding-bottom:0.5rem;
    margin:1rem 0 0.7rem 0;
}
.draft-panel h3 {
    font-size:0.75rem; font-weight:700; letter-spacing:0.12em;
    text-transform:uppercase; color:#f0c040 !important; margin:1.3rem 0 0.4rem 0;
}
.draft-panel strong { color:#e6edf3 !important; }
.draft-panel em     { color:#8b949e !important; }
.draft-panel p, .draft-panel li { color:#c9d1d9 !important; }
.draft-panel hr     { border-color:#30363d !important; }

/* ─── Source cards ─── */
.src-label {
    font-size:0.65rem; font-weight:700; letter-spacing:0.15em;
    text-transform:uppercase; color:#8b949e !important;
    border-bottom:1px solid #30363d; padding-bottom:0.35rem; margin-bottom:0.75rem;
}
.src-card {
    background:#161b22; border:1px solid #30363d;
    border-left:3px solid #f0c040; border-radius:6px;
    padding:0.8rem 0.95rem; margin-bottom:0.5rem;
}
.src-top  { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem; }
.src-ref  { font-family:'JetBrains Mono',monospace; font-size:0.73rem; font-weight:600; color:#f0c040 !important; }
.src-chip {
    font-family:'JetBrains Mono',monospace; font-size:0.65rem;
    background:rgba(63,185,80,0.12); color:#7ee787 !important;
    border:1px solid rgba(63,185,80,0.25); border-radius:3px; padding:0.08rem 0.4rem;
}
.src-file   { font-size:0.7rem; color:#8b949e !important; margin-bottom:0.3rem; font-family:'JetBrains Mono',monospace; }
.src-bar    { height:2px; background:#21262d; border-radius:2px; margin:0.35rem 0; }
.src-fill   { height:2px; border-radius:2px; background:linear-gradient(90deg,#f0c040,#7ee787); }
.src-excerpt{ font-size:0.75rem; color:#6e7681 !important; font-style:italic; line-height:1.5; }

/* ─── Metric boxes ─── */
.metrics-row { display:flex; gap:0.8rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.metric-box {
    flex:1; min-width:130px; background:#161b22;
    border:1px solid #30363d; border-radius:8px; padding:1rem 1.2rem;
}
.metric-box:hover { border-color:#f0c040; }
.metric-val { font-family:'JetBrains Mono',monospace; font-size:1.9rem; font-weight:700; color:#f0c040; line-height:1; }
.metric-val.green { color:#7ee787; }
.metric-val.red   { color:#ff7b72; }
.metric-lbl { font-size:0.63rem; letter-spacing:0.12em; text-transform:uppercase; color:#8b949e; margin-top:0.3rem; }
.metric-sub { font-size:0.7rem; color:#6e7681; margin-top:0.15rem; }

/* ─── Improvement card ─── */
.imp-card {
    background:#161b22; border:1px solid #30363d; border-radius:8px;
    padding:1.2rem 1.4rem; margin-bottom:0.8rem;
}
.imp-title { font-size:0.78rem; font-weight:700; color:#e6edf3 !important; margin-bottom:0.8rem; }
.imp-row   { display:flex; justify-content:space-between; margin-bottom:0.4rem; }
.imp-key   { font-size:0.75rem; color:#8b949e !important; }
.imp-val   { font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:600; color:#f0c040 !important; }
.imp-bar-track { height:4px; background:#21262d; border-radius:2px; margin:0.25rem 0 0.6rem 0; }
.imp-bar-fill  { height:4px; border-radius:2px; }

/* ─── Preference rows ─── */
.pref-row {
    background:#161b22; border:1px solid #30363d; border-radius:6px;
    padding:0.7rem 1rem; margin-bottom:0.4rem; display:flex; gap:0.8rem;
}
.pref-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; margin-top:0.4rem; }
.pref-dot.active   { background:#7ee787; }
.pref-dot.inactive { background:#30363d; }
.pref-text { font-size:0.82rem; color:#c9d1d9 !important; line-height:1.4; }
.pref-meta { font-size:0.68rem; color:#6e7681 !important; margin-top:0.2rem; font-family:'JetBrains Mono',monospace; }

/* ─── Info banner ─── */
.info-banner {
    background:#1c2128; border:1px solid #30363d; border-left:3px solid #f0c040;
    border-radius:6px; padding:0.75rem 1rem; font-size:0.82rem;
    color:#c9d1d9 !important; margin-bottom:1.2rem; line-height:1.6;
}
.info-banner strong { color:#f0c040 !important; }

/* ─── Empty state ─── */
.empty-state {
    background:#161b22; border:1px solid #30363d; border-radius:8px;
    padding:3.5rem 2rem; text-align:center;
}
.empty-code  { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#484f58 !important; letter-spacing:0.2em; }
.empty-title { font-size:0.95rem; font-weight:600; color:#c9d1d9 !important; margin:0.8rem 0 0.3rem; }
.empty-desc  { font-size:0.8rem; color:#8b949e !important; }

/* ─── Alerts ─── */
.stSuccess > div { background:rgba(63,185,80,0.08)  !important; border:1px solid rgba(63,185,80,0.25)  !important; border-radius:6px !important; color:#7ee787 !important; }
.stInfo    > div { background:rgba(240,192,64,0.08) !important; border:1px solid rgba(240,192,64,0.25) !important; border-radius:6px !important; color:#f0c040 !important; }
.stWarning > div { background:rgba(251,191,36,0.08) !important; border:1px solid rgba(251,191,36,0.25) !important; border-radius:6px !important; }
.stError   > div { background:rgba(248,81,73,0.08)  !important; border:1px solid rgba(248,81,73,0.25)  !important; border-radius:6px !important; }

/* ─── Column label ─── */
.col-label {
    font-size:0.65rem; font-weight:700; letter-spacing:0.15em;
    text-transform:uppercase; color:#8b949e;
    border-bottom:1px solid #30363d; padding-bottom:0.35rem; margin-bottom:0.6rem;
}
.col-label.gold { color:#f0c040; border-color:#f0c040; }

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#0d1117; }
::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#f0c040; }

/* ─── Spinner ─── */
.stSpinner > div { border-top-color:#f0c040 !important; }
</style>
""", unsafe_allow_html=True)

# ── Imports ────────────────────────────────────────────────────────────────────
from groq import RateLimitError, BadRequestError

from document_processor import process_document
from retrieval import add_document, search, list_documents, delete_document
from draft_generator import generate_draft
from edit_learner import capture_edit, get_active_preferences, list_all_preferences, deactivate_preference
from metrics import load_metrics_history, summarise_improvement
from few_shot_store import list_examples, delete_example
from operator_profile import build_profile, load_profile

SUPPORTED = ["pdf","txt","png","jpg","jpeg","tiff","tif","bmp","md","rtf"]

# ── Session state ──────────────────────────────────────────────────────────────
_STATE_DEFAULTS = {
    "last_draft":        "",
    "last_query":        "",
    "last_sources":      [],
    "last_metrics":      {},
    "selected_doc_id":   None,   # doc_id currently scoped for analysis
    "selected_doc_name": "All Documents",
}
for k, v in _STATE_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────────────────────
def badge(t: str) -> str:
    cls = {"contract":"b-contract","notice":"b-notice","memo":"b-memo","deed":"b-deed"}.get(t,"b-other")
    return f'<span class="badge {cls}">{t or "unknown"}</span>'

def score_bar(s: float, color: str = "linear-gradient(90deg,#f0c040,#7ee787)") -> str:
    return (f'<div class="src-bar"><div class="src-fill" '
            f'style="width:{s*100:.0f}%;background:{color}"></div></div>')

def _rate_limit_card(exc: Exception) -> None:
    import re
    m = re.search(r"try again in ([\d.]+\w+)", str(exc), re.I)
    wait = m.group(1) if m else "a few minutes"
    st.markdown(f"""
    <div style="background:rgba(248,81,73,0.08);border:1px solid rgba(248,81,73,0.3);
                border-left:3px solid #ff7b72;border-radius:6px;padding:1rem 1.2rem;
                font-size:0.83rem;color:#c9d1d9;line-height:1.7;">
        <strong style="color:#ff7b72;">Groq API — Token Limit Reached</strong><br>
        The free tier quota (100k tokens/day) is exhausted.
        The system tried all 3 fallback models automatically.<br><br>
        <strong style="color:#f0c040;">Options:</strong>
        <ul style="margin:0.4rem 0 0 1rem;color:#8b949e;">
            <li><strong style="color:#c9d1d9;">Wait {wait}</strong> — quota resets automatically.</li>
            <li><strong style="color:#c9d1d9;">New key</strong> — create a free account at
            <a href="https://console.groq.com" target="_blank" style="color:#f0c040;">console.groq.com</a>
            and paste the new key in your <code style="color:#7ee787;">.env</code> file.</li>
        </ul>
        <div style="font-size:0.7rem;color:#484f58;margin-top:0.5rem;font-family:monospace;">{str(exc)[:160]}</div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="wordmark">
        <div class="wm-firm">Pearson Specter Litt</div>
        <div class="wm-sub">Legal Intelligence Platform</div>
    </div>""", unsafe_allow_html=True)

    docs      = list_documents()
    all_prefs = list_all_preferences()
    history   = load_metrics_history()
    active_p  = [p for p in all_prefs if p.get("active", True)]
    summary   = summarise_improvement(history)

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-pill"><div class="stat-num">{len(docs)}</div><div class="stat-lbl">Docs</div></div>
        <div class="stat-pill"><div class="stat-num">{len(active_p)}</div><div class="stat-lbl">Prefs</div></div>
        <div class="stat-pill"><div class="stat-num">{len(history)}</div><div class="stat-lbl">Edits</div></div>
    </div>""", unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="sec-label">Upload Document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop any legal document", type=SUPPORTED, label_visibility="collapsed")

    if uploaded:
        sz = f"{uploaded.size/1024:.1f} KB"
        st.markdown(f"""
        <div class="doc-card" style="border-color:#f0c040;">
            <div class="doc-name">{uploaded.name}</div>
            <div class="doc-meta">{Path(uploaded.name).suffix.upper().lstrip('.')} · {sz}</div>
        </div>""", unsafe_allow_html=True)

        if st.button("Process and Index"):
            ext = Path(uploaded.name).suffix or ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                shutil.copyfileobj(uploaded, tmp)
                tmp_path = tmp.name
            with st.spinner("Extracting and indexing…"):
                try:
                    res = process_document(tmp_path)
                    n   = add_document(res["doc_id"], uploaded.name, res["chunks"], res["structured_fields"])
                    f   = res["structured_fields"]
                    st.success(f"Indexed {n} chunks")
                    st.markdown(f"""
                    <div class="doc-card">
                        <div style="margin-bottom:0.3rem;">{badge(f.get('document_type','other'))}</div>
                        <div class="doc-meta">{f.get('summary','')[:110]}</div>
                    </div>""", unsafe_allow_html=True)
                except (RateLimitError, BadRequestError) as e:
                    _rate_limit_card(e)
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    os.unlink(tmp_path)
            st.rerun()

    # Library + Document Selector
    st.markdown('<div class="sec-label">Document Library</div>', unsafe_allow_html=True)
    if not docs:
        st.markdown('<div class="doc-meta" style="text-align:center;padding:0.8rem 0;color:#484f58;">No documents indexed.</div>', unsafe_allow_html=True)
    else:
        # Build selector options: "All Documents" + one per indexed doc
        doc_options = {"All Documents": None}
        for d in docs:
            label = d["file_name"] if len(d["file_name"]) <= 28 else d["file_name"][:25] + "..."
            doc_options[label] = d["doc_id"]

        current_label = st.session_state.selected_doc_name
        if current_label not in doc_options:
            current_label = "All Documents"

        chosen_label = st.selectbox(
            "Scope analysis to:",
            options=list(doc_options.keys()),
            index=list(doc_options.keys()).index(current_label),
            label_visibility="collapsed",
            key="doc_selector",
        )

        chosen_id = doc_options[chosen_label]

        # When selection changes, clear stale draft so user sees fresh results
        if chosen_id != st.session_state.selected_doc_id:
            st.session_state.selected_doc_id   = chosen_id
            st.session_state.selected_doc_name = chosen_label
            st.session_state.last_draft        = ""
            st.session_state.last_sources      = []
            st.session_state.last_query        = ""

        # Show cards for all docs, highlight the selected one
        for d in docs:
            is_active = (d["doc_id"] == st.session_state.selected_doc_id)
            border    = "#1f6feb" if is_active else "#30363d"
            indicator = '<span style="color:#1f6feb;font-size:0.65rem;font-weight:700;margin-left:0.4rem;">● ACTIVE</span>' if is_active else ""
            st.markdown(f"""
            <div class="doc-card" style="border-color:{border};margin-top:0.4rem;">
                <div class="doc-name">{d['file_name']}{indicator}</div>
                <div style="margin:0.2rem 0;">{badge(d.get('document_type','other'))}</div>
                <div class="doc-meta">{d.get('summary','')[:80]}…</div>
            </div>""", unsafe_allow_html=True)

        # Scope indicator below library
        if st.session_state.selected_doc_id:
            st.markdown(f"""
            <div style="margin-top:0.6rem;padding:0.45rem 0.7rem;
                        background:rgba(31,111,235,0.1);border:1px solid rgba(31,111,235,0.3);
                        border-radius:5px;font-size:0.72rem;color:#79c0ff;line-height:1.4;">
                <strong>Scoped to:</strong> {st.session_state.selected_doc_name}<br>
                <span style="color:#484f58;font-size:0.67rem;">
                Drafts will only use chunks from this document.</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="margin-top:0.6rem;padding:0.45rem 0.7rem;
                        background:rgba(139,148,158,0.08);border:1px solid #30363d;
                        border-radius:5px;font-size:0.72rem;color:#8b949e;line-height:1.4;">
                <strong>All documents</strong> — search spans the full corpus.
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-hdr">
    <h1 class="page-title">Document <span>Intelligence</span></h1>
    <p class="page-sub">Ingest · Extract · Retrieve · Draft · Improve — every output grounded in source documents</p>
</div>""", unsafe_allow_html=True)

# Pipeline tracker
n_done = sum([len(docs)>0, len(docs)>0, bool(st.session_state.last_draft), len(active_p)>0])
steps  = [("01","Ingest"),("02","Index"),("03","Draft"),("04","Learn")]
html   = '<div class="pipeline">'
for i,(n,l) in enumerate(steps):
    cls = "done" if i<n_done else ("active" if i==n_done else "")
    html += f'<div class="pipe-step {cls}">{n} &nbsp; {l}</div>'
html += "</div>"
st.markdown(html, unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Generate Draft", "Edit and Learn", "Intelligence Hub", "Operator Profile"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Generate Draft
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not docs:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-code">— no documents —</div>
            <div class="empty-title">Nothing indexed yet</div>
            <div class="empty-desc">Upload a PDF, image, or text file using the sidebar panel.</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Show active scope banner
        active_doc_id   = st.session_state.selected_doc_id
        active_doc_name = st.session_state.selected_doc_name
        if active_doc_id:
            st.markdown(f"""
            <div style="margin-bottom:0.8rem;padding:0.5rem 0.85rem;
                        background:rgba(31,111,235,0.1);border:1px solid rgba(31,111,235,0.3);
                        border-radius:5px;font-size:0.78rem;color:#79c0ff;">
                Analyzing: <strong>{active_doc_name}</strong>
                <span style="color:#484f58;font-size:0.7rem;margin-left:0.6rem;">
                (change in sidebar → Document Library)</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="margin-bottom:0.8rem;padding:0.5rem 0.85rem;
                        background:rgba(139,148,158,0.06);border:1px solid #30363d;
                        border-radius:5px;font-size:0.78rem;color:#8b949e;">
                Analyzing: <strong>All Documents</strong>
                <span style="font-size:0.7rem;margin-left:0.5rem;">
                — select a specific document in the sidebar to scope results</span>
            </div>""", unsafe_allow_html=True)

        col_q, col_c = st.columns([3,1], gap="medium")
        with col_q:
            st.markdown('<div class="col-label">Matter or question</div>', unsafe_allow_html=True)
            query = st.text_area("q", placeholder="e.g. Summarise all key facts, parties, obligations and disputes in this matter.",
                                 height=105, label_visibility="collapsed")
        with col_c:
            st.markdown('<div class="col-label">Evidence passages</div>', unsafe_allow_html=True)
            n_res = st.slider("n", 3, 15, 8, label_visibility="collapsed")
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            run_btn = st.button("Run Analysis", disabled=not query)

        if run_btn and query:
            with st.spinner("Retrieving evidence and generating grounded draft…"):
                try:
                    # Pass doc_id_filter so search is scoped to the selected document
                    chunks  = search(query, n_results=n_res, doc_id_filter=active_doc_id)
                    learned = get_active_preferences()

                    if not chunks:
                        scope_msg = f'"{active_doc_name}"' if active_doc_id else "any indexed document"
                        st.warning(f"No relevant passages found in {scope_msg}. Try broadening your query or selecting a different document.")
                    else:
                        result  = generate_draft(query=query, retrieved_chunks=chunks, learned_preferences=learned)
                        st.session_state.last_draft   = result["draft"]
                        st.session_state.last_query   = query
                        st.session_state.last_sources = result["sources"]
                        if learned:
                            st.info(f"{len(learned)} learned preferences applied.")
                except (RateLimitError, BadRequestError) as e:
                    _rate_limit_card(e)
                except Exception as e:
                    st.error(f"Generation failed: {e}")

        if st.session_state.last_draft:
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            col_d, col_s = st.columns([3,2], gap="large")

            with col_d:
                st.markdown('<div class="col-label">Generated draft</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="draft-panel">{st.session_state.last_draft}</div>', unsafe_allow_html=True)
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                st.download_button("Download as Markdown", data=st.session_state.last_draft,
                                   file_name="case_fact_summary.md", mime="text/markdown",
                                   use_container_width=True)

            with col_s:
                st.markdown('<div class="src-label">Evidence retrieved (hybrid BM25 + semantic)</div>', unsafe_allow_html=True)
                for src in st.session_state.last_sources:
                    s = src["relevance_score"]
                    st.markdown(f"""
                    <div class="src-card">
                        <div class="src-top">
                            <span class="src-ref">Source {src['source_number']}</span>
                            <span class="src-chip">{s:.0%} match</span>
                        </div>
                        <div class="src-file">{src['file_name']}</div>
                        {score_bar(s)}
                        <div class="src-excerpt">"{src['excerpt'][:180]}…"</div>
                    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Edit and Learn
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.last_draft:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-code">— no draft —</div>
            <div class="empty-title">No draft to review</div>
            <div class="empty-desc">Generate a draft first, then return here to edit and train the system.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-banner">
            <strong>How the learning loop works:</strong>
            Edit the draft on the right exactly as you would in practice.
            On submission, the system measures how much it needed to change
            (edit distance, retained content) and extracts <strong>generalizable preferences</strong>
            that automatically improve all future drafts — not just this document.
        </div>""", unsafe_allow_html=True)

        col_o, col_e = st.columns(2, gap="large")
        with col_o:
            st.markdown('<div class="col-label">Original AI draft — read only</div>', unsafe_allow_html=True)
            st.text_area("orig", value=st.session_state.last_draft, height=520,
                         disabled=True, label_visibility="collapsed")
        with col_e:
            st.markdown('<div class="col-label gold">Your edited version</div>', unsafe_allow_html=True)
            edited = st.text_area("edit", value=st.session_state.last_draft, height=520,
                                  label_visibility="collapsed", key="edit_area")

        col_b1, col_b2 = st.columns([2,1])
        with col_b1:
            submit = st.button("Submit Edits and Train", use_container_width=True)
        with col_b2:
            if st.button("Reset", use_container_width=True):
                st.rerun()

        if submit:
            if edited.strip() == st.session_state.last_draft.strip():
                st.warning("No changes detected.")
            else:
                with st.spinner("Analysing edits and extracting preferences…"):
                    doc_names = list({s["file_name"] for s in st.session_state.last_sources})
                    result    = capture_edit(
                        original_draft=st.session_state.last_draft,
                        edited_draft=edited,
                        query=st.session_state.last_query,
                        doc_names=doc_names,
                    )

                m = result.get("edit_metrics", {})
                st.session_state.last_metrics = m

                # Metrics display
                imp   = m.get("improvement_score", 0)
                ret   = m.get("retained_pct", 0)
                edpct = m.get("edit_distance_pct", 0)
                add   = m.get("additions_pct", 0)

                imp_color  = "green" if imp >= 65 else ("" if imp >= 40 else "red")
                ret_color  = "green" if ret >= 0.7 else ""
                edit_color = "green" if edpct <= 0.2 else ("red" if edpct > 0.5 else "")

                st.markdown(f"""
                <div class="metrics-row">
                    <div class="metric-box">
                        <div class="metric-val {imp_color}">{imp:.0f}</div>
                        <div class="metric-lbl">Improvement Score</div>
                        <div class="metric-sub">0 = all rewritten · 100 = perfect draft</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val {ret_color}">{ret*100:.0f}%</div>
                        <div class="metric-lbl">Content Retained</div>
                        <div class="metric-sub">AI content kept by operator</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val {edit_color}">{edpct*100:.0f}%</div>
                        <div class="metric-lbl">Edit Distance</div>
                        <div class="metric-sub">Characters changed</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val">{add*100:.0f}%</div>
                        <div class="metric-lbl">Additions</div>
                        <div class="metric-sub">New content operator added</div>
                    </div>
                </div>""", unsafe_allow_html=True)

                if result.get("preferences_extracted"):
                    st.success(f"{len(result['preferences_extracted'])} preferences extracted and saved.")
                    for p in result["preferences_extracted"]:
                        st.markdown(f"""
                        <div class="pref-row">
                            <div class="pref-dot active"></div>
                            <div><div class="pref-text">{p}</div></div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info(result.get("message","No preferences extracted."))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Intelligence Hub
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    all_prefs = list_all_preferences()
    history   = load_metrics_history()
    summary   = summarise_improvement(history)
    active_p  = [p for p in all_prefs if p.get("active",True)]

    # Top metrics
    avg_score = summary.get("avg_improvement_score", 0)
    avg_ret   = summary.get("avg_retained_pct", 0)
    trend     = summary.get("score_trend", 0)
    trend_str = f"+{trend:.1f}" if trend >= 0 else f"{trend:.1f}"
    trend_col = "green" if trend >= 0 else "red"

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-box">
            <div class="metric-val">{len(docs)}</div>
            <div class="metric-lbl">Documents indexed</div>
        </div>
        <div class="metric-box">
            <div class="metric-val">{len(active_p)}</div>
            <div class="metric-lbl">Active preferences</div>
        </div>
        <div class="metric-box">
            <div class="metric-val">{len(history)}</div>
            <div class="metric-lbl">Operator edits logged</div>
        </div>
        <div class="metric-box">
            <div class="metric-val {'green' if avg_score>=60 else ''}">{avg_score:.0f}</div>
            <div class="metric-lbl">Avg improvement score</div>
            <div class="metric-sub">Across all edits</div>
        </div>
        <div class="metric-box">
            <div class="metric-val {trend_col}">{trend_str}</div>
            <div class="metric-lbl">Score trend</div>
            <div class="metric-sub">Early vs recent drafts</div>
        </div>
        <div class="metric-box">
            <div class="metric-val {'green' if avg_ret>=0.65 else ''}">{avg_ret*100:.0f}%</div>
            <div class="metric-lbl">Avg content retained</div>
        </div>
    </div>""", unsafe_allow_html=True)

    col_p, col_h = st.columns([3,2], gap="large")

    with col_p:
        st.markdown('<div class="src-label">Learned preferences</div>', unsafe_allow_html=True)
        if not all_prefs:
            st.markdown("""
            <div class="empty-state" style="padding:2rem;">
                <div class="empty-code">— empty —</div>
                <div class="empty-title">No preferences learned yet</div>
                <div class="empty-desc">Edit a draft and submit it to begin training.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for i, pref in enumerate(all_prefs):
                is_active = pref.get("active", True)
                date_str  = pref.get("extracted_at","")[:10]
                imp_s     = pref.get("improvement_score_at_capture")
                imp_badge = f" · score at capture: {imp_s:.0f}" if imp_s else ""
                st.markdown(f"""
                <div class="pref-row" style="{'opacity:0.35;' if not is_active else ''}">
                    <div class="pref-dot {'active' if is_active else 'inactive'}"></div>
                    <div style="flex:1;">
                        <div class="pref-text">{pref['preference']}</div>
                        <div class="pref-meta">{date_str}{imp_badge}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                if is_active:
                    if st.button("Deactivate", key=f"deact_{i}"):
                        deactivate_preference(i)
                        st.rerun()

    with col_h:
        st.markdown('<div class="src-label">Edit history — improvement over time</div>', unsafe_allow_html=True)
        if not history:
            st.markdown('<div class="doc-meta" style="color:#484f58;padding:2rem 0;text-align:center;">No edits logged yet.</div>', unsafe_allow_html=True)
        else:
            for rec in reversed(history[-8:]):
                score = rec.get("improvement_score", 0)
                ret   = rec.get("retained_pct", 0)
                edpct = rec.get("edit_distance_pct", 0)
                date  = rec.get("timestamp","")[:10]
                q     = rec.get("query","")[:55]
                col   = "#7ee787" if score >= 65 else ("#f0c040" if score >= 40 else "#ff7b72")
                st.markdown(f"""
                <div class="imp-card">
                    <div class="imp-title">{q or "Untitled matter"}</div>
                    <div class="imp-row">
                        <span class="imp-key">Improvement score</span>
                        <span class="imp-val" style="color:{col};">{score:.0f}/100</span>
                    </div>
                    <div class="imp-bar-track">
                        <div class="imp-bar-fill" style="width:{score}%;background:{col};"></div>
                    </div>
                    <div class="imp-row">
                        <span class="imp-key">Content retained</span>
                        <span class="imp-val">{ret*100:.0f}%</span>
                    </div>
                    <div class="imp-row">
                        <span class="imp-key">Edit distance</span>
                        <span class="imp-val">{edpct*100:.0f}%</span>
                    </div>
                    <div class="imp-row">
                        <span class="imp-key">Date</span>
                        <span class="imp-val" style="color:#6e7681;">{date}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

        # Summary trend
        if summary and len(history) >= 2:
            e_s = summary.get("early_avg_score",0)
            l_s = summary.get("late_avg_score",0)
            delta = l_s - e_s
            d_col = "#7ee787" if delta >= 0 else "#ff7b72"
            d_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
            st.markdown(f"""
            <div class="imp-card" style="border-color:#f0c040;">
                <div class="imp-title" style="color:#f0c040;">Learning Trend</div>
                <div class="imp-row">
                    <span class="imp-key">Early drafts avg score</span>
                    <span class="imp-val">{e_s:.0f}</span>
                </div>
                <div class="imp-row">
                    <span class="imp-key">Recent drafts avg score</span>
                    <span class="imp-val">{l_s:.0f}</span>
                </div>
                <div class="imp-row">
                    <span class="imp-key">Delta (improvement)</span>
                    <span class="imp-val" style="color:{d_col};">{d_str} pts</span>
                </div>
            </div>""", unsafe_allow_html=True)

        # Trend chart with altair
        if len(history) >= 2:
            try:
                import altair as alt
                import pandas as pd
                df = pd.DataFrame([
                    {"Edit": i+1, "Improvement Score": h.get("improvement_score",0),
                     "Retained %": round(h.get("retained_pct",0)*100,1)}
                    for i, h in enumerate(history)
                ])
                chart = alt.Chart(df).mark_line(point=True, color="#f0c040").encode(
                    x=alt.X("Edit:O", title="Edit #"),
                    y=alt.Y("Improvement Score:Q", scale=alt.Scale(domain=[0,100])),
                    tooltip=["Edit","Improvement Score","Retained %"],
                ).properties(
                    height=180, background="#161b22",
                    title=alt.TitleParams("Improvement Score Over Time", color="#8b949e", fontSize=11)
                ).configure_axis(
                    gridColor="#30363d", labelColor="#8b949e", titleColor="#8b949e"
                ).configure_view(stroke="#30363d")
                st.altair_chart(chart, use_container_width=True)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Operator Profile
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    all_prefs_t4 = list_all_preferences()
    profile      = load_profile()
    examples     = list_examples()

    col_prof, col_ex = st.columns([2,3], gap="large")

    with col_prof:
        st.markdown('<div class="src-label">Operator preference profile</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-banner">
            <strong>What this is:</strong> An aggregated profile of this operator's drafting style,
            built from all their edits. Used to personalise every new draft automatically.
        </div>""", unsafe_allow_html=True)

        if st.button("Rebuild Profile from Preferences", use_container_width=True):
            with st.spinner("Analysing preferences to build profile…"):
                try:
                    profile = build_profile(all_prefs_t4)
                    st.success("Profile updated.")
                except Exception as e:
                    st.error(f"Could not build profile: {e}")
            st.rerun()

        if not profile:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-code">— no profile —</div>
                <div class="empty-title">Profile not built yet</div>
                <div class="empty-desc">Submit at least one edit, then click Rebuild Profile.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="imp-card" style="border-color:#f0c040;">
                <div class="imp-title" style="color:#f0c040;">Writing Style</div>
                <div class="pref-text">{profile.get('writing_style','—')}</div>
            </div>""", unsafe_allow_html=True)

            for section, label in [
                ("structure_preferences", "Structure Preferences"),
                ("content_priorities",    "Content Priorities"),
                ("common_additions",      "Common Additions"),
                ("avoid",                 "Things to Avoid"),
            ]:
                items = profile.get(section, [])
                if items:
                    rows = "".join(f'<div class="pref-row"><div class="pref-dot active"></div>'
                                   f'<div class="pref-text">{it}</div></div>' for it in items)
                    st.markdown(f'<div class="src-label">{label}</div>{rows}', unsafe_allow_html=True)

            if profile.get("summary"):
                st.markdown(f"""
                <div class="imp-card">
                    <div class="imp-title">Profile Summary</div>
                    <div class="pref-text">{profile['summary']}</div>
                </div>""", unsafe_allow_html=True)

    with col_ex:
        st.markdown('<div class="src-label">Few-shot gold examples</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-banner">
            <strong>What this is:</strong> Human-approved (query, draft) pairs that scored highly.
            The system injects the most relevant one into every new draft prompt as a style reference.
        </div>""", unsafe_allow_html=True)

        if not examples:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-code">— no examples —</div>
                <div class="empty-title">No gold examples yet</div>
                <div class="empty-desc">Examples are saved automatically when an edited draft scores above 55/100.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for i, ex in enumerate(examples):
                score = ex.get("improvement_score", 0)
                col_e = "#7ee787" if score >= 65 else "#f0c040"
                with st.expander(f"Example {i+1}  —  score {score:.0f}/100  —  {ex.get('saved_at','')[:10]}"):
                    st.markdown(f"""
                    <div class="imp-row" style="margin-bottom:0.5rem;">
                        <span class="imp-key">Query</span>
                        <span class="imp-val" style="color:#c9d1d9;">{ex.get('query','')[:80]}</span>
                    </div>
                    <div class="imp-row">
                        <span class="imp-key">Score</span>
                        <span class="imp-val" style="color:{col_e};">{score:.0f}/100</span>
                    </div>""", unsafe_allow_html=True)
                    st.markdown('<div class="col-label" style="margin-top:0.8rem;">Human-approved draft (excerpt)</div>', unsafe_allow_html=True)
                    st.text_area(f"ex_{i}", value=ex.get("edited_draft","")[:600], height=180,
                                 disabled=True, label_visibility="collapsed")
                    if st.button("Delete this example", key=f"del_ex_{i}"):
                        delete_example(i)
                        st.rerun()
