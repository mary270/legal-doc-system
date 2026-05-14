"""
Retrieval layer — hybrid search combining:
  1. Semantic search  (ChromaDB + sentence-transformers, cosine similarity)
  2. BM25 keyword search (rank_bm25, exact term matching)

Scores are fused with configurable weights so relevant passages surface
even when they don't semantically match the query (e.g. proper names, case numbers).
"""
from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

try:
    from config import (
        CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL,
        HYBRID_SEMANTIC_WEIGHT, HYBRID_BM25_WEIGHT,
    )
except ImportError:
    CHROMA_DIR             = Path(__file__).parent.parent / "data" / "chroma_db"
    COLLECTION_NAME        = "legal_documents"
    EMBED_MODEL            = "all-MiniLM-L6-v2"
    HYBRID_SEMANTIC_WEIGHT = 0.65
    HYBRID_BM25_WEIGHT     = 0.35

log = logging.getLogger(__name__)

_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)


# ── ChromaDB helpers ───────────────────────────────────────────────────────────

def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_EMBED_FN,
        metadata={"hnsw:space": "cosine"},
    )


# ── BM25 (in-memory, built on-the-fly) ────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class _BM25:
    """Lightweight BM25 over a list of document strings."""
    k1 = 1.5
    b  = 0.75

    def __init__(self, docs: list[str]) -> None:
        self.docs      = docs
        self.tokenised = [_tokenise(d) for d in docs]
        self.n         = len(docs)
        avg_len        = sum(len(t) for t in self.tokenised) / max(self.n, 1)
        self.avg_dl    = avg_len

        # Document frequency
        self.df: dict[str, int] = defaultdict(int)
        for tokens in self.tokenised:
            for tok in set(tokens):
                self.df[tok] += 1

    def score(self, query: str, idx: int) -> float:
        tokens = _tokenise(query)
        doc    = self.tokenised[idx]
        dl     = len(doc)
        score  = 0.0
        tf_map: dict[str, int] = defaultdict(int)
        for t in doc:
            tf_map[t] += 1

        for tok in tokens:
            if tok not in self.df:
                continue
            tf  = tf_map.get(tok, 0)
            idf = math.log((self.n - self.df[tok] + 0.5) / (self.df[tok] + 0.5) + 1)
            num = tf * (self.k1 + 1)
            den = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
            score += idf * (num / den)
        return score


# ── Public API ─────────────────────────────────────────────────────────────────

def add_document(
    doc_id:           str,
    file_name:        str,
    chunks:           list[dict],
    structured_fields: dict,
) -> int:
    """Embed and store all chunks. Returns number of chunks added."""
    collection = _get_collection()
    ids, documents, metadatas = [], [], []

    for chunk in chunks:
        chunk_id = f"{doc_id}__chunk_{chunk['chunk_id']}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "doc_id":        doc_id,
            "file_name":     file_name,
            "chunk_index":   chunk["chunk_id"],
            "document_type": structured_fields.get("document_type", "unknown"),
            "summary":       structured_fields.get("summary", "")[:200],
        })

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    log.info("Indexed %d chunks for doc %s (%s)", len(ids), doc_id, file_name)
    return len(ids)


def search(
    query:          str,
    n_results:      int = 8,
    doc_id_filter:  str | None = None,
    use_hybrid:     bool = True,
) -> list[dict[str, Any]]:
    """
    Hybrid semantic + BM25 search.
    Returns list of result dicts with text, metadata, and fused relevance_score.
    """
    collection = _get_collection()
    total      = collection.count()
    if total == 0:
        log.warning("No documents in collection — returning empty results")
        return []

    where = {"doc_id": doc_id_filter} if doc_id_filter else None
    fetch = min(max(n_results * 2, 10), total)

    try:
        sem_results = collection.query(
            query_texts=[query],
            n_results=fetch,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        log.error("ChromaDB query failed: %s", exc)
        return []

    docs   = sem_results["documents"][0] if sem_results["documents"] else []
    metas  = sem_results["metadatas"][0] if sem_results["metadatas"] else []
    dists  = sem_results["distances"][0]  if sem_results["distances"]  else []

    if not docs:
        return []

    # Semantic scores (cosine similarity, 0-1)
    sem_scores = [round(1 - d, 4) for d in dists]

    if use_hybrid and len(docs) > 1:
        # BM25 scores over retrieved candidates
        bm25      = _BM25(docs)
        raw_bm25  = [bm25.score(query, i) for i in range(len(docs))]
        max_bm25  = max(raw_bm25) or 1.0
        bm25_norm = [s / max_bm25 for s in raw_bm25]

        fused = [
            HYBRID_SEMANTIC_WEIGHT * s + HYBRID_BM25_WEIGHT * b
            for s, b in zip(sem_scores, bm25_norm)
        ]
    else:
        fused = sem_scores

    # Sort by fused score and return top-N
    ranked = sorted(
        zip(docs, metas, fused, sem_scores),
        key=lambda x: x[2],
        reverse=True,
    )[:n_results]

    return [
        {
            "text":             doc,
            "metadata":         meta,
            "relevance_score":  round(score, 4),
            "semantic_score":   round(sem, 4),
        }
        for doc, meta, score, sem in ranked
    ]


def list_documents() -> list[dict[str, Any]]:
    """Return one entry per unique document."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    all_items = collection.get(include=["metadatas"])
    seen: dict[str, dict] = {}
    for meta in all_items["metadatas"]:
        doc_id = meta.get("doc_id", "")
        if doc_id not in seen:
            seen[doc_id] = {
                "doc_id":        doc_id,
                "file_name":     meta.get("file_name", ""),
                "document_type": meta.get("document_type", ""),
                "summary":       meta.get("summary", ""),
            }
    return list(seen.values())


def delete_document(doc_id: str) -> int:
    """Remove all chunks for a document. Returns number deleted."""
    collection = _get_collection()
    existing   = collection.get(where={"doc_id": doc_id})
    ids        = existing["ids"]
    if ids:
        collection.delete(ids=ids)
    log.info("Deleted %d chunks for doc %s", len(ids), doc_id)
    return len(ids)
