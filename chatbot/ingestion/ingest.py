"""
ingestion/ingest.py

Reads all chunked documents and populates:
  1. ChromaDB  — persistent vector store (cosine similarity)
  2. FAISS     — flat inner-product index for fast ANN lookup
  3. BM25      — sparse index serialised with pickle

Run once (or re-run to refresh after scraping new pages).

GPU note: The SentenceTransformer encoder is placed on CUDA (via
EMBEDDING_DEVICE in config.py) when available, which significantly
speeds up the batch encoding step during ingestion.
"""

import os
import pickle
import sys
import logging
from pathlib import Path

import numpy as np
import faiss
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    RAW_DIR, CHROMA_DIR, FAISS_DIR, BM25_DIR,
    EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_DEVICE,
    CHROMA_COLLECTION,
)
from ingestion.chunker import chunks_from_directory, Chunk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

FAISS_INDEX_PATH  = FAISS_DIR / "f1.index"
FAISS_META_PATH   = FAISS_DIR / "f1_meta.pkl"
BM25_INDEX_PATH   = BM25_DIR  / "f1_bm25.pkl"
BM25_CORPUS_PATH  = BM25_DIR  / "f1_corpus.pkl"

BATCH_SIZE = 128   # larger batches are more efficient on GPU (was 64)


# ── Tokeniser for BM25 ─────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenisation for BM25."""
    return text.lower().split()


# ── Main ingestion ─────────────────────────────────────────────────────────────

def ingest(raw_dir: Path = RAW_DIR, force: bool = False) -> None:
    """
    Full ingestion pipeline.

    Parameters
    ----------
    raw_dir : directory containing scraped .txt files
    force   : if True, rebuild indexes even if they exist
    """

    # ── 0. Load chunks ──────────────────────────────────────────────────────────
    log.info(f"Loading chunks from {raw_dir} …")
    chunks: list[Chunk] = list(chunks_from_directory(raw_dir))

    if not chunks:
        log.error("No chunks found — run scraper/scrape_f1.py first!")
        return

    texts   = [c.text       for c in chunks]
    ids     = [c.chunk_id   for c in chunks]
    metas   = [c.metadata   for c in chunks]
    log.info(f"Total chunks: {len(chunks):,}")

    # ── 1. Embed ────────────────────────────────────────────────────────────────
    log.info(f"Loading embedding model: {EMBEDDING_MODEL}  (device: {EMBEDDING_DEVICE})")
    embedder = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)

    log.info("Encoding chunks …")
    embeddings = embedder.encode(
        texts,
        batch_size            = BATCH_SIZE,
        show_progress_bar     = True,
        normalize_embeddings  = True,   # cosine via inner product
        convert_to_numpy      = True,
    ).astype("float32")
    log.info(f"Embeddings shape: {embeddings.shape}")

    # ── 2. ChromaDB ─────────────────────────────────────────────────────────────
    chroma_client = chromadb.PersistentClient(
        path     = str(CHROMA_DIR),
        settings = Settings(anonymized_telemetry=False),
    )

    # Drop + recreate collection on re-ingest (idempotent)
    try:
        chroma_client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name      = CHROMA_COLLECTION,
        metadata  = {"hnsw:space": "cosine"},
    )

    log.info("Populating ChromaDB …")
    for start in range(0, len(chunks), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.add(
            ids        = ids[start:end],
            documents  = texts[start:end],
            embeddings = embeddings[start:end].tolist(),
            metadatas  = metas[start:end],
        )
    log.info(f"ChromaDB: {collection.count()} documents stored → {CHROMA_DIR}")

    # ── 3. FAISS ────────────────────────────────────────────────────────────────
    log.info("Building FAISS index …")
    dim   = embeddings.shape[1]
    # IndexFlatIP works with L2-normalised vectors → cosine similarity
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(FAISS_INDEX_PATH))

    # Store chunk metadata list aligned to FAISS row indices
    with open(FAISS_META_PATH, "wb") as f:
        pickle.dump({"ids": ids, "texts": texts, "metas": metas}, f)

    log.info(f"FAISS index: {index.ntotal} vectors → {FAISS_INDEX_PATH}")

    # ── 4. BM25 ─────────────────────────────────────────────────────────────────
    log.info("Building BM25 index …")
    tokenised_corpus = [_tokenise(t) for t in texts]
    bm25_index       = BM25Okapi(tokenised_corpus)

    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump(bm25_index, f)

    with open(BM25_CORPUS_PATH, "wb") as f:
        pickle.dump({"tokenised": tokenised_corpus, "texts": texts,
                     "ids": ids, "metas": metas}, f)

    log.info(f"BM25 index saved → {BM25_INDEX_PATH}")
    log.info("\n✅ Ingestion complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest F1 docs into vector DB")
    parser.add_argument("--force", action="store_true", help="Rebuild all indexes")
    args = parser.parse_args()

    ingest(force=args.force)
