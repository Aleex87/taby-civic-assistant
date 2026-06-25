from pyproj import Transformer

from src.schemas import GeoPoint


WGS84_CRS = "EPSG:4326"
TABY_MAP_CRS = "EPSG:3011"

_wgs84_to_taby = Transformer.from_crs(
    WGS84_CRS,
    TABY_MAP_CRS,
    always_xy=True,
)

_taby_to_wgs84 = Transformer.from_crs(
    TABY_MAP_CRS,
    WGS84_CRS,
    always_xy=True,
)


def wgs84_to_taby_map(
    point: GeoPoint,
) -> tuple[float, float]:
    """Transform WGS84 coordinates into the Taby map CRS."""

    easting, northing = _wgs84_to_taby.transform(
        point.longitude,
        point.latitude,
    )

    return float(easting), float(northing)


def taby_map_to_wgs84(
    easting: float,
    northing: float,
) -> GeoPoint:
    """Transform Taby map coordinates back into WGS84."""

    longitude, latitude = _taby_to_wgs84.transform(
        easting,
        northing,
    )

    return GeoPoint(
        latitude=float(latitude),
        longitude=float(longitude),
    )


def build_point_wkt(
    point: GeoPoint,
) -> str:
    """Build the projected WKT point expected by SpatialMap."""

    easting, northing = wgs84_to_taby_map(point)

    return f"POINT({easting:.8f} {northing:.8f})"
