"""
scraper/scrape_f1.py

Scrapes F1-related pages from the sources defined in config.py.
Output: one .txt file per URL saved under data/raw/
"""

import os
import re
import sys
import time
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    F1_SOURCES, RAW_DIR, SCRAPE_DELAY, SCRAPE_TIMEOUT, MAX_PAGES_PER_SITE
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; F1-RAG-Bot/1.0; "
        "+https://github.com/your-org/f1-rag)"
    )
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename (max 80 chars) + md5 suffix."""
    parsed   = urlparse(url)
    slug     = re.sub(r"[^\w\-]", "_", parsed.path.strip("/"))[:60]
    md5_short = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{parsed.netloc.replace('.', '_')}__{slug}__{md5_short}.txt"


def clean_text(text: str) -> str:
    """Normalise whitespace and remove junk lines."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        # drop very short / noisy lines
        if len(line) < 20 and not line.endswith(":"):
            continue
        # drop edit / reference noise
        if re.match(r"^\[\d+\]$", line):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# ── Parsers ────────────────────────────────────────────────────────────────────

def parse_wikipedia(soup: BeautifulSoup) -> str:
    """Extract main article text from a Wikipedia page."""
    content_div = soup.find("div", id="mw-content-text")
    if not content_div:
        return ""

    # Remove unwanted elements
    for tag in content_div.find_all(
        ["table", "sup", "span.mw-editsection",
         "div.navbox", "div.reflist", "div.mw-references-wrap",
         "div.hatnote", "div.thumb"]
    ):
        tag.decompose()

    paragraphs = content_div.find_all("p")
    text = "\n\n".join(p.get_text(separator=" ") for p in paragraphs if p.get_text(strip=True))
    return clean_text(text)


def parse_generic(soup: BeautifulSoup) -> str:
    """Fallback: extract all paragraph text from any page."""
    for tag in soup.find_all(["nav", "footer", "header", "aside",
                               "script", "style", "noscript"]):
        tag.decompose()

    paragraphs = soup.find_all("p")
    text = "\n\n".join(p.get_text(separator=" ") for p in paragraphs if p.get_text(strip=True))
    return clean_text(text)


# ── Core scrape function ───────────────────────────────────────────────────────

def scrape_url(url: str) -> str | None:
    """Fetch a single URL and return cleaned text or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=SCRAPE_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    # Choose parser
    if "wikipedia.org" in url:
        body = parse_wikipedia(soup)
    else:
        body = parse_generic(soup)

    if not body:
        log.warning(f"No content extracted from {url}")
        return None

    return f"SOURCE: {url}\nTITLE: {title}\n\n{body}"


# ── Main pipeline ──────────────────────────────────────────────────────────────

def scrape_all(urls: list[str] = F1_SOURCES) -> dict[str, Path]:
    """
    Scrape all URLs, save each as a .txt file in RAW_DIR.
    Returns mapping {url: Path}.
    """
    saved: dict[str, Path] = {}
    total = len(urls)

    log.info(f"Starting scrape of {total} URLs → {RAW_DIR}")

    for idx, url in enumerate(urls, 1):
        filename = url_to_filename(url)
        out_path  = RAW_DIR / filename

        if out_path.exists():
            log.info(f"[{idx}/{total}] SKIP (cached): {url}")
            saved[url] = out_path
            continue

        log.info(f"[{idx}/{total}] Fetching: {url}")
        text = scrape_url(url)

        if text:
            out_path.write_text(text, encoding="utf-8")
            log.info(f"  ✓ Saved {len(text):,} chars → {filename}")
            saved[url] = out_path
        else:
            log.warning(f"  ✗ Skipped (no content)")

        time.sleep(SCRAPE_DELAY)

    log.info(f"\nDone. {len(saved)}/{total} pages saved to {RAW_DIR}")
    return saved


if __name__ == "__main__":
    results = scrape_all()

    # Summary
    total_chars = sum(p.stat().st_size for p in results.values())
    print(f"\n{'='*60}")
    print(f"Scraped {len(results)} documents")
    print(f"Total text size: {total_chars / 1_000:.1f} KB")
    print(f"Output directory: {RAW_DIR}")
    print(f"{'='*60}")
