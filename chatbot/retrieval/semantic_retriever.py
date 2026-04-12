"""
retrieval/semantic_retriever.py

Dense semantic retrieval using:
  - ChromaDB  for persistent storage + HNSW approximate search
  - FAISS     for exact inner-product (cosine) search as an alternative

Both use the same `sentence-transformers/all-MiniLM-L6-v2` embeddings.

GPU note: The SentenceTransformer embedding model is moved to CUDA when
available (controlled by EMBEDDING_DEVICE in config.py). This accelerates
both ingestion encoding and per-query encoding.
"""

import pickle
import sys
import logging
from pathlib import Path

import numpy as np
import faiss
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    CHROMA_DIR, FAISS_DIR, EMBEDDING_MODEL,
    CHROMA_COLLECTION, TOP_K_SEMANTIC, EMBEDDING_DEVICE,
)
from retrieval.bm25_retriever import RetrievedDoc

log = logging.getLogger(__name__)

FAISS_INDEX_PATH = FAISS_DIR / "f1.index"
FAISS_META_PATH  = FAISS_DIR / "f1_meta.pkl"


class SemanticRetriever:
    """
    Retrieves chunks by semantic similarity.

    Parameters
    ----------
    backend : "chroma" (default) or "faiss"
        Choose which vector store to query.
        Both stores hold the same documents; FAISS gives exact results
        while Chroma uses HNSW approximation (faster at scale).
    """

    def __init__(self, backend: str = "chroma") -> None:
        assert backend in ("chroma", "faiss"), "backend must be 'chroma' or 'faiss'"
        self.backend   = backend
        self._loaded   = False
        self.embedder  = None

        # chroma
        self._chroma_collection = None

        # faiss
        self._faiss_index = None
        self._faiss_meta  = None

    def _load(self) -> None:
        if self._loaded:
            return

        log.info(f"Loading embedding model: {EMBEDDING_MODEL}  (device: {EMBEDDING_DEVICE})")
        # Pass the device so the encoder runs on GPU when available
        self.embedder = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)

        if self.backend == "chroma":
            self._load_chroma()
        else:
            self._load_faiss()

        self._loaded = True

    def _load_chroma(self) -> None:
        client = chromadb.PersistentClient(
            path     = str(CHROMA_DIR),
            settings = Settings(anonymized_telemetry=False),
        )
        self._chroma_collection = client.get_collection(CHROMA_COLLECTION)
        log.info(f"ChromaDB collection loaded: {self._chroma_collection.count()} docs")

    def _load_faiss(self) -> None:
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {FAISS_INDEX_PATH}. "
                "Run `python ingestion/ingest.py` first."
            )
        self._faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
        with open(FAISS_META_PATH, "rb") as f:
            self._faiss_meta = pickle.load(f)
        log.info(f"FAISS index loaded: {self._faiss_index.ntotal} vectors")

    def _embed_query(self, query: str) -> np.ndarray:
        vec = self.embedder.encode(
            [query],
            normalize_embeddings = True,
            convert_to_numpy     = True,
        ).astype("float32")
        return vec

    # ── Chroma retrieval ────────────────────────────────────────────────────────

    def _retrieve_chroma(self, query: str, top_k: int) -> list[RetrievedDoc]:
        vec = self._embed_query(query)

        results = self._chroma_collection.query(
            query_embeddings = vec.tolist(),
            n_results        = top_k,
            include          = ["documents", "metadatas", "distances"],
        )

        docs = []
        for rank, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            # ChromaDB cosine distance → similarity: 1 - distance
            score = 1.0 - float(dist)
            docs.append(RetrievedDoc(
                chunk_id = results["ids"][0][rank],
                text     = doc,
                score    = score,
                metadata = meta,
                rank     = rank,
            ))
        return docs

    # ── FAISS retrieval ─────────────────────────────────────────────────────────

    def _retrieve_faiss(self, query: str, top_k: int) -> list[RetrievedDoc]:
        vec = self._embed_query(query)
        scores, indices = self._faiss_index.search(vec, top_k)

        docs = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:
                continue
            docs.append(RetrievedDoc(
                chunk_id = self._faiss_meta["ids"][idx],
                text     = self._faiss_meta["texts"][idx],
                score    = float(score),
                metadata = self._faiss_meta["metas"][idx],
                rank     = rank,
            ))
        return docs

    # ── Public API ──────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = TOP_K_SEMANTIC) -> list[RetrievedDoc]:
        """
        Return top-k semantically similar chunks.

        Parameters
        ----------
        query : natural language query string
        top_k : number of results
        """
        self._load()

        if self.backend == "chroma":
            return self._retrieve_chroma(query, top_k)
        else:
            return self._retrieve_faiss(query, top_k)
