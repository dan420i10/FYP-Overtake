"""
main.py — F1 RAG System CLI

Modes:
  interactive  : REPL loop, ask questions one by one (default)
  single       : answer one question passed via --query
  eval         : run a batch of test questions from --eval-file

Usage
-----
python main.py                                     # interactive mode
python main.py --query "Who is Max Verstappen?"    # single question
python main.py --stream                            # interactive + streaming
python main.py --backend faiss                     # use FAISS instead of Chroma
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Fix Unicode encoding on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level  = logging.WARNING,          # suppress INFO from sub-modules in CLI
    format = "%(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)


def build_pipeline(backend: str = "chroma"):
    """Lazily import and initialise the RAG pipeline components."""
    from retrieval.hybrid_ranker import HybridRanker
    from llm.generator           import F1Generator

    ranker    = HybridRanker(semantic_backend=backend)
    generator = F1Generator()
    return ranker, generator


def ask(
    question:  str,
    ranker,
    generator,
    stream:    bool = False,
    verbose:   bool = False,
) -> str:
    """Run a single question through the RAG pipeline."""

    # 1. Retrieve
    t0   = time.perf_counter()
    docs = ranker.retrieve(question)
    t_retrieve = time.perf_counter() - t0

    if not docs:
        return "⚠️  No relevant documents found in the knowledge base."

    if verbose:
        print(f"\n{'─'*60}")
        print(f"Retrieved {len(docs)} chunks in {t_retrieve:.2f}s")
        for d in docs:
            print(
                f"  [{d.chunk_id}] "
                f"RRF={d.rrf_score:.4f}  "
                f"BM25={d.bm25_rank}  Sem={d.sem_rank}  "
                f"→ {d.text[:80].strip()}…"
            )
        print(f"{'─'*60}\n")

    # 2. Generate
    t1 = time.perf_counter()

    if stream:
        print("\n🏎  Answer:\n")
        answer_parts = []
        for token in generator.stream(question, docs):
            print(token, end="", flush=True)
            answer_parts.append(token)
        print()
        answer = "".join(answer_parts)
    else:
        answer = generator.answer(question, docs)

    t_gen = time.perf_counter() - t1

    if verbose:
        print(f"\n[Generation time: {t_gen:.2f}s]")

    return answer


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="F1 RAG — Hybrid BM25 + Semantic search with Qwen2.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--query", "-q", type=str, default=None,
        help="Single question to answer (non-interactive mode)",
    )
    p.add_argument(
        "--stream", action="store_true",
        help="Stream tokens as they are generated",
    )
    p.add_argument(
        "--backend", choices=["chroma", "faiss"], default="chroma",
        help="Vector backend for semantic retrieval (default: chroma)",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show retrieved chunks and timing info",
    )
    p.add_argument(
        "--eval-file", type=Path, default=None,
        help="Path to a .txt file with one question per line (batch eval)",
    )
    return p.parse_args()


def interactive_loop(ranker, generator, stream: bool, verbose: bool) -> None:
    print("\n" + "═"*60)
    print("  🏁  F1 RAG System — Ask me anything about Formula 1")
    print("  Type 'exit' or press Ctrl-C to quit")
    print("═"*60 + "\n")

    # If stdin is not a TTY (e.g., running as subprocess from frontend),
    # read from stdin line-by-line without blocking
    is_interactive = sys.stdin.isatty()

    while True:
        try:
            if is_interactive:
                question = input("❓ Question: ").strip()
            else:
                # Read from stdin line by line (blocking until a line arrives)
                sys.stdout.write("❓ Question: ")
                sys.stdout.flush()
                question = sys.stdin.readline().strip()
                if not question:
                    break  # EOF reached
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! 🏁")
            break

        if question.lower() in ("exit", "quit", "q"):
            print("Goodbye! 🏁")
            break

        if not question:
            continue

        answer = ask(question, ranker, generator, stream=stream, verbose=verbose)

        if not stream:
            print(f"\n🏎  Answer:\n{answer}\n")


def batch_eval(
    eval_file: Path,
    ranker,
    generator,
    verbose: bool,
) -> None:
    questions = [
        line.strip()
        for line in eval_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    print(f"\nEvaluating {len(questions)} questions from {eval_file}\n")

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Q: {q}")
        answer = ask(q, ranker, generator, stream=False, verbose=verbose)
        print(f"    A: {answer}\n")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    print("Initialising F1 RAG pipeline …")
    ranker, generator = build_pipeline(backend=args.backend)
    print("Ready ✓\n")

    if args.eval_file:
        batch_eval(args.eval_file, ranker, generator, verbose=args.verbose)

    elif args.query:
        answer = ask(
            args.query, ranker, generator,
            stream  = args.stream,
            verbose = args.verbose,
        )
        if not args.stream:
            print(f"\n🏎  Answer:\n{answer}\n")

    else:
        interactive_loop(ranker, generator, stream=args.stream, verbose=args.verbose)


if __name__ == "__main__":
    main()
