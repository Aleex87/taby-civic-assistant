from src.schemas import (
    CitizenInquiry,
    GeocodingResult,
    InquiryContext,
)
from src.services.geocoding import geocode_address
from src.services.inquiry_analyzer import analyze_inquiry_with_llm
from src.services.taby_retriever import retrieve_known_pages


BUILDING_SOURCE_URLS = [
    (
        "https://www.taby.se/bygga-bo-och-miljo/"
        "bygga-riva-och-forandra/"
        "behover-jag-bygglov/komplementbyggnad"
    ),
]


def _geocode_primary_address(
    result,
) -> GeocodingResult | None:
    """Geocode the primary address when sufficiently complete."""

    address = result.inquiry.entities.address

    if not address.street or not address.house_number:
        return None

    return geocode_address(address)


def _geocode_reported_address(
    result,
) -> GeocodingResult | None:
    """Geocode another explicitly reported property address."""

    address = result.inquiry.entities.reported_address

    if (
        address is None
        or not address.street
        or not address.house_number
    ):
        return None

    return geocode_address(address)


def build_inquiry_context(
    inquiry: CitizenInquiry,
) -> InquiryContext:
    """Build geocoding and retrieval context for one inquiry."""

    analysis = analyze_inquiry_with_llm(inquiry)

    primary_location = _geocode_primary_address(analysis)
    reported_location = _geocode_reported_address(analysis)

    retrieval = retrieve_known_pages(
        query=" ".join(
            part
            for part in [
                analysis.inquiry.entities.subject,
                analysis.inquiry.domain.value,
                analysis.inquiry.intent.value,
            ]
            if part
        ),
        urls=BUILDING_SOURCE_URLS,
    )

    return InquiryContext(
        analysis=analysis,
        primary_location=primary_location,
        reported_location=reported_location,
        retrieval=retrieval,
    )
