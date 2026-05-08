"""
llm/generator.py

Text generation using Groq API (mixtral-8x7b-32768 model).
Fast, cloud-based inference via Groq's LPU technology.

No local GPU acceleration needed — all computation happens on Groq's servers.
"""

import sys
import logging
from pathlib import Path
from typing import Iterator

from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    GROQ_MODEL, GROQ_API_KEY, LLM_MAX_NEW_TOKENS,
    LLM_TEMPERATURE, LLM_TOP_P,
    RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE,
)
from retrieval.hybrid_ranker import RankedResult

log = logging.getLogger(__name__)


class F1Generator:
    """
    Wraps Groq API for RAG-based question answering.

    Usage
    -----
    gen = F1Generator()
    answer = gen.answer("Who is Max Verstappen?", context_docs)
    # or stream:
    for token in gen.stream("...", context_docs):
        print(token, end="", flush=True)
    """

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables. Add it to .env file.")
        self.client = Groq(api_key=GROQ_API_KEY)
        log.info(f"Groq client initialized with model: {GROQ_MODEL}")

    # ── Prompt construction ─────────────────────────────────────────────────────

    @staticmethod
    def _build_context(docs: list[RankedResult]) -> str:
        parts = []
        for doc in docs:
            parts.append(doc.text)
        return "\n\n".join(parts)

    def _build_messages(self, question: str, docs: list[RankedResult]) -> list[dict]:
        context = self._build_context(docs)
        user_msg = RAG_USER_TEMPLATE.format(context=context, question=question)
        return [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]

    # ── Generation ──────────────────────────────────────────────────────────────

    def answer(
        self,
        question:       str,
        docs:           list[RankedResult],
        max_new_tokens: int   = LLM_MAX_NEW_TOKENS,
        temperature:    float = LLM_TEMPERATURE,
        top_p:          float = LLM_TOP_P,
    ) -> str:
        """Generate a complete answer via Groq API."""
        messages = self._build_messages(question, docs)

        try:
            response = self.client.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = messages,
                max_tokens  = max_new_tokens,
                temperature = temperature,
                top_p       = top_p,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            log.error(f"Error calling Groq API: {e}")
            raise

    def stream(
        self,
        question:       str,
        docs:           list[RankedResult],
        max_new_tokens: int   = LLM_MAX_NEW_TOKENS,
        temperature:    float = LLM_TEMPERATURE,
        top_p:          float = LLM_TOP_P,
    ) -> Iterator[str]:
        """Stream the answer token by token via Groq API."""
        messages = self._build_messages(question, docs)

        try:
            response = self.client.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = messages,
                max_tokens  = max_new_tokens,
                temperature = temperature,
                top_p       = top_p,
                stream      = True,
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            log.error(f"Error calling Groq API (stream): {e}")
            raise

