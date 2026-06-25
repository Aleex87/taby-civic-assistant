import pytest

from src.schemas import GeoPoint
from src.services.coordinate_transformer import (
    build_point_wkt,
    taby_map_to_wgs84,
    wgs84_to_taby_map,
)


def test_coordinate_transformation_round_trip() -> None:
    """Preserve a geographic point through a CRS round trip."""

    original = GeoPoint(
        latitude=59.4249881,
        longitude=18.0982575,
    )

    easting, northing = wgs84_to_taby_map(original)

    restored = taby_map_to_wgs84(
        easting=easting,
        northing=northing,
    )

    assert restored.latitude == pytest.approx(
        original.latitude,
        abs=0.000001,
    )
    assert restored.longitude == pytest.approx(
        original.longitude,
        abs=0.000001,
    )


def test_build_point_wkt_uses_projected_coordinates() -> None:
    """Build a projected point accepted by the map query."""

    point = GeoPoint(
        latitude=59.4249881,
        longitude=18.0982575,
    )

    wkt = build_point_wkt(point)

    assert wkt.startswith("POINT(")
    assert wkt.endswith(")")
    assert "59.4249881" not in wkt
    assert "18.0982575" not in wkt