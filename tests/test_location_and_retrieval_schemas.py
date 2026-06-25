from src.schemas import (
    AddressData,
    GeocodingResult,
    GeocodingStatus,
    GeoPoint,
    RetrievedSource,
    RetrievalResult,
    SourceType,
)


def test_geocoding_result_can_represent_resolved_address() -> None:
    """Represent a successfully resolved municipal address."""

    result = GeocodingResult(
        query="Parkvägen 14, Taby",
        status=GeocodingStatus.RESOLVED,
        matched_address=AddressData(
            street="Parkvägen",
            house_number="14",
            municipality="Taby",
        ),
        coordinates=GeoPoint(
            latitude=59.443,
            longitude=18.068,
        ),
        provider="example-provider",
        confidence=0.95,
        external_id="address-123",
        raw_label="Parkvägen 14, Taby kommun",
    )

    assert result.status == GeocodingStatus.RESOLVED
    assert result.coordinates is not None
    assert result.coordinates.latitude == 59.443
    assert result.matched_address is not None
    assert result.matched_address.street == "Parkvägen"


def test_retrieval_result_can_hold_official_sources() -> None:
    """Represent official municipal sources returned by retrieval."""

    source = RetrievedSource(
        title="Building permits",
        url="https://www.taby.se/example",
        source_type=SourceType.WEB_PAGE,
        excerpt="Information about when a building permit is required.",
        relevance_score=0.91,
        municipality="Taby",
    )

    result = RetrievalResult(
        query="building permit garage property boundary",
        sources=[source],
    )

    assert len(result.sources) == 1
    assert result.sources[0].title == "Building permits"
    assert result.sources[0].source_type == SourceType.WEB_PAGE
    