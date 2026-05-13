"""
Pearson Specter Litt — Legal Document AI
Streamlit UI: Professional law-firm dark theme with full document support.
Run with: streamlit run src/app.py
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

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="PSL Legal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — professional law-firm dark theme ──────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ── Main background ── */
.stApp { background-color: #0d1117; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 60%, #1a1200 100%);
    border: 1px solid #30363d;
    border-left: 4px solid #d4a017;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #d4a017;
    margin: 0 0 0.3rem 0;
    letter-spacing: 0.5px;
}
.hero-subtitle {
    font-size: 1rem;
    color: #8b949e;
    margin: 0;
    font-weight: 300;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.hero-badge {
    display: inline-block;
    background: rgba(212, 160, 23, 0.12);
    border: 1px solid rgba(212, 160, 23, 0.3);
    color: #d4a017;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    margin-bottom: 0.8rem;
    display: inline-block;
}

/* ── Metric cards ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    flex: 1;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #d4a017; }
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #d4a017;
    line-height: 1;
}
.metric-label {
    font-size: 0.75rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

/* ── Document cards ── */
.doc-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: all 0.2s ease;
    cursor: default;
}
.doc-card:hover {
    border-color: #d4a017;
    background: #1c2128;
    transform: translateX(3px);
}
.doc-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #e6edf3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.doc-meta {
    font-size: 0.72rem;
    color: #8b949e;
    margin-top: 0.2rem;
}
.doc-type-badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    margin-right: 0.4rem;
}
.badge-contract  { background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
.badge-notice    { background: rgba(248,81,73,0.15);  color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
.badge-memo      { background: rgba(63,185,80,0.15);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.badge-deed      { background: rgba(212,160,23,0.15); color: #d4a017; border: 1px solid rgba(212,160,23,0.3); }
.badge-other     { background: rgba(139,148,158,0.15);color: #8b949e; border: 1px solid rgba(139,148,158,0.3); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-radius: 10px;
    padding: 0.3rem;
    gap: 0.3rem;
    border: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #8b949e;
    border-radius: 7px;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 0.5rem 1.2rem;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: rgba(212, 160, 23, 0.15) !important;
    color: #d4a017 !important;
    border: 1px solid rgba(212,160,23,0.3) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #d4a017 0%, #b8861a 100%);
    color: #0d1117;
    font-weight: 700;
    font-size: 0.85rem;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.4rem;
    letter-spacing: 0.5px;
    transition: all 0.2s;
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #e6b520 0%, #c99b1e 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(212,160,23,0.25);
}
.stButton > button[kind="secondary"] {
    background: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
}

/* ── Text inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #d4a017 !important;
    box-shadow: 0 0 0 2px rgba(212,160,23,0.15) !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] { color: #d4a017; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #161b22;
    border: 2px dashed #30363d;
    border-radius: 10px;
    padding: 1rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #d4a017; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Draft display ── */
.draft-container {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 2rem;
    font-size: 0.9rem;
    line-height: 1.7;
}
.draft-container h2, .draft-container h3 {
    color: #d4a017;
    border-bottom: 1px solid #21262d;
    padding-bottom: 0.4rem;
    font-family: 'Playfair Display', serif;
}

/* ── Source cards ── */
.source-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-left: 3px solid #d4a017;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.8rem;
}
.source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.source-label { font-weight: 700; color: #d4a017; }
.source-file  { color: #8b949e; font-size: 0.75rem; }
.source-score {
    background: rgba(63,185,80,0.15);
    color: #3fb950;
    border: 1px solid rgba(63,185,80,0.3);
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    font-size: 0.7rem;
    font-weight: 600;
}
.source-text  { color: #8b949e; font-style: italic; line-height: 1.5; }

/* ── Progress bar ── */
.relevance-bar-bg {
    background: #21262d;
    border-radius: 4px;
    height: 4px;
    margin-top: 0.4rem;
}
.relevance-bar-fill {
    background: linear-gradient(90deg, #d4a017, #3fb950);
    border-radius: 4px;
    height: 4px;
}

/* ── Preference cards ── */
.pref-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
}
.pref-icon { font-size: 1rem; flex-shrink: 0; margin-top: 0.1rem; }
.pref-text { font-size: 0.85rem; color: #e6edf3; }
.pref-date { font-size: 0.7rem; color: #8b949e; margin-top: 0.2rem; }
.pref-inactive { opacity: 0.4; }

/* ── Alerts / Info boxes ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 8px !important;
    border: none !important;
}

/* ── Step indicators ── */
.step-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.2rem;
    align-items: center;
}
.step-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    color: #8b949e;
}
.step-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #30363d;
    flex-shrink: 0;
}
.step-dot.active  { background: #d4a017; box-shadow: 0 0 6px rgba(212,160,23,0.5); }
.step-dot.done    { background: #3fb950; }
.step-arrow { color: #30363d; font-size: 0.8rem; }

/* ── Divider ── */
hr { border-color: #21262d !important; margin: 1.2rem 0 !important; }

/* ── Hide Streamlit default elements ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Lazy imports ───────────────────────────────────────────────────────────────
from document_processor import process_document
from retrieval import add_document, search, list_documents, delete_document
from draft_generator import generate_draft
from edit_learner import capture_edit, get_active_preferences, list_all_preferences, deactivate_preference

# ── Supported file types ───────────────────────────────────────────────────────
SUPPORTED_TYPES = ["pdf", "txt", "png", "jpg", "jpeg", "tiff", "tif", "bmp",
                   "doc", "docx", "md", "csv", "rtf"]

# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "last_draft": "",
    "last_query": "",
    "last_sources": [],
    "draft_generated": False,
    "active_tab": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helper: type badge ─────────────────────────────────────────────────────────
def type_badge(doc_type: str) -> str:
    cls = {
        "contract": "badge-contract",
        "notice":   "badge-notice",
        "memo":     "badge-memo",
        "deed":     "badge-deed",
    }.get(doc_type, "badge-other")
    return f'<span class="doc-type-badge {cls}">{doc_type}</span>'


def relevance_bar(score: float) -> str:
    pct = int(score * 100)
    return f"""
    <div class="relevance-bar-bg">
        <div class="relevance-bar-fill" style="width:{pct}%"></div>
    </div>"""


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
        <div style="font-size:2.5rem;">⚖️</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.1rem;
                    color:#d4a017; font-weight:700; letter-spacing:0.5px;">
            Pearson Specter Litt
        </div>
        <div style="font-size:0.7rem; color:#8b949e; letter-spacing:1.5px;
                    text-transform:uppercase; margin-top:0.2rem;">
            Legal Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ──
    docs = list_documents()
    prefs = list_all_preferences()
    active_prefs = [p for p in prefs if p.get("active", True)]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div class="metric-value">{len(docs)}</div>
            <div class="metric-label">Documents</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div class="metric-value">{len(active_prefs)}</div>
            <div class="metric-label">Preferences</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Upload ──
    st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Upload Document</p>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop any legal document",
        type=SUPPORTED_TYPES,
        label_visibility="collapsed",
    )

    if uploaded:
        st.markdown(f'<div class="doc-card"><div class="doc-title">📎 {uploaded.name}</div><div class="doc-meta">{uploaded.size / 1024:.1f} KB</div></div>', unsafe_allow_html=True)

        if st.button("⬆ Process & Index", use_container_width=True):
            suffix = Path(uploaded.name).suffix or ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(uploaded, tmp)
                tmp_path = tmp.name

            with st.spinner("Reading & indexing…"):
                try:
                    result = process_document(tmp_path)
                    chunks_added = add_document(
                        doc_id=result["doc_id"],
                        file_name=uploaded.name,
                        chunks=result["chunks"],
                        structured_fields=result["structured_fields"],
                    )
                    st.success(f"✓ Indexed {chunks_added} chunks")
                    fields = result["structured_fields"]
                    st.markdown(f"""
                    <div class="source-card">
                        <div style="font-size:0.75rem; color:#8b949e;">
                            {type_badge(fields.get('document_type','other'))}
                            <span style="color:#3fb950; margin-left:0.3rem;">✓ Processed</span>
                        </div>
                        <div style="font-size:0.8rem; color:#c9d1d9; margin-top:0.4rem;">
                            {fields.get('summary','')[:120]}…
                        </div>
                    </div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    os.unlink(tmp_path)
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Document library ──
    st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Document Library</p>', unsafe_allow_html=True)

    if not docs:
        st.markdown('<p style="font-size:0.8rem; color:#8b949e; text-align:center; padding:1rem 0;">No documents yet.<br>Upload one above.</p>', unsafe_allow_html=True)
    else:
        for doc in docs:
            doc_type = doc.get("document_type", "other")
            badge = type_badge(doc_type)
            st.markdown(f"""
            <div class="doc-card">
                <div class="doc-title">📄 {doc['file_name']}</div>
                <div class="doc-meta" style="margin-top:0.3rem;">{badge}</div>
                <div class="doc-meta" style="margin-top:0.2rem; font-size:0.7rem;">
                    {doc.get('summary','')[:70]}…
                </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Hero ──
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">AI-Powered Legal Intelligence</div>
    <div class="hero-title">⚖️ Pearson Specter Litt</div>
    <div class="hero-subtitle">Document Understanding · Grounded Drafting · Continuous Improvement</div>
</div>
""", unsafe_allow_html=True)

# ── Pipeline step tracker ──
steps_done = sum([
    len(docs) > 0,
    len(docs) > 0,
    bool(st.session_state.last_draft),
    len(active_prefs) > 0,
])
step_labels = ["Upload Docs", "Index & Retrieve", "Generate Draft", "Learn from Edits"]
step_html = '<div class="step-row">'
for i, label in enumerate(step_labels):
    cls = "done" if i < steps_done else ("active" if i == steps_done else "")
    icon = "✓" if cls == "done" else ("●" if cls == "active" else "○")
    step_html += f'<div class="step-item"><div class="step-dot {cls}"></div>{label}</div>'
    if i < len(step_labels) - 1:
        step_html += '<div class="step-arrow">›</div>'
step_html += "</div>"
st.markdown(step_html, unsafe_allow_html=True)

# ── Tabs ──
tab1, tab2, tab3 = st.tabs([
    "📝  Generate Draft",
    "✏️  Edit & Learn",
    "🧠  Intelligence Hub",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Generate Draft
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not docs:
        st.markdown("""
        <div style="text-align:center; padding: 4rem 2rem; background:#161b22;
                    border-radius:12px; border:1px solid #21262d;">
            <div style="font-size:3rem;">📂</div>
            <div style="font-size:1.1rem; color:#c9d1d9; font-weight:600; margin:0.8rem 0;">
                No documents indexed yet
            </div>
            <div style="font-size:0.85rem; color:#8b949e;">
                Upload a PDF, image, or text file in the sidebar to get started.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_query, col_controls = st.columns([3, 1])

        with col_query:
            query = st.text_area(
                "Describe the matter or question",
                placeholder="e.g.  Summarise all key facts, parties, obligations and disputes in this matter...",
                height=110,
                label_visibility="collapsed",
            )

        with col_controls:
            st.markdown('<p style="font-size:0.8rem; color:#8b949e; margin-bottom:0.3rem;">Evidence passages</p>', unsafe_allow_html=True)
            n_results = st.slider("", 3, 15, 8, label_visibility="collapsed")
            generate_btn = st.button("⚡ Generate Draft", disabled=not query, use_container_width=True)

        if generate_btn and query:
            progress = st.progress(0, text="Retrieving evidence…")
            chunks = search(query, n_results=n_results)
            progress.progress(40, text="Applying learned preferences…")
            prefs_active = get_active_preferences()
            progress.progress(65, text="Generating grounded draft…")
            result = generate_draft(query=query, retrieved_chunks=chunks, learned_preferences=prefs_active)
            progress.progress(100, text="Done!")
            time.sleep(0.4)
            progress.empty()

            st.session_state.last_draft = result["draft"]
            st.session_state.last_query = query
            st.session_state.last_sources = result["sources"]
            st.session_state.draft_generated = True

            if prefs_active:
                st.info(f"✦ Applied {len(prefs_active)} learned operator preferences to this draft.")

        # ── Draft output ──
        if st.session_state.last_draft:
            st.markdown("<hr>", unsafe_allow_html=True)

            col_draft, col_sources = st.columns([3, 2])

            with col_draft:
                st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.6rem;">Generated Draft</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="draft-container">{st.session_state.last_draft}</div>', unsafe_allow_html=True)

                # Download button
                st.download_button(
                    label="⬇ Download Draft (.md)",
                    data=st.session_state.last_draft,
                    file_name="case_fact_summary.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            with col_sources:
                st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.6rem;">Evidence Sources</p>', unsafe_allow_html=True)

                for src in st.session_state.last_sources:
                    score = src["relevance_score"]
                    bar = relevance_bar(score)
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-header">
                            <span class="source-label">[Source {src['source_number']}]</span>
                            <span class="source-score">{score:.0%} match</span>
                        </div>
                        <div class="source-file">📄 {src['file_name']}</div>
                        {bar}
                        <div class="source-text" style="margin-top:0.5rem;">
                            "{src['excerpt'][:160]}…"
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Edit & Learn
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.last_draft:
        st.markdown("""
        <div style="text-align:center; padding:4rem 2rem; background:#161b22;
                    border-radius:12px; border:1px solid #21262d;">
            <div style="font-size:3rem;">✍️</div>
            <div style="font-size:1.1rem; color:#c9d1d9; font-weight:600; margin:0.8rem 0;">
                No draft to edit yet
            </div>
            <div style="font-size:0.85rem; color:#8b949e;">
                Generate a draft in the first tab, then come back here to edit it.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#161b22; border:1px solid #21262d; border-left:3px solid #d4a017;
                    border-radius:8px; padding:0.8rem 1.2rem; margin-bottom:1rem; font-size:0.85rem; color:#c9d1d9;">
            ✦ <strong style="color:#d4a017;">How this works:</strong>
            Edit the draft on the right as a real attorney would. When you click
            <em>Submit Edits</em>, the AI analyses what changed and extracts
            <strong>generalizable preferences</strong> — rules that improve every future draft,
            not just this one.
        </div>
        """, unsafe_allow_html=True)

        col_orig, col_edit = st.columns(2)

        with col_orig:
            st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Original AI Draft</p>', unsafe_allow_html=True)
            st.text_area(
                "orig",
                value=st.session_state.last_draft,
                height=520,
                disabled=True,
                label_visibility="collapsed",
            )

        with col_edit:
            st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#d4a017; text-transform:uppercase; letter-spacing:1px;">✏ Your Edited Version</p>', unsafe_allow_html=True)
            edited = st.text_area(
                "edit",
                value=st.session_state.last_draft,
                height=520,
                label_visibility="collapsed",
                key="edited_draft_area",
            )

        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            submit_btn = st.button("🧠 Submit Edits & Train AI", use_container_width=True)
        with col_btn2:
            if st.button("↺ Reset to Original", use_container_width=True):
                st.rerun()

        if submit_btn:
            if edited.strip() == st.session_state.last_draft.strip():
                st.warning("No changes detected — make some edits first!")
            else:
                with st.spinner("Analysing your edits and extracting preferences…"):
                    doc_names = list({s["file_name"] for s in st.session_state.last_sources})
                    result = capture_edit(
                        original_draft=st.session_state.last_draft,
                        edited_draft=edited,
                        query=st.session_state.last_query,
                        doc_names=doc_names,
                    )

                if result["preferences_extracted"]:
                    st.success(f"✓ Extracted {len(result['preferences_extracted'])} new preferences — future drafts will improve automatically!")
                    for pref in result["preferences_extracted"]:
                        st.markdown(f"""
                        <div class="pref-card">
                            <div class="pref-icon">✦</div>
                            <div><div class="pref-text">{pref}</div></div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(result.get("message", "No new preferences extracted."))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Intelligence Hub
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    all_prefs = list_all_preferences()
    active   = [p for p in all_prefs if p.get("active", True)]
    inactive = [p for p in all_prefs if not p.get("active", True)]

    # ── Stats row ──
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-value">{len(docs)}</div>
            <div class="metric-label">Documents Indexed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{len(active)}</div>
            <div class="metric-label">Active Preferences</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{len(all_prefs)}</div>
            <div class="metric-label">Total Learned</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{"Yes" if active else "No"}</div>
            <div class="metric-label">AI Personalised</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_prefs, col_docs = st.columns([3, 2])

    with col_prefs:
        st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.8rem;">🧠 Learned Operator Preferences</p>', unsafe_allow_html=True)

        if not all_prefs:
            st.markdown("""
            <div style="text-align:center; padding:2.5rem 1rem; background:#161b22;
                        border-radius:10px; border:1px solid #21262d;">
                <div style="font-size:2rem;">🧠</div>
                <div style="font-size:0.9rem; color:#8b949e; margin-top:0.5rem;">
                    No preferences learned yet.<br>
                    Edit a draft to start training the AI.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-size:0.75rem; color:#3fb950; margin-bottom:0.6rem;">● Active — applied to all new drafts</p>', unsafe_allow_html=True)
            for i, pref in enumerate(all_prefs):
                if pref.get("active", True):
                    date_str = pref.get("extracted_at", "")[:10]
                    st.markdown(f"""
                    <div class="pref-card">
                        <div class="pref-icon">✦</div>
                        <div style="flex:1;">
                            <div class="pref-text">{pref['preference']}</div>
                            <div class="pref-date">Learned {date_str} · from: {pref.get('query','')[:50]}…</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Deactivate #{i}", key=f"deact_{i}", help="Remove this preference"):
                        deactivate_preference(i)
                        st.rerun()

            if inactive:
                with st.expander(f"Inactive preferences ({len(inactive)})"):
                    for pref in inactive:
                        st.markdown(f'<div class="pref-card pref-inactive"><div class="pref-icon">✕</div><div class="pref-text">{pref["preference"]}</div></div>', unsafe_allow_html=True)

    with col_docs:
        st.markdown('<p style="font-size:0.8rem; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.8rem;">📚 Indexed Documents</p>', unsafe_allow_html=True)

        if not docs:
            st.markdown('<p style="font-size:0.85rem; color:#8b949e; text-align:center; padding:2rem;">No documents indexed.</p>', unsafe_allow_html=True)
        else:
            for doc in docs:
                doc_type = doc.get("document_type", "other")
                badge = type_badge(doc_type)
                summary = doc.get("summary", "")[:100]
                st.markdown(f"""
                <div class="doc-card">
                    <div class="doc-title">📄 {doc['file_name']}</div>
                    <div style="margin:0.3rem 0;">{badge}</div>
                    <div class="doc-meta">{summary}…</div>
                </div>
                """, unsafe_allow_html=True)
