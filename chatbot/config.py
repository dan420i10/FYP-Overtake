"""
config.py — Central configuration for the F1 RAG system.
All paths, model names, and hyperparameters live here.
"""

import os
import torch
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
RAW_DIR       = DATA_DIR / "raw"
CHROMA_DIR    = DATA_DIR / "chroma_db"
FAISS_DIR     = DATA_DIR / "faiss_index"
BM25_DIR      = DATA_DIR / "bm25_index"

for d in [RAW_DIR, CHROMA_DIR, FAISS_DIR, BM25_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Scraper ────────────────────────────────────────────────────────────────────
SCRAPE_DELAY       = 1.5          # seconds between requests (be polite)
SCRAPE_TIMEOUT     = 15           # request timeout
MAX_PAGES_PER_SITE = 30           # cap per source

F1_SOURCES = [
    # Wikipedia — key F1 topics
    "https://en.wikipedia.org/wiki/Formula_One",
    "https://en.wikipedia.org/wiki/History_of_Formula_One",
    "https://en.wikipedia.org/wiki/Formula_One_regulations",
    "https://en.wikipedia.org/wiki/Formula_One_car",
    "https://en.wikipedia.org/wiki/Formula_One_engines",
    "https://en.wikipedia.org/wiki/Formula_One_tyres",
    "https://en.wikipedia.org/wiki/DRS_(Formula_One)",
    "https://en.wikipedia.org/wiki/KERS",
    "https://en.wikipedia.org/wiki/Formula_One_World_Championship",
    "https://en.wikipedia.org/wiki/List_of_Formula_One_World_Drivers%27_Champions",
    "https://en.wikipedia.org/wiki/List_of_Formula_One_World_Constructors%27_Champions",
    "https://en.wikipedia.org/wiki/2024_Formula_One_World_Championship",
    "https://en.wikipedia.org/wiki/2023_Formula_One_World_Championship",
    "https://en.wikipedia.org/wiki/2022_Formula_One_World_Championship",
    # Drivers
    "https://en.wikipedia.org/wiki/Max_Verstappen",
    "https://en.wikipedia.org/wiki/Lewis_Hamilton",
    "https://en.wikipedia.org/wiki/Charles_Leclerc",
    "https://en.wikipedia.org/wiki/Lando_Norris",
    "https://en.wikipedia.org/wiki/Fernando_Alonso",
    "https://en.wikipedia.org/wiki/Sebastian_Vettel",
    "https://en.wikipedia.org/wiki/Michael_Schumacher",
    "https://en.wikipedia.org/wiki/Ayrton_Senna",
    "https://en.wikipedia.org/wiki/Niki_Lauda",
    "https://en.wikipedia.org/wiki/Alain_Prost",
    # Teams / Constructors
    "https://en.wikipedia.org/wiki/Red_Bull_Racing",
    "https://en.wikipedia.org/wiki/Scuderia_Ferrari",
    "https://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One",
    "https://en.wikipedia.org/wiki/McLaren",
    "https://en.wikipedia.org/wiki/Aston_Martin_in_Formula_One",
    "https://en.wikipedia.org/wiki/Williams_Racing",
    "https://en.wikipedia.org/wiki/Renault_in_Formula_One",
    # Circuits
    "https://en.wikipedia.org/wiki/Monaco_Grand_Prix",
    "https://en.wikipedia.org/wiki/British_Grand_Prix",
    "https://en.wikipedia.org/wiki/Italian_Grand_Prix",
    "https://en.wikipedia.org/wiki/Belgian_Grand_Prix",
    "https://en.wikipedia.org/wiki/Japanese_Grand_Prix",
    "https://en.wikipedia.org/wiki/Abu_Dhabi_Grand_Prix",
    "https://en.wikipedia.org/wiki/Singapore_Grand_Prix",
    "https://en.wikipedia.org/wiki/Circuit_de_Monaco",
    "https://en.wikipedia.org/wiki/Silverstone_Circuit",
    "https://en.wikipedia.org/wiki/Spa-Francorchamps",
    # Technical
    "https://en.wikipedia.org/wiki/Ground_effect_in_cars",
    "https://en.wikipedia.org/wiki/Downforce",
    "https://en.wikipedia.org/wiki/Formula_One_aerodynamics",
    "https://en.wikipedia.org/wiki/Safety_car",
    "https://en.wikipedia.org/wiki/Virtual_safety_car",
    "https://en.wikipedia.org/wiki/Pit_stop",
]

# ── Chunking ───────────────────────────────────────────────────────────────────
CHUNK_SIZE        = 512       # tokens / chars per chunk
CHUNK_OVERLAP     = 64        # overlap between consecutive chunks

# ── Embedding model ────────────────────────────────────────────────────────────
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM     = 384

# Device detection — used by embedding model and FAISS
CUDA_AVAILABLE    = torch.cuda.is_available()
EMBEDDING_DEVICE  = "cuda" if CUDA_AVAILABLE else "cpu"

# ── Vector DB ─────────────────────────────────────────────────────────────────
CHROMA_COLLECTION = "f1_docs"

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K_BM25        = 10        # candidates from BM25
TOP_K_SEMANTIC    = 10        # candidates from vector search
TOP_K_FINAL       = 5         # docs sent to LLM after reranking
RRF_K             = 60        # RRF constant (standard = 60)

# ── LLM ───────────────────────────────────────────────────────────────────────
# Qwen2.5-1.5B-Instruct: best lightweight open-source model for text generation.
# With 4-bit NF4 quantisation on a CUDA GPU, generation drops from ~70s → ~3-5s.
LLM_MODEL_ID       = "Qwen/Qwen2.5-1.5B-Instruct"
LLM_MAX_NEW_TOKENS = 512
LLM_TEMPERATURE    = 0.2
LLM_TOP_P          = 0.9

# "auto" lets accelerate place layers optimally across GPU(s) + CPU.
# Override to "cuda:0" if you want to pin to a specific GPU.
LLM_DEVICE         = "auto"

# ── RAG prompt template ───────────────────────────────────────────────────────
RAG_SYSTEM_PROMPT = """You are an expert Formula 1 analyst and historian.
Answer the user's question using ONLY the provided context documents.
Be precise, factual, and concise. If the context does not contain enough
information to answer confidently, say so clearly."""

RAG_USER_TEMPLATE = """Context documents:
{context}

Question: {question}

Answer:"""
