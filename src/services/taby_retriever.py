from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from src.schemas import RetrievedSource, RetrievalResult, SourceType


TABY_BASE_URL = "https://www.taby.se"
PROVIDER_NAME = "Taby Municipality website"

REQUEST_HEADERS = {
    "User-Agent": (
        "Taby-Civic-Assistant/0.1 "
        "(alessandrodanteabbate@gmail.com)"
    ),
    "Accept-Language": "sv,en",
}


def is_official_taby_url(url: str) -> bool:
    """Check whether a URL belongs to an approved Taby domain."""

    hostname = urlparse(url).hostname

    return hostname in {
        "www.taby.se",
        "taby.se",
        "doc.taby.se",
        "service.taby.se",
    }


def fetch_page(url: str) -> str:
    """Download one official Taby web page."""

    if not is_official_taby_url(url):
        raise ValueError("Only official Taby URLs are allowed.")

    response = httpx.get(
        url,
        headers=REQUEST_HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(
            connect=5.0,
            read=15.0,
            write=10.0,
            pool=5.0,
        ),
    )
    response.raise_for_status()

    return response.text


def extract_page_content(
    html: str,
) -> tuple[str, str]:
    """Extract a page title and readable main text."""

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "dialog",
        ]
    ):
        element.decompose()

    for selector in [
        "[id*='cookie']",
        "[class*='cookie']",
        "[id*='consent']",
        "[class*='consent']",
    ]:
        for element in soup.select(selector):
            element.decompose()

    main = soup.find("main") or soup.body or soup

    heading = main.find("h1")
    if heading:
        title = heading.get_text(" ", strip=True)
    elif soup.title:
        title = soup.title.get_text(" ", strip=True)
    else:
        title = ""

    text = " ".join(
        main.get_text(" ", strip=True).split()
    )

    return title, text


def build_excerpt(
    text: str,
    query_terms: list[str],
    max_length: int = 500,
) -> str:
    """Build a short excerpt around the first matching query term."""

    normalized_text = text.casefold()

    match_positions = [
        normalized_text.find(term.casefold())
        for term in query_terms
        if term and normalized_text.find(term.casefold()) >= 0
    ]

    if not match_positions:
        return text[:max_length].strip()

    position = min(match_positions)
    start = max(0, position - 150)
    end = min(len(text), start + max_length)

    return text[start:end].strip()


def retrieve_known_pages(
    query: str,
    urls: list[str],
) -> RetrievalResult:
    """Retrieve and parse a controlled list of official pages."""

    query_terms = query.split()
    sources: list[RetrievedSource] = []
    errors: list[str] = []

    for url in urls:
        try:
            html = fetch_page(url)
            title, text = extract_page_content(html)

            sources.append(
                RetrievedSource(
                    title=title or url,
                    url=url,
                    source_type=SourceType.WEB_PAGE,
                    excerpt=build_excerpt(
                        text=text,
                        query_terms=query_terms,
                    ),
                    municipality="Taby",
                )
            )
        except (httpx.HTTPError, ValueError) as exc:
            errors.append(f"{url}: {exc}")

    return RetrievalResult(
        query=query,
        sources=sources,
        requires_human_review=not sources,
        error_message=(
            "; ".join(errors)
            if errors
            else None
        ),
    )
