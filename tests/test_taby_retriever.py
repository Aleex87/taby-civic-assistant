import httpx
import pytest

from src.schemas import SourceType
from src.services import taby_retriever


SAMPLE_HTML = """
<!doctype html>
<html lang="sv">
  <head>
    <title>Fallback title</title>
  </head>
  <body>
    <div class="cookie-consent">
      <h1>Vi använder kakor (cookies)</h1>
      <p>Cookie information</p>
    </div>

    <nav>Navigation content</nav>

    <main>
      <h1>Komplementbyggnad</h1>
      <p>
        Här finns information om bygglov för garage,
        carport och andra komplementbyggnader.
      </p>
      <p>
        Reglerna kan bero på fastigheten och gällande detaljplan.
      </p>
    </main>

    <footer>Footer content</footer>
  </body>
</html>
"""


class FakeResponse:
    """Minimal HTTP response used by retriever tests."""

    def __init__(
        self,
        text: str,
        status_code: int = 200,
    ) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request(
                "GET",
                "https://www.taby.se/example",
            )
            response = httpx.Response(
                self.status_code,
                request=request,
            )
            raise httpx.HTTPStatusError(
                "Simulated HTTP error",
                request=request,
                response=response,
            )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.taby.se/example", True),
        ("https://taby.se/example", True),
        ("https://doc.taby.se/example.pdf", True),
        ("https://service.taby.se/example", True),
        ("https://example.com", False),
        ("https://taby.se.example.com", False),
    ],
)
def test_is_official_taby_url(
    url: str,
    expected: bool,
) -> None:
    """Allow only approved official Taby domains."""

    assert taby_retriever.is_official_taby_url(url) is expected


def test_fetch_page_rejects_external_domain() -> None:
    """Reject URLs outside the approved Taby domains."""

    with pytest.raises(
        ValueError,
        match="Only official Taby URLs are allowed",
    ):
        taby_retriever.fetch_page(
            "https://example.com/external-page"
        )


def test_fetch_page_returns_html(
    monkeypatch,
) -> None:
    """Download HTML from an approved official URL."""

    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(SAMPLE_HTML)

    monkeypatch.setattr(
        taby_retriever.httpx,
        "get",
        fake_get,
    )

    html = taby_retriever.fetch_page(
        "https://www.taby.se/example"
    )

    assert "Komplementbyggnad" in html


def test_extract_page_content_uses_main_content() -> None:
    """Extract the heading and readable main page text."""

    title, text = taby_retriever.extract_page_content(
        SAMPLE_HTML
    )

    assert title == "Komplementbyggnad"
    assert "bygglov för garage" in text
    assert "Navigation content" not in text
    assert "Footer content" not in text
    assert "Cookie information" not in text


def test_build_excerpt_uses_matching_term() -> None:
    """Create an excerpt around a matching query term."""

    text = (
        "Introduction. "
        "General municipal information. "
        "A garage may require a building permit. "
        "More information follows."
    )

    excerpt = taby_retriever.build_excerpt(
        text=text,
        query_terms=["garage"],
        max_length=80,
    )

    assert "garage" in excerpt.casefold()
    assert len(excerpt) <= 80


def test_retrieve_known_pages_returns_official_source(
    monkeypatch,
) -> None:
    """Retrieve and parse a controlled official page."""

    monkeypatch.setattr(
        taby_retriever,
        "fetch_page",
        lambda url: SAMPLE_HTML,
    )

    result = taby_retriever.retrieve_known_pages(
        query="garage bygglov",
        urls=["https://www.taby.se/example"],
    )

    assert result.error_message is None
    assert result.requires_human_review is False
    assert len(result.sources) == 1

    source = result.sources[0]

    assert source.title == "Komplementbyggnad"
    assert source.url == "https://www.taby.se/example"
    assert source.source_type == SourceType.WEB_PAGE
    assert source.municipality == "Taby"
    assert source.excerpt is not None
    assert "garage" in source.excerpt.casefold()


def test_retrieve_known_pages_handles_fetch_error(
    monkeypatch,
) -> None:
    """Return a structured error when no page can be retrieved."""

    def fake_fetch_page(url: str) -> str:
        request = httpx.Request("GET", url)
        response = httpx.Response(
            503,
            request=request,
        )
        raise httpx.HTTPStatusError(
            "Simulated provider failure",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        taby_retriever,
        "fetch_page",
        fake_fetch_page,
    )

    result = taby_retriever.retrieve_known_pages(
        query="garage bygglov",
        urls=["https://www.taby.se/example"],
    )

    assert result.sources == []
    assert result.requires_human_review is True
    assert result.error_message is not None
    assert "Simulated provider failure" in result.error_message