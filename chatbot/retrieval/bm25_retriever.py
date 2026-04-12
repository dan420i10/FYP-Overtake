"""
retrieval/bm25_retriever.py

Sparse BM25 retrieval using rank_bm25 (BM25Okapi).
Loads the pre-built index from disk and returns ranked candidate chunks.
"""

import pickle
import sys
import logging
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BM25_DIR, TOP_K_BM25

log = logging.getLogger(__name__)

BM25_INDEX_PATH  = BM25_DIR / "f1_bm25.pkl"
BM25_CORPUS_PATH = BM25_DIR / "f1_corpus.pkl"


@dataclass
class RetrievedDoc:
    """A candidate document returned by a retriever."""
    chunk_id:   str
    text:       str
    score:      float
    metadata:   dict
    rank:       int = 0


def _tokenise(text: str) -> list[str]:
    return text.lower().split()


class BM25Retriever:
    """
    Wraps a serialised BM25Okapi index.

    Usage
    -----
    retriever = BM25Retriever()
    docs = retriever.retrieve("Hamilton pole position Monaco", top_k=10)
    """

    def __init__(self) -> None:
        self._loaded = False
        self.index   = None
        self.corpus  = None

    def _load(self) -> None:
        if self._loaded:
            return
        if not BM25_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"BM25 index not found at {BM25_INDEX_PATH}. "
                "Run `python ingestion/ingest.py` first."
            )
        log.info("Loading BM25 index …")
        with open(BM25_INDEX_PATH, "rb") as f:
            self.index = pickle.load(f)
        with open(BM25_CORPUS_PATH, "rb") as f:
            self.corpus = pickle.load(f)
        self._loaded = True
        log.info(f"BM25 index loaded ({len(self.corpus['texts']):,} docs)")

    def retrieve(self, query: str, top_k: int = TOP_K_BM25) -> list[RetrievedDoc]:
        """
        Return top-k chunks ranked by BM25 score.

        Parameters
        ----------
        query : natural language query string
        top_k : number of results to return
        """
        self._load()

        tokenised_query = _tokenise(query)
        scores          = self.index.get_scores(tokenised_query)

        # argsort descending, take top_k
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            results.append(RetrievedDoc(
                chunk_id = self.corpus["ids"][idx],
                text     = self.corpus["texts"][idx],
                score    = float(scores[idx]),
                metadata = self.corpus["metas"][idx],
                rank     = rank,
            ))

        return results
