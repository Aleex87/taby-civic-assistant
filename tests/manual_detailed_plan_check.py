from src.schemas import GeoPoint
from src.services.detailed_plan_service import resolve_detailed_plans


def main() -> None:
    """Run one real detailed-plan lookup against Taby SpatialMap."""

    point = GeoPoint(
        latitude=59.4249881,
        longitude=18.0982575,
    )

    result = resolve_detailed_plans(point)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
    