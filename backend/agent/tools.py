import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain.tools import tool


def search_web_results(query: str, max_results: int = 8) -> list[dict[str, str]]:
    """
    Searches the web and returns normalized result objects.
    """
    results = []
    for backend in ("duckduckgo", "bing", "yahoo", "auto"):
        try:
            with DDGS(timeout=20) as ddgs:
                results = list(ddgs.text(query, max_results=max_results, backend=backend))
            if results:
                break
        except Exception as exc:
            print(f"--- Search backend '{backend}' failed: {exc} ---")

    normalized_results = []
    seen_urls = set()
    for result in results:
        url = result.get("href") or result.get("url")
        title = result.get("title") or url
        snippet = result.get("body") or result.get("snippet") or ""
        if url and url not in seen_urls:
            seen_urls.add(url)
            normalized_results.append({
                "title": str(title),
                "url": str(url),
                "snippet": str(snippet),
            })

    return normalized_results


def scrape_url(url: str) -> str:
    """
    Scrapes readable text content from a URL.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    return " ".join(t.strip() for t in soup.stripped_strings)


@tool("web_search")
def search_web(query: str) -> list[dict[str, str]]:
    """
    Searches the web and returns result objects with title, url, and snippet.
    Use the returned URLs as input to the web_scraper tool.
    """
    return search_web_results(query)


@tool("web_scraper")
def scrape_website(url: str) -> str:
    """
    Scrapes the text content from a given website URL.
    """
    print(f"--- Scraping {url} ---")
    try:
        text = scrape_url(url)
        print(f"--- Finished scraping {url} ---")
        return text
    except requests.RequestException as e:
        return f"Error scraping website: {e}"
    except Exception as e:
        return f"An unexpected error occurred during scraping: {e}"


research_tools = [search_web, scrape_website]
