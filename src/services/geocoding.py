import time

import httpx

from src.schemas import (
    AddressData,
    GeocodingResult,
    GeocodingStatus,
    GeoPoint,
)


NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
PROVIDER_NAME = "OpenStreetMap Nominatim"
FALLBACK_REQUEST_DELAY_SECONDS = 1.0


def build_address_query(address: AddressData) -> str:
    """Build a normalized free-form query from structured address data."""

    parts = [
        address.street,
        address.house_number,
        address.municipality,
        "Sweden",
    ]

    return ", ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def build_structured_params(
    address: AddressData,
) -> dict[str, str | int]:
    """Build structured Nominatim parameters for an address."""

    street_parts = [
        address.house_number,
        address.street,
    ]
    street = " ".join(
        part.strip()
        for part in street_parts
        if part and part.strip()
    )

    params: dict[str, str | int] = {
        "street": street,
        "country": "Sweden",
        "countrycodes": "se",
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
    }

    if address.municipality:
        params["city"] = address.municipality.strip()

    return params


def _request_nominatim(
    params: dict[str, str | int],
) -> list[dict]:
    """Send one search request to Nominatim."""

    response = httpx.get(
        NOMINATIM_SEARCH_URL,
        params=params,
        headers={
            "User-Agent": (
                "Taby-Civic-Assistant/0.1 "
                "(alessandrodanteabbate@gmail.com)"
            ),
            "Accept-Language": "sv,en",
        },
        timeout=httpx.Timeout(
            connect=5.0,
            read=15.0,
            write=10.0,
            pool=5.0,
        ),
    )
    response.raise_for_status()

    return response.json()


def _has_exact_house_number(
    result: dict,
    requested_house_number: str,
) -> bool:
    """Check whether a provider result contains the requested number."""

    raw_address = result.get("address", {})
    matched_house_number = raw_address.get("house_number")

    if not isinstance(matched_house_number, str):
        return False

    return (
        matched_house_number.casefold().strip()
        == requested_house_number.casefold().strip()
    )


def _build_result(
    query: str,
    provider_result: dict,
    requested_house_number: str,
) -> GeocodingResult:
    """Convert a Nominatim result into the application schema."""

    raw_address = provider_result.get("address", {})

    matched_address = AddressData(
        street=(
            raw_address.get("road")
            or raw_address.get("pedestrian")
            or raw_address.get("residential")
        ),
        house_number=raw_address.get("house_number"),
        municipality=(
            raw_address.get("municipality")
            or raw_address.get("city")
            or raw_address.get("town")
        ),
    )

    exact_house_number = _has_exact_house_number(
        provider_result,
        requested_house_number,
    )

    return GeocodingResult(
        query=query,
        status=(
            GeocodingStatus.RESOLVED
            if exact_house_number
            else GeocodingStatus.PARTIAL_MATCH
        ),
        matched_address=matched_address,
        coordinates=GeoPoint(
            latitude=float(provider_result["lat"]),
            longitude=float(provider_result["lon"]),
        ),
        provider=PROVIDER_NAME,
        confidence=1.0 if exact_house_number else 0.6,
        external_id=str(provider_result.get("place_id")),
        raw_label=provider_result.get("display_name"),
    )


def geocode_address(address: AddressData) -> GeocodingResult:
    """Resolve a structured address using OpenStreetMap Nominatim."""

    query = build_address_query(address)

    if not address.street or not address.house_number:
        return GeocodingResult(
            query=query,
            status=GeocodingStatus.NOT_FOUND,
            provider=PROVIDER_NAME,
            error_message=(
                "Street and house number are required for geocoding."
            ),
        )

    try:
        results = _request_nominatim(
            build_structured_params(address)
        )

        if not results:
            time.sleep(FALLBACK_REQUEST_DELAY_SECONDS)

            results = _request_nominatim(
                {
                    "q": query,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "countrycodes": "se",
                    "limit": 1,
                }
            )
    except httpx.HTTPError as exc:
        return GeocodingResult(
            query=query,
            status=GeocodingStatus.ERROR,
            provider=PROVIDER_NAME,
            error_message=str(exc),
        )

    if not results:
        return GeocodingResult(
            query=query,
            status=GeocodingStatus.NOT_FOUND,
            provider=PROVIDER_NAME,
        )

    return _build_result(
        query=query,
        provider_result=results[0],
        requested_house_number=address.house_number,
    )
