from src.schemas import (
    AddressData,
    CitizenInquiry,
    ClassificationSource,
    GeocodingResult,
    GeocodingStatus,
    InquiryClassificationResult,
    InquiryDomain,
    InquiryEntities,
    InquiryIntent,
    RetrievedSource,
    RetrievalResult,
)
from src.services import inquiry_context


def test_build_inquiry_context_combines_all_services(
    monkeypatch,
) -> None:
    """Combine analysis, geocoding, and official source retrieval."""

    analyzed_inquiry = CitizenInquiry(
        original_text="Example inquiry",
        language="sv",
        domain=InquiryDomain.BUILDING_AND_PLANNING,
        intent=InquiryIntent.PERMISSION_QUESTION,
        entities=InquiryEntities(
            address=AddressData(
                street="Parkvägen",
                house_number="12",
                municipality="Taby",
            ),
            subject="garage",
            neighbour_related=True,
            reported_address=AddressData(
                street="Parkvägen",
                house_number="14",
                municipality="Taby",
            ),
        ),
        requires_location=True,
        requires_human_review=True,
    )

    analysis_result = InquiryClassificationResult(
        inquiry=analyzed_inquiry,
        source=ClassificationSource.LLM,
    )

    primary_location = GeocodingResult(
        query="Parkvägen 12, Taby",
        status=GeocodingStatus.RESOLVED,
        provider="test-provider",
    )

    reported_location = GeocodingResult(
        query="Parkvägen 14, Taby",
        status=GeocodingStatus.PARTIAL_MATCH,
        provider="test-provider",
    )

    retrieval_result = RetrievalResult(
        query="garage building_and_planning permission_question",
        sources=[
            RetrievedSource(
                title="Komplementbyggnad",
                url="https://www.taby.se/example",
                excerpt="Information about garages and building permits.",
                municipality="Taby",
            )
        ],
    )

    monkeypatch.setattr(
        inquiry_context,
        "analyze_inquiry_with_llm",
        lambda inquiry: analysis_result,
    )

    geocoding_results = iter(
        [
            primary_location,
            reported_location,
        ]
    )

    monkeypatch.setattr(
        inquiry_context,
        "geocode_address",
        lambda address: next(geocoding_results),
    )

    monkeypatch.setattr(
        inquiry_context,
        "retrieve_known_pages",
        lambda query, urls: retrieval_result,
    )

    result = inquiry_context.build_inquiry_context(
        CitizenInquiry(
            original_text="Example inquiry",
        )
    )

    assert result.analysis == analysis_result
    assert result.primary_location == primary_location
    assert result.reported_location == reported_location
    assert result.retrieval == retrieval_result


def test_build_inquiry_context_skips_missing_addresses(
    monkeypatch,
) -> None:
    """Skip geocoding when the analysis has no complete address."""

    analyzed_inquiry = CitizenInquiry(
        original_text="Behöver jag bygglov för ett garage?",
        language="sv",
        domain=InquiryDomain.BUILDING_AND_PLANNING,
        intent=InquiryIntent.PERMISSION_QUESTION,
        entities=InquiryEntities(
            subject="garage",
        ),
        requires_location=True,
        requires_human_review=True,
    )

    analysis_result = InquiryClassificationResult(
        inquiry=analyzed_inquiry,
        source=ClassificationSource.LLM,
    )

    monkeypatch.setattr(
        inquiry_context,
        "analyze_inquiry_with_llm",
        lambda inquiry: analysis_result,
    )

    def fail_if_geocoding_is_called(address) -> None:
        raise AssertionError(
            "Geocoding should not run for incomplete addresses."
        )

    monkeypatch.setattr(
        inquiry_context,
        "geocode_address",
        fail_if_geocoding_is_called,
    )

    monkeypatch.setattr(
        inquiry_context,
        "retrieve_known_pages",
        lambda query, urls: RetrievalResult(
            query=query,
            sources=[],
        ),
    )

    result = inquiry_context.build_inquiry_context(
        CitizenInquiry(
            original_text="Behöver jag bygglov för ett garage?",
        )
    )

    assert result.primary_location is None
    assert result.reported_location is None
    assert result.retrieval is not None


def test_build_inquiry_context_builds_retrieval_query(
    monkeypatch,
) -> None:
    """Build the retrieval query from subject, domain, and intent."""

    analyzed_inquiry = CitizenInquiry(
        original_text="Example inquiry",
        language="sv",
        domain=InquiryDomain.BUILDING_AND_PLANNING,
        intent=InquiryIntent.PERMISSION_QUESTION,
        entities=InquiryEntities(
            subject="garage",
        ),
        requires_location=False,
        requires_human_review=True,
    )

    analysis_result = InquiryClassificationResult(
        inquiry=analyzed_inquiry,
        source=ClassificationSource.LLM,
    )

    captured_query = {}

    monkeypatch.setattr(
        inquiry_context,
        "analyze_inquiry_with_llm",
        lambda inquiry: analysis_result,
    )

    def fake_retrieve_known_pages(
        query: str,
        urls: list[str],
    ) -> RetrievalResult:
        captured_query["query"] = query
        captured_query["urls"] = urls

        return RetrievalResult(
            query=query,
            sources=[],
        )

    monkeypatch.setattr(
        inquiry_context,
        "retrieve_known_pages",
        fake_retrieve_known_pages,
    )

    result = inquiry_context.build_inquiry_context(
        CitizenInquiry(
            original_text="Example inquiry",
        )
    )

    assert captured_query["query"] == (
        "garage building_and_planning permission_question"
    )
    assert captured_query["urls"] == inquiry_context.BUILDING_SOURCE_URLS
    assert result.retrieval is not None
    