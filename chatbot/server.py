"""
server.py — Thin Flask wrapper around the RAG pipeline.

Run in the chatbot venv:
    python server.py

Listens on http://127.0.0.1:5100
Only accessible from localhost — the main backend proxies to it.

Endpoints
---------
POST /chat
    Body  : { "question": "..." }
    Return: { "answer": "..." }

GET  /health
    Return: { "status": "ok" }
"""

import logging
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Fix Windows Unicode ────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── App ────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
# Only the backend (localhost) should ever call this server directly,
# but allow all origins for easier local development.
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Pipeline (lazy init on first request) ─────────────────────────────────────
_ranker = None
_generator = None


def _get_pipeline():
    global _ranker, _generator
    if _ranker is None:
        log.info("Initialising RAG pipeline …")
        from retrieval.hybrid_ranker import HybridRanker
        from llm.generator import F1Generator

        _ranker    = HybridRanker(semantic_backend="chroma")
        _generator = F1Generator()
        log.info("RAG pipeline ready ✓")
    return _ranker, _generator


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    try:
        ranker, generator = _get_pipeline()

        docs = ranker.retrieve(question)
        if not docs:
            return jsonify({"answer": "I couldn't find relevant information in the knowledge base for that question."}), 200

        answer = generator.answer(question, docs)
        return jsonify({"answer": answer}), 200

    except Exception as exc:
        log.exception("Error during RAG pipeline")
        return jsonify({"error": str(exc)}), 500


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    try:
        ranker, generator = _get_pipeline()
        docs = ranker.retrieve(question)

        if not docs:
            return Response("I couldn't find relevant information in the knowledge base for that question.", mimetype="text/plain")

        def generate():
            try:
                for token in generator.stream(question, docs):
                    yield token
            except Exception as exc:
                log.exception("Error during streaming")
                yield f"\n[Error: {str(exc)}]"

        return Response(stream_with_context(generate()), mimetype="text/plain")

    except Exception as exc:
        log.exception("Error setting up stream")
        return jsonify({"error": str(exc)}), 500


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("CHATBOT_PORT", 3001))
    log.info("Starting chatbot server on http://127.0.0.1:%d", port)
    # use_reloader=False keeps the model loaded in one process
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
