"""
retrieval/hybrid_ranker.py

Hybrid retrieval via Reciprocal Rank Fusion (RRF).

RRF score for a document d:
    RRF(d) = Σ  1 / (k + rank_i(d))
             i

Where k=60 (standard constant) and rank_i is 1-indexed position in
retriever i's result list.

This combines BM25 (keyword) and semantic (dense) rankings without
needing to calibrate score magnitudes.
"""

import sys
import logging
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TOP_K_BM25, TOP_K_SEMANTIC, TOP_K_FINAL, RRF_K
)
from retrieval.bm25_retriever     import BM25Retriever, RetrievedDoc
from retrieval.semantic_retriever import SemanticRetriever

log = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """Final result after hybrid fusion."""
    chunk_id:    str
    text:        str
    rrf_score:   float
    bm25_rank:   int | None    # 1-indexed, None if not in BM25 results
    sem_rank:    int | None    # 1-indexed, None if not in semantic results
    metadata:    dict


class HybridRanker:
    """
    Orchestrates BM25 + semantic retrieval and fuses results with RRF.

    Usage
    -----
    ranker = HybridRanker()
    results = ranker.retrieve("Why did Verstappen win the 2023 championship?")
    for r in results:
        print(r.rrf_score, r.text[:120])
    """

    def __init__(
        self,
        bm25_top_k:     int = TOP_K_BM25,
        sem_top_k:      int = TOP_K_SEMANTIC,
        final_top_k:    int = TOP_K_FINAL,
        rrf_k:          int = RRF_K,
        semantic_backend: str = "chroma",
    ) -> None:
        self.bm25_top_k    = bm25_top_k
        self.sem_top_k     = sem_top_k
        self.final_top_k   = final_top_k
        self.rrf_k         = rrf_k

        self.bm25_retriever = BM25Retriever()
        self.sem_retriever  = SemanticRetriever(backend=semantic_backend)

    def retrieve(self, query: str) -> list[RankedResult]:
        """
        Run hybrid retrieval for `query` and return top-k fused results.
        """
        log.info(f"BM25 retrieval for: '{query}'")
        bm25_results = self.bm25_retriever.retrieve(query, top_k=self.bm25_top_k)

        log.info(f"Semantic retrieval for: '{query}'")
        sem_results  = self.sem_retriever.retrieve(query,  top_k=self.sem_top_k)

        return self._fuse(bm25_results, sem_results)

    def _fuse(
        self,
        bm25_results: list[RetrievedDoc],
        sem_results:  list[RetrievedDoc],
    ) -> list[RankedResult]:
        """Apply Reciprocal Rank Fusion and return final ranked list."""

        # chunk_id → {rrf_score, bm25_rank, sem_rank, text, metadata}
        doc_map: dict[str, dict] = {}

        def add(docs: list[RetrievedDoc], source: str) -> None:
            for rank_0, doc in enumerate(docs):
                rank_1 = rank_0 + 1   # 1-indexed
                rrf    = 1.0 / (self.rrf_k + rank_1)

                if doc.chunk_id not in doc_map:
                    doc_map[doc.chunk_id] = {
                        "rrf_score": 0.0,
                        "bm25_rank": None,
                        "sem_rank":  None,
                        "text":      doc.text,
                        "metadata":  doc.metadata,
                    }

                doc_map[doc.chunk_id]["rrf_score"] += rrf

                if source == "bm25":
                    doc_map[doc.chunk_id]["bm25_rank"] = rank_1
                else:
                    doc_map[doc.chunk_id]["sem_rank"]  = rank_1

        add(bm25_results, "bm25")
        add(sem_results,  "sem")

        # Sort by RRF score descending
        sorted_ids = sorted(doc_map, key=lambda k: doc_map[k]["rrf_score"], reverse=True)

        results = []
        for cid in sorted_ids[: self.final_top_k]:
            d = doc_map[cid]
            results.append(RankedResult(
                chunk_id  = cid,
                text      = d["text"],
                rrf_score = d["rrf_score"],
                bm25_rank = d["bm25_rank"],
                sem_rank  = d["sem_rank"],
                metadata  = d["metadata"],
            ))

        log.info(
            f"Hybrid fusion: BM25={len(bm25_results)}, "
            f"Semantic={len(sem_results)} → "
            f"Final={len(results)}"
        )
        return results
