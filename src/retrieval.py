"""
Retrieval layer: stores processed document chunks in ChromaDB,
surfaces relevant passages for a given drafting query.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions


_CHROMA_PATH = str(Path(__file__).parent.parent / "data" / "chroma_db")
_COLLECTION_NAME = "legal_documents"

# Use sentence-transformers locally (no API key needed for retrieval)
_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_EMBED_FN,
        metadata={"hnsw:space": "cosine"},
    )


def add_document(doc_id: str, file_name: str, chunks: list[dict], structured_fields: dict) -> int:
    """
    Embed and store all chunks for a processed document.
    Returns the number of chunks added.
    """
    collection = _get_collection()

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        chunk_id = f"{doc_id}__chunk_{chunk['chunk_id']}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "doc_id": doc_id,
            "file_name": file_name,
            "chunk_index": chunk["chunk_id"],
            "document_type": structured_fields.get("document_type", "unknown"),
            "summary": structured_fields.get("summary", ""),
        })

    # ChromaDB handles upserts — safe to re-add same doc
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def search(query: str, n_results: int = 5, doc_id_filter: str | None = None) -> list[dict[str, Any]]:
    """
    Semantic search over all stored chunks.
    Returns list of result dicts with text, metadata, and similarity distance.
    """
    collection = _get_collection()

    where = {"doc_id": doc_id_filter} if doc_id_filter else None

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count() or 1),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    hits = []
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    dists = results["distances"][0] if results["distances"] else []

    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "metadata": meta,
            "relevance_score": round(1 - dist, 4),  # cosine similarity
        })

    return hits


def list_documents() -> list[dict[str, Any]]:
    """Return one entry per unique document stored."""
    collection = _get_collection()
    total = collection.count()
    if total == 0:
        return []

    # Fetch all and deduplicate by doc_id
    all_items = collection.get(include=["metadatas"])
    seen: dict[str, dict] = {}
    for meta in all_items["metadatas"]:
        doc_id = meta.get("doc_id", "")
        if doc_id not in seen:
            seen[doc_id] = {
                "doc_id": doc_id,
                "file_name": meta.get("file_name", ""),
                "document_type": meta.get("document_type", ""),
                "summary": meta.get("summary", ""),
            }
    return list(seen.values())


def delete_document(doc_id: str) -> int:
    """Remove all chunks for a document. Returns number of chunks deleted."""
    collection = _get_collection()
    existing = collection.get(where={"doc_id": doc_id})
    ids_to_delete = existing["ids"]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)
