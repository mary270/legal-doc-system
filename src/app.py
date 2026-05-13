"""
Streamlit UI for the Legal Document Drafting System.
Run with: streamlit run src/app.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import streamlit as st

from document_processor import process_document
from retrieval import add_document, search, list_documents
from draft_generator import generate_draft
from edit_learner import capture_edit, get_active_preferences, list_all_preferences

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pearson Specter Litt — AI Drafter",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Pearson Specter Litt — Legal Document AI")
st.caption("Ingest messy legal documents · Retrieve evidence · Generate grounded drafts · Learn from edits")

# ── Session state ──────────────────────────────────────────────────────────────

if "last_draft" not in st.session_state:
    st.session_state.last_draft = ""
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# ── Sidebar: document management ──────────────────────────────────────────────

with st.sidebar:
    st.header("📄 Document Library")

    docs = list_documents()
    if docs:
        for doc in docs:
            st.markdown(f"**{doc['file_name']}**")
            st.caption(f"{doc['document_type']} · {doc['summary'][:80]}...")
            st.divider()
    else:
        st.info("No documents indexed yet. Upload below.")

    st.header("⬆️ Upload Document")
    uploaded = st.file_uploader(
        "Upload PDF, image, or text file",
        type=["pdf", "txt", "png", "jpg", "jpeg", "tiff"],
    )

    if uploaded and st.button("Process & Index", type="primary"):
        import tempfile, shutil
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(uploaded, tmp)
            tmp_path = tmp.name

        with st.spinner("Processing document..."):
            try:
                result = process_document(tmp_path)
                chunks_added = add_document(
                    doc_id=result["doc_id"],
                    file_name=uploaded.name,
                    chunks=result["chunks"],
                    structured_fields=result["structured_fields"],
                )
                st.success(f"Indexed {chunks_added} chunks from {uploaded.name}")
                with st.expander("Extracted fields"):
                    st.json(result["structured_fields"])
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                os.unlink(tmp_path)
            st.rerun()

# ── Main tabs ──────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📝 Generate Draft", "✏️ Edit & Learn", "🧠 Learned Preferences"])

# ── Tab 1: Generate ────────────────────────────────────────────────────────────

with tab1:
    st.subheader("Generate a Grounded Case Fact Summary")

    query = st.text_area(
        "Describe the matter or question",
        placeholder="e.g. Summarize key facts about the commercial lease dispute between Riverside Corp and Harbor LLC",
        height=100,
    )
    n_results = st.slider("Evidence passages to retrieve", 3, 15, 8)

    col1, col2 = st.columns([1, 3])
    with col1:
        generate_btn = st.button("Generate Draft", type="primary", disabled=not query)

    if generate_btn and query:
        with st.spinner("Retrieving evidence and generating draft..."):
            prefs = get_active_preferences()
            chunks = search(query, n_results=n_results)
            result = generate_draft(query=query, retrieved_chunks=chunks, learned_preferences=prefs)

        st.session_state.last_draft = result["draft"]
        st.session_state.last_query = query
        st.session_state.last_sources = result["sources"]

        if prefs:
            st.info(f"Applied {len(prefs)} learned operator preferences to this draft.")

    if st.session_state.last_draft:
        st.markdown("---")
        st.markdown(st.session_state.last_draft)

        with st.expander("📚 Evidence Sources Used"):
            for src in st.session_state.last_sources:
                st.markdown(f"**[Source {src['source_number']}]** — `{src['file_name']}` (relevance: {src['relevance_score']:.2f})")
                st.caption(src["excerpt"])
                st.divider()

# ── Tab 2: Edit & Learn ────────────────────────────────────────────────────────

with tab2:
    st.subheader("Edit the Draft — Teach the System Your Preferences")
    st.markdown(
        "Edit the AI draft below as you would in real practice. "
        "When you submit, the system analyzes what changed and extracts **reusable preferences** "
        "that will automatically improve all future drafts."
    )

    if not st.session_state.last_draft:
        st.warning("Generate a draft first in the 'Generate Draft' tab.")
    else:
        col_orig, col_edit = st.columns(2)

        with col_orig:
            st.caption("Original AI Draft")
            st.text_area(
                "original",
                value=st.session_state.last_draft,
                height=500,
                disabled=True,
                label_visibility="collapsed",
            )

        with col_edit:
            st.caption("Your Edited Version")
            edited = st.text_area(
                "edited",
                value=st.session_state.last_draft,
                height=500,
                label_visibility="collapsed",
                key="edited_draft",
            )

        if st.button("Submit Edits & Learn", type="primary"):
            with st.spinner("Analyzing your edits..."):
                doc_names = [s["file_name"] for s in st.session_state.last_sources]
                result = capture_edit(
                    original_draft=st.session_state.last_draft,
                    edited_draft=edited,
                    query=st.session_state.last_query,
                    doc_names=doc_names,
                )

            if result["preferences_extracted"]:
                st.success(f"Learned {len(result['preferences_extracted'])} new preferences!")
                for pref in result["preferences_extracted"]:
                    st.markdown(f"- {pref}")
                st.info("These preferences will be applied to all future drafts.")
            else:
                st.info(result.get("message", "No new preferences extracted."))

# ── Tab 3: Preferences ─────────────────────────────────────────────────────────

with tab3:
    st.subheader("Learned Operator Preferences")
    st.markdown("These preferences were extracted from prior operator edits and are applied to new drafts.")

    all_prefs = list_all_preferences()
    if not all_prefs:
        st.info("No preferences learned yet. Generate a draft, edit it, and submit feedback.")
    else:
        active = [p for p in all_prefs if p.get("active", True)]
        inactive = [p for p in all_prefs if not p.get("active", True)]

        st.metric("Active preferences", len(active))
        st.metric("Total learned", len(all_prefs))

        st.markdown("### Active Preferences")
        for i, pref in enumerate(all_prefs):
            if pref.get("active", True):
                st.markdown(f"**{i}.** {pref['preference']}")
                st.caption(f"Learned: {pref['extracted_at'][:10]} · Query: {pref['query'][:60]}")

        if inactive:
            with st.expander("Inactive preferences"):
                for pref in inactive:
                    st.markdown(f"~~{pref['preference']}~~")
