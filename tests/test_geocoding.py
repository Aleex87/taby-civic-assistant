import httpx

from src.schemas import (
    AddressData,
    GeocodingStatus,
)
from src.services import geocoding


class FakeResponse:
    """Minimal HTTP response used by geocoding tests."""

    def __init__(
        self,
        payload: list[dict],
        status_code: int = 200,
    ) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request(
                "GET",
                geocoding.NOMINATIM_SEARCH_URL,
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

    def json(self) -> list[dict]:
        return self._payload


def test_build_address_query() -> None:
    """Build a complete Swedish address query."""

    address = AddressData(
        street="Parkvägen",
        house_number="14",
        municipality="Taby",
    )

    query = geocoding.build_address_query(address)

    assert query == "Parkvägen, 14, Taby, Sweden"


def test_geocode_address_returns_resolved_match(
    monkeypatch,
) -> None:
    """Return coordinates for an exact house-number match."""

    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            [
                {
                    "place_id": 12345,
                    "lat": "59.443",
                    "lon": "18.068",
                    "display_name": (
                        "Parkvägen 14, Taby kommun, Sweden"
                    ),
                    "address": {
                        "road": "Parkvägen",
                        "house_number": "14",
                        "municipality": "Taby kommun",
                    },
                }
            ]
        )

    monkeypatch.setattr(
        geocoding.httpx,
        "get",
        fake_get,
    )

    result = geocoding.geocode_address(
        AddressData(
            street="Parkvägen",
            house_number="14",
            municipality="Taby",
        )
    )

    assert result.status == GeocodingStatus.RESOLVED
    assert result.coordinates is not None
    assert result.coordinates.latitude == 59.443
    assert result.coordinates.longitude == 18.068
    assert result.matched_address is not None
    assert result.matched_address.street == "Parkvägen"
    assert result.matched_address.house_number == "14"
    assert result.external_id == "12345"


def test_geocode_address_returns_not_found_for_missing_number() -> None:
    """Reject an incomplete address before making an HTTP request."""

    result = geocoding.geocode_address(
        AddressData(
            street="Parkvägen",
            municipality="Taby",
        )
    )

    assert result.status == GeocodingStatus.NOT_FOUND
    assert result.coordinates is None
    assert result.error_message is not None


def test_geocode_address_returns_not_found_for_empty_results(
    monkeypatch,
) -> None:
    """Return not found when the provider has no matching address."""

    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse([])

    monkeypatch.setattr(
        geocoding.httpx,
        "get",
        fake_get,
    )

    result = geocoding.geocode_address(
        AddressData(
            street="Unknown Street",
            house_number="999",
            municipality="Taby",
        )
    )

    assert result.status == GeocodingStatus.NOT_FOUND
    assert result.coordinates is None


def test_geocode_address_handles_provider_error(
    monkeypatch,
) -> None:
    """Convert HTTP failures into a structured error result."""

    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            payload=[],
            status_code=503,
        )

    monkeypatch.setattr(
        geocoding.httpx,
        "get",
        fake_get,
    )

    result = geocoding.geocode_address(
        AddressData(
            street="Parkvägen",
            house_number="14",
            municipality="Taby",
        )
    )

    assert result.status == GeocodingStatus.ERROR
    assert result.coordinates is None
    assert result.error_message is not None
    