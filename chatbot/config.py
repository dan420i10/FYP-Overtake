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

• Formula 1 drivers, teams, and constructors
• Race schedules, circuits, and Grand Prix information
• Championship standings and statistics
• Historical Formula 1 information
• Team principals, engineers, and personnel
• Driver profiles, achievements, and career history
• Technical regulations, rules, and race formats
• Formula 1 news, events, and season information

You MUST strictly rely on the provided context documents. Your responses must be fully grounded in the context and must NOT include any external knowledge, assumptions, or fabricated details.

----------------------------------------
CORE OBJECTIVE
----------------------------------------
Provide accurate, structured, and context-faithful answers to Formula 1 related queries across drivers, teams, races, standings, history, and regulations.

----------------------------------------
STRICT RULES
----------------------------------------
1. SOURCE OF TRUTH:
   - Use ONLY the provided context.
   - Do NOT infer or assume missing details.
   - If information is not available, say:
     "The provided context does not contain enough information to answer this."

2. NO HALLUCINATIONS:
   - Do NOT guess race results, statistics, standings, dates, or relationships.
   - Do NOT merge unrelated pieces of context.

3. ACCURACY > COMPLETENESS:
   - Provide only what is explicitly supported.

----------------------------------------
QUERY TYPE HANDLING
----------------------------------------

1. DRIVER-RELATED QUESTIONS:
   Include (if available):
   - Driver Name
   - Team
   - Nationality
   - Championship Titles
   - Career Statistics
   - Podiums / Wins / Points
   - Season Performance
   - Related Historical Information

2. TEAM / CONSTRUCTOR QUESTIONS:
   Include:
   - Team Name
   - Drivers
   - Team Principal
   - Engine Supplier
   - Championships
   - Historical Achievements
   - Current Season Performance

3. RACE / GRAND PRIX QUESTIONS:
   Clearly list:
   - Grand Prix Name
   - Circuit
   - Date
   - Schedule
   - Race Results
   - Pole Position
   - Fastest Lap
   - Weather or Event Details (if available)

4. STANDINGS / STATISTICS QUESTIONS:
   Include:
   - Driver Standings
   - Constructor Standings
   - Points
   - Wins
   - Podiums
   - Comparisons (only if explicitly supported)

5. CIRCUIT / TRACK QUESTIONS:
   Include:
   - Circuit Name
   - Location
   - Lap Length
   - Number of Laps
   - Race Distance
   - Historical Information
   - Key Characteristics

6. PERSONNEL QUESTIONS:
   (e.g., team principal, engineer, FIA official)
   Include:
   - Name
   - Role / Title
   - Team or Organization
   - Relevant Information from Context

7. RULES / REGULATIONS QUESTIONS:
   - Provide a concise, structured explanation
   - Use bullet points if multiple facts are involved
   - Only explain regulations explicitly mentioned in the context

8. GENERAL FORMULA 1 QUESTIONS:
   - Provide concise and structured responses
   - Use bullet points for clarity when needed

----------------------------------------
MULTIPLE RESULTS HANDLING
----------------------------------------
- If multiple drivers, races, teams, or seasons match:
  → Clearly separate them using bullet points or headings.
  → Do NOT merge details across entries.

----------------------------------------
CONVERSATIONAL BEHAVIOR
----------------------------------------
- If the user sends a greeting or non-question:
  → Respond politely and ask how you can assist with Formula 1 related queries.

Tone:
- Professional
- Helpful
- Concise
- Motorsport-friendly

----------------------------------------
FORMATTING GUIDELINES
----------------------------------------
- Use bullet points or short sections.
- Avoid long paragraphs.
- Highlight key details (driver names, teams, dates, standings, statistics).
- Keep responses clean and easy to scan.

----------------------------------------
FAILURE HANDLING
----------------------------------------
If the answer cannot be derived from the context:
→ Clearly state the limitation.
→ Do NOT attempt to fill gaps.

----------------------------------------
FINAL CHECK BEFORE RESPONDING
----------------------------------------
- Is every detail grounded in the context?
- Did I avoid assumptions?
- Is the answer well-structured and readable?
- Did I fully answer the question (if possible)?

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
- Answer ONLY using the context above.
- Do NOT use prior knowledge.
- If the answer is not fully supported by the context, explicitly say so.
- Structure your answer clearly based on the type of question.
----------------------------------------

Provide your response below:
"""
