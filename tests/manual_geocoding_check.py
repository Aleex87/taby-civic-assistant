from src.schemas import AddressData
from src.services.geocoding import geocode_address


def main() -> None:
    """Run one real geocoding request against Nominatim."""

    result = geocode_address(
        AddressData(
            street="Parkvägen",
            house_number="14",
            municipality="Taby",
        )
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

