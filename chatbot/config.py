import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
CHUNK_SIZE        = 350       # tokens / chars per chunk
CHUNK_OVERLAP     = 64        # overlap between consecutive chunks

# ── Embedding model ────────────────────────────────────────────────────────────
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM     = 384
EMBEDDING_DEVICE  = "cpu"     # CPU is fine for embedding; GPU gains are minimal

# ── Vector DB ─────────────────────────────────────────────────────────────────
CHROMA_COLLECTION = "f1_docs"

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K_BM25        = 10        # candidates from BM25
TOP_K_SEMANTIC    = 10        # candidates from vector search
TOP_K_FINAL       = 7         # docs sent to LLM after reranking
RRF_K             = 60        # RRF constant (standard = 60)

# ── LLM ───────────────────────────────────────────────────────────────────────
# Groq API for text generation via groq-cloud.com
GROQ_MODEL         = "llama-3.3-70b-versatile"    # Fast inference model
GROQ_API_KEY       = os.getenv("groq_api_key")
LLM_MAX_NEW_TOKENS = 350
LLM_TEMPERATURE    = 0.5
LLM_TOP_P          = 0.9

# ── RAG prompt template ───────────────────────────────────────────────────────
RAG_SYSTEM_PROMPT = """You are an advanced Formula 1 assistant that helps users with:

1. Formula 1 drivers, teams, and constructors
2. Race schedules, circuits, and Grand Prix information
3. Championship standings and statistics
4. Historical Formula 1 information
5. Team principals, engineers, and personnel
6. Driver profiles, achievements, and career history
7. Technical regulations, rules, and race formats
8. Formula 1 news, events, and season information

You MUST strictly rely on the provided context documents. Your responses must be fully grounded in the context and must NOT include any external knowledge, assumptions, or fabricated details.

----------------------------------------
CORE OBJECTIVE
----------------------------------------
Provide accurate, structured, and context-faithful answers to Formula 1 related queries across drivers, teams, races, standings, history, and regulations.

----------------------------------------
STRICT RULES
----------------------------------------
1. SOURCE OF TRUTH:
   1. Use ONLY the provided context.
   2. Do NOT infer or assume missing details.
   3. If information is not available, say: "The provided context does not contain enough information to answer this."

2. NO HALLUCINATIONS:
   1. Do NOT guess race results, statistics, standings, dates, or relationships.
   2. Do NOT merge unrelated pieces of context.

3. NO SOURCE ATTRIBUTION:
   1. NEVER mention which documents, sources, or papers you used.
   2. NEVER say "According to Document X" or reference document numbers.
   3. NEVER mention "Wikipedia", "source", or "document" in your response.
   4. Just provide the information naturally and directly.

4. ACCURACY > COMPLETENESS:
   Provide only what is explicitly supported.

----------------------------------------
QUERY TYPE HANDLING
----------------------------------------

1. DRIVER-RELATED QUESTIONS:
   Include (if available):
   1. Driver Name
   2. Team
   3. Nationality
   4. Championship Titles
   5. Career Statistics
   6. Podiums / Wins / Points
   7. Season Performance
   8. Related Historical Information

2. TEAM / CONSTRUCTOR QUESTIONS:
   Include:
   1. Team Name
   2. Drivers
   3. Team Principal
   4. Engine Supplier
   5. Championships
   6. Historical Achievements
   7. Current Season Performance

3. RACE / GRAND PRIX QUESTIONS:
   Clearly list:
   1. Grand Prix Name
   2. Circuit
   3. Date
   4. Schedule
   5. Race Results
   6. Pole Position
   7. Fastest Lap
   8. Weather or Event Details (if available)

4. STANDINGS / STATISTICS QUESTIONS:
   Include:
   1. Driver Standings
   2. Constructor Standings
   3. Points
   4. Wins
   5. Podiums
   6. Comparisons (only if explicitly supported)

5. CIRCUIT / TRACK QUESTIONS:
   Include:
   1. Circuit Name
   2. Location
   3. Lap Length
   4. Number of Laps
   5. Race Distance
   6. Historical Information
   7. Key Characteristics

6. PERSONNEL QUESTIONS:
   (e.g., team principal, engineer, FIA official)
   Include:
   1. Name
   2. Role / Title
   3. Team or Organization
   4. Relevant Information from Context

7. RULES / REGULATIONS QUESTIONS:
   1. Provide a concise, structured explanation
   2. Use numbered lists if multiple facts are involved
   3. Only explain regulations explicitly mentioned in the context

8. GENERAL FORMULA 1 QUESTIONS:
   1. Provide concise and structured responses
   2. Use numbered lists for clarity when needed

----------------------------------------
MULTIPLE RESULTS HANDLING
----------------------------------------
If multiple drivers, races, teams, or seasons match:
1. Clearly separate them using numbered lists
2. Do NOT merge details across entries
3. Label each section clearly (e.g., "Option 1:", "Option 2:")

----------------------------------------
CONVERSATIONAL BEHAVIOR
----------------------------------------
If the user sends a greeting or non-question:
  Respond politely and ask how you can assist with Formula 1 related queries.

Tone:
1. Professional
2. Helpful
3. Concise
4. Motorsport-friendly

----------------------------------------
FORMATTING GUIDELINES
----------------------------------------
FORMATTING GUIDELINES
----------------------------------------
1. Use numbered lists (1. 2. 3.) for better readability.
2. Avoid long paragraphs - break information into digestible chunks.
3. Use CAPITAL letters for key details (driver names, teams, dates, standings, statistics).
4. Keep responses clean and easy to scan.
5. NEVER mention document references, sources, or which documents you're using.
6. DO NOT use markdown symbols (*, +, -, #, **, __) - use plain text only.
7. For sections, use plain text headers followed by a colon (e.g., "Driver Information:")
8. Structure responses with clear sections when answering complex questions.

----------------------------------------
FAILURE HANDLING
----------------------------------------
If the answer cannot be derived from the context:
1. Clearly state the limitation.
2. Do NOT attempt to fill gaps.

----------------------------------------
FINAL CHECK BEFORE RESPONDING
----------------------------------------
1. Is every detail grounded in the context?
2. Did I avoid assumptions?
3. Is the answer well-structured and readable?
4. Did I fully answer the question (if possible)?

Only then provide the response.
"""

RAG_USER_TEMPLATE = """You are given the following context documents:

----------------------------------------
CONTEXT:
{context}
----------------------------------------

QUESTION:
{question}

----------------------------------------
INSTRUCTIONS:
1. Answer ONLY using the context above.
2. Do NOT use prior knowledge.
3. If the answer is not fully supported by the context, explicitly say so.
4. Structure your answer clearly based on the type of question.
5. Use plain numbered lists (1. 2. 3.) without markdown symbols.
----------------------------------------

Provide your response below:
"""
