import time
from uuid import uuid4

import httpx

from src.schemas import (
    DetailedPlanResult,
    DetailedPlanStatus,
    DetailedPlanType,
    GeoPoint,
)
from src.services.coordinate_transformer import build_point_wkt
from src.services.detailed_plan_parser import (
    parse_detailed_plan_record,
)


SPATIALMAP_URL = "https://karta.taby.se/spatialmap"
PORTAL_URL = (
    "https://karta.taby.se/"
    "rest/profile/default/tools/html/client/portal"
)
PROVIDER_NAME = "Taby SpatialMap"

PROFILE_NAME = "csm_standard_profile"

PLAN_LAYERS = [
    "theme-bakgrund",
    "theme-bakgrund_sjoar",
    "theme-bg__vagmitt_gatunamn_ihopbakad",
    "theme-td_bal_bal_byggnad_y",
    "theme-td_baskarta_ml_markdetaljer",
    "theme-td_baskarta_ma_markanvandningyta_y",
    "theme-td_baskarta_td_vagkanter",
    "theme-gisdata_bg_kommundelsnamn",
    "theme-td_drk",
    "theme-td_detaljplan_dp_tillaggsplan",
    "theme-td_detaljplan_dp_fastighetsplan",
    "theme-td_detaljplan_dp_detaljplan",
    "userpoint",
    "userline",
    "userpolygon",
    "selectorpoint",
    "selectorline",
    "selectorpolygon",
    "selectorbufferzone",
]

SUPPORTED_TARGET_NAMES = {
    "detaljplan",
    "tilläggsplan",
    "fastighetsplan",
}

MAX_STATUS_ATTEMPTS = 10
STATUS_DELAY_SECONDS = 0.5

REQUEST_HEADERS = {
    "User-Agent": (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "sv,en",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://karta.taby.se",
    "Referer": "https://karta.taby.se/spatialmap",
    "X-Requested-With": "XMLHttpRequest",
}


def _post_json(
    client: httpx.Client,
    page: str,
    data: dict[str, str],
) -> dict:
    """Send one SpatialMap request and return its JSON payload."""

    payload = {
        **data,
        "page": page,
        "outputformat": "json",
        "jdaf.error.contenttype": "json",
    }

    response = client.post(
        SPATIALMAP_URL,
        params={"page": page},
        data=payload,
    )
    response.raise_for_status()

    result = response.json()

    if not isinstance(result, dict):
        raise ValueError(
            "SpatialMap returned an unexpected response format."
        )

    return result


def _extract_status_rows(payload: dict) -> list[dict]:
    """Extract query-status rows from the nested SpatialMap response."""

    outer_rows = payload.get("row")

    if not isinstance(outer_rows, list):
        return []

    result_rows: list[dict] = []

    for outer_row in outer_rows:
        if not isinstance(outer_row, dict):
            continue

        nested_rows = outer_row.get("row")

        if not isinstance(nested_rows, list):
            continue

        for nested_row in nested_rows:
            if isinstance(nested_row, dict):
                result_rows.append(nested_row)

    return result_rows


def _is_supported_plan_row(row: dict) -> bool:
    """Check whether a status row represents a supported plan type."""

    target_name = row.get("targetname")

    if not isinstance(target_name, str):
        return False

    return target_name.casefold() in SUPPORTED_TARGET_NAMES


def _all_plan_rows_ready(rows: list[dict]) -> bool:
    """Check whether all returned planning rows completed."""

    plan_rows = [
        row
        for row in rows
        if _is_supported_plan_row(row)
    ]

    if not plan_rows:
        return False

    return all(
        row.get("status") == "ready"
        for row in plan_rows
    )


def _get_ready_plan_rows(
    client: httpx.Client,
) -> list[dict]:
    """Poll SpatialMap until the planning query is complete."""

    latest_rows: list[dict] = []

    for attempt in range(MAX_STATUS_ATTEMPTS):
        payload = _post_json(
            client=client,
            page="spatialquery-get-query-status",
            data={},
        )

        latest_rows = _extract_status_rows(payload)

        if _all_plan_rows_ready(latest_rows):
            return [
                row
                for row in latest_rows
                if _is_supported_plan_row(row)
            ]

        if attempt < MAX_STATUS_ATTEMPTS - 1:
            time.sleep(STATUS_DELAY_SECONDS)

    raise TimeoutError(
        "SpatialMap did not complete the detailed-plan query in time."
    )


def _check_query_pending(
    client: httpx.Client,
) -> None:
    """Check whether a SpatialMap query is already pending."""

    _post_json(
        client=client,
        page="spatialquery-is-query-pending",
        data={},
    )


def _delete_dynamic_layer(
    client: httpx.Client,
    layer: str,
    datasource: str,
) -> None:
    """Delete one temporary SpatialMap dynamic layer."""

    _post_json(
        client=client,
        page="dynamiclayer-delete",
        data={
            "dynamiclayer": layer,
            "dynamicdatasource": datasource,
        },
    )


def _create_user_point_layer(
    client: httpx.Client,
    point: GeoPoint,
) -> None:
    """Create the temporary point layer used by SpatialMap."""

    point_wkt = build_point_wkt(point)

    _post_json(
        client=client,
        page="minimap2.add-dynamiclayer-from-singlerow-expr",
        data={
            "dynamiclayer": "userpoint",
            "dynamicdatasource": "userpoint",
            "row1": f"'{point_wkt}'",
            "append": "false",
        },
    )

def _initialize_session(
    client: httpx.Client,
) -> None:
    """Initialize a SpatialMap session and load the active profile."""

    response = client.post(
        SPATIALMAP_URL,
        data={
            "page": "get-profile-and-tools",
            "outputformat": "json",
            "jdaf.error.contenttype": "json",
        },
    )
    response.raise_for_status()

    result = response.json()

    if not isinstance(result, dict):
        raise ValueError(
            "SpatialMap returned an unexpected session response."
        )

def _initialize_spatial_query(
    client: httpx.Client,
    point: GeoPoint,
) -> None:
    """Prepare the temporary SpatialMap layers for a point query."""

    _check_query_pending(client)

    _delete_dynamic_layer(
        client=client,
        layer="userpoint,userline,userpolygon",
        datasource="userdatasource",
    )

    _create_user_point_layer(
        client=client,
        point=point,
    )

    _delete_dynamic_layer(
        client=client,
        layer="userline",
        datasource="userline",
    )

    _delete_dynamic_layer(
        client=client,
        layer="userpolygon",
        datasource="userpolygon",
    )

    _check_query_pending(client)


def _start_plan_query(
    client: httpx.Client,
    point: GeoPoint,
    session_id: str,
) -> None:
    """Start a SpatialMap query for planning layers at one point."""

    _post_json(
        client=client,
        page="spatialquery-async",
        data={
            "profilequery": "info",
            "wkt": build_point_wkt(point),
            "layers": " ".join(PLAN_LAYERS),
            "distance": "5.194521194311368",
            "currentscale": "1963.27967443237",
            "profile": PROFILE_NAME,
            "sessionid": session_id,
            "userthemes": "true",
            "filterconstruct": "true",
        },
    )

def _get_formatted_result(
    client: httpx.Client,
    position: str,
) -> dict:
    """Retrieve one formatted SpatialMap query result."""

    return _post_json(
        client=client,
        page="spatialquery-get-result-formatted",
        data={
            "position": position,
            "jsonformat": "compact",
        },
    )

def _record_identity(record) -> tuple:
    """Build a stable identity used to remove duplicate records."""

    return (
        record.plan_type,
        record.plan_number,
        record.designation,
        record.datasource,
    )

def resolve_detailed_plans(
    point: GeoPoint,
) -> DetailedPlanResult:
    """Resolve all planning records applicable to a geographic point."""

    timeout = httpx.Timeout(
        connect=5.0,
        read=15.0,
        write=10.0,
        pool=5.0,
    )

    session_id = f"{{{str(uuid4()).upper()}}}"

    headers = {
        **REQUEST_HEADERS,
        "Session-Id": session_id,
    }

    try:
        with httpx.Client(
            headers=headers,
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            portal_response = client.get(PORTAL_URL)
            portal_response.raise_for_status()
            
            _initialize_session(client)

            _initialize_spatial_query(
                client=client,
                point=point,
            )

            _start_plan_query(
                client=client,
                point=point,
                session_id=session_id,
            )

            status_rows = _get_ready_plan_rows(client)

            records = []
            seen_records = set()

            for row in status_rows:
                row_count = row.get("rowcount")

                try:
                    count = int(row_count)
                except (TypeError, ValueError):
                    count = 0

                if count <= 0:
                    continue

                formatted_position = row.get("formattedpos")

                try:
                    starting_position = int(formatted_position)
                except (TypeError, ValueError):
                    continue

                for offset in range(count):
                    position = str(starting_position + offset)

                    payload = _get_formatted_result(
                        client=client,
                        position=position,
                    )

                    record = parse_detailed_plan_record(payload)
                    identity = _record_identity(record)

                    if identity in seen_records:
                        continue

                    seen_records.add(identity)
                    records.append(record)

    except (
        httpx.HTTPError,
        TimeoutError,
        ValueError,
    ) as exc:
        return DetailedPlanResult(
            status=DetailedPlanStatus.ERROR,
            query_point=point,
            records=[],
            provider=PROVIDER_NAME,
            confidence=None,
            error_message=str(exc),
        )

    if not records:
        return DetailedPlanResult(
            status=DetailedPlanStatus.NOT_FOUND,
            query_point=point,
            records=[],
            provider=PROVIDER_NAME,
            confidence=0.0,
            error_message=None,
        )

    status = (
        DetailedPlanStatus.RESOLVED
        if len(records) == 1
        else DetailedPlanStatus.MULTIPLE_MATCHES
    )

    has_unknown_type = any(
        record.plan_type == DetailedPlanType.UNKNOWN
        for record in records
    )

    return DetailedPlanResult(
        status=status,
        query_point=point,
        records=records,
        provider=PROVIDER_NAME,
        confidence=0.8 if has_unknown_type else 1.0,
        error_message=None,
    )
