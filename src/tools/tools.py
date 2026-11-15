import os
import requests
from rich import print
from langchain.tools import tool
from tavily import TavilyClient
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

gemini_api_key = os.environ["GEMINI_API_KEY"]
gemini_model = os.environ["GEMINI_MODEL"]
tavily_api_key = os.environ["TAVILY_API_KEY"]
groq_api_key = os.environ["GROQ_API_KEY"]


tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MAX_CONTENT_CHARS = 5000  # Truncate scraped content for brevity
MIN_CONTENT_CHARS = 200   # Below this, an extraction strategy is considered to have failed
NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form"]


@tool
def web_search(query: str) -> str:
    """Search the web for recent reliable information based on the query. Return titles, snippets, and URLs of relevant results."""

    results = tavily.search(query=query, max_results=3)

    out = []

    for result in results['results']:
        out.append(
            f" Title: {result['title']}\n Content: {result['content']}\n URL: {result['url']}"
        )

    return "\n --------- \n".join(out)


def _clean(text: str) -> str:
    """Collapse whitespace and truncate."""
    return re.sub(r'\s+', ' ', text).strip()[:MAX_CONTENT_CHARS]


def _visible_text(html: str) -> str:
    """Strip noise tags from HTML and return its visible text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    return soup.get_text(separator=' ', strip=True)


def _extract_from_html(html: str) -> str:
    """Try local extraction strategies in order. Returns "" if nothing usable is found."""

    # Strategy 1 -> trafilatura (best for articles and long-form content)
    extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
    if extracted and len(extracted.strip()) > MIN_CONTENT_CHARS:
        return _clean(extracted)

    # Strategy 2 -> readability
    text = _visible_text(Document(html).summary())
    if len(text) > MIN_CONTENT_CHARS:
        return _clean(text)

    # Strategy 3 -> full page text
    return _clean(_visible_text(html))


def _tavily_extract(url: str) -> str:
    """
    Fallback for sites that block direct requests (bot protection, 401/403, JS-rendered pages).
    Returns "" if Tavily cannot extract the page either.
    """
    try:
        response = tavily.extract(urls=url, extract_depth="advanced", format="text")
    except Exception as e:
        print(f"[yellow]Tavily extract failed for {url}: {e}[/yellow]")
        return ""

    for result in response.get("results", []):
        content = result.get("raw_content") or ""
        if content.strip():
            return _clean(content)
    return ""


@tool
def scrape_url(url: str) -> str:
    """
    Scrape and extract clean readable content from the given URL.
    Tries a direct fetch with multiple local extraction strategies first, then falls back
    to Tavily's extraction API for sites that block direct requests.
    """
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        content = _extract_from_html(response.text)
        if content:
            return content
        error = "Could not extract meaningful content from the page"

    except requests.exceptions.Timeout:
        error = "Request timed out while scraping the URL"

    except requests.exceptions.HTTPError as e:
        error = f"HTTP error occurred while scraping the URL: {e}"

    except Exception as e:
        print(f"[yellow]Direct fetch failed for {url}: {e}. Trying Tavily extract...[/yellow]")
        error = f"Error scraping the URL: {e}"

    # Direct scraping failed -> fall back to Tavily extract
    return _tavily_extract(url) or (
        f"{error}. Tavily extract fallback also failed; the site likely blocks automated access."
    )
