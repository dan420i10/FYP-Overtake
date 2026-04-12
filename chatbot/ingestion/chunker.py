"""
ingestion/chunker.py

Splits raw text documents into overlapping chunks suitable for embedding.
Uses a character-level sliding window that respects sentence boundaries.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class Chunk:
    """A single text chunk with associated metadata."""
    text:       str
    source_url: str
    doc_title:  str
    chunk_id:   str          # "{filename}_{idx:04d}"
    char_start: int
    char_end:   int
    metadata:   dict = field(default_factory=dict)


# ── Sentence splitter ──────────────────────────────────────────────────────────

_SENT_END = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Naive sentence splitter (no heavy NLP dependency required)."""
    return _SENT_END.split(text)


# ── Core chunker ───────────────────────────────────────────────────────────────

def chunk_text(
    text:       str,
    source_url: str,
    doc_title:  str,
    doc_id:     str,
    chunk_size: int = CHUNK_SIZE,
    overlap:    int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Splits `text` into overlapping chunks.

    Strategy:
    1. Split into sentences.
    2. Greedily pack sentences until chunk_size is reached.
    3. Next chunk starts `overlap` chars before the current end.
    """
    sentences = _split_sentences(text)
    chunks    : list[Chunk] = []
    buf       : list[str]   = []
    buf_len   = 0
    char_start = 0
    idx        = 0
    sent_i     = 0

    while sent_i < len(sentences):
        sentence = sentences[sent_i].strip()
        if not sentence:
            sent_i += 1
            continue

        buf.append(sentence)
        buf_len += len(sentence) + 1   # +1 for space

        if buf_len >= chunk_size:
            chunk_text_str = " ".join(buf)
            char_end = char_start + len(chunk_text_str)

            chunks.append(Chunk(
                text       = chunk_text_str,
                source_url = source_url,
                doc_title  = doc_title,
                chunk_id   = f"{doc_id}_{idx:04d}",
                char_start = char_start,
                char_end   = char_end,
                metadata   = {
                    "source":    source_url,
                    "title":     doc_title,
                    "chunk_idx": idx,
                },
            ))

            idx += 1

            # Roll back by overlap
            rollback_chars = 0
            rollback_sents = []
            for s in reversed(buf):
                rollback_chars += len(s) + 1
                rollback_sents.insert(0, s)
                if rollback_chars >= overlap:
                    break

            char_start = char_end - rollback_chars
            buf        = rollback_sents
            buf_len    = rollback_chars

        sent_i += 1

    # Flush remainder
    if buf:
        chunk_text_str = " ".join(buf)
        chunks.append(Chunk(
            text       = chunk_text_str,
            source_url = source_url,
            doc_title  = doc_title,
            chunk_id   = f"{doc_id}_{idx:04d}",
            char_start = char_start,
            char_end   = char_start + len(chunk_text_str),
            metadata   = {
                "source":    source_url,
                "title":     doc_title,
                "chunk_idx": idx,
            },
        ))

    return chunks


# ── File loader ────────────────────────────────────────────────────────────────

def _parse_header(text: str) -> tuple[str, str, str]:
    """
    Extract SOURCE / TITLE from the header written by the scraper.
    Returns (source_url, title, body_text).
    """
    source_url = ""
    title      = ""
    lines      = text.splitlines()
    body_start = 0

    for i, line in enumerate(lines):
        if line.startswith("SOURCE: "):
            source_url = line[len("SOURCE: "):].strip()
        elif line.startswith("TITLE: "):
            title = line[len("TITLE: "):].strip()
        elif line.strip() == "" and i > 1:
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    return source_url, title, body


def chunks_from_file(path: Path) -> list[Chunk]:
    """Load a raw .txt file produced by the scraper and return its chunks."""
    raw_text   = path.read_text(encoding="utf-8")
    source_url, title, body = _parse_header(raw_text)
    doc_id = path.stem
    return chunk_text(body, source_url, title, doc_id)


def chunks_from_directory(raw_dir: Path) -> Generator[Chunk, None, None]:
    """Yield chunks from every .txt file in raw_dir."""
    txt_files = sorted(raw_dir.glob("*.txt"))
    for fp in txt_files:
        for chunk in chunks_from_file(fp):
            yield chunk
