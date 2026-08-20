from src.schemas import (
    DetailedPlanStatus,
    DetailedPlanType,
    GeoPoint,
)
from src.services import detailed_plan_service


SESSION_HTML = (
    'sessionStorage.setItem('
    '"spatialmapSessionId", '
    '"{11111111-1111-1111-1111-111111111111}"'
    ");"
)


class FakeResponse:
    """Minimal HTTP response used by SpatialMap tests."""

    def __init__(
        self,
        payload: dict | list,
        status_code: int = 200,
        text: str | None = None,
    ) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text or ""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("Simulated HTTP failure")

    def json(self):
        return self._payload


class FakeClient:
    """Fake session preserving the SpatialMap request sequence."""

    def __init__(
        self,
        *args,
        headers: dict | None = None,
        **kwargs,
    ) -> None:
        self.post_calls: list[dict] = []
        self.headers = dict(headers or {})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def get(self, url: str) -> FakeResponse:
        return FakeResponse(
            {},
            text=SESSION_HTML,
        )

    def post(
        self,
        url: str,
        params: dict | None = None,
        data: dict | None = None,
    ) -> FakeResponse:
        params = params or {}
        data = data or {}

        self.post_calls.append(
            {
                "url": url,
                "params": params,
                "data": data,
            }
        )

        page = params.get("page") or data.get("page")

        if page == "get-profile-and-tools":
            return FakeResponse(
                {
                    "profile": {
                        "name": "csm_standard_profile",
                    }
                }
            )

        if page == "spatialquery-is-query-pending":
            return FakeResponse(
                {
                    "pending": False,
                }
            )

        if page == "dynamiclayer-delete":
            return FakeResponse(
                {
                    "status": "deleted",
                }
            )

        if page == "minimap2.add-dynamiclayer-from-singlerow-expr":
            return FakeResponse(
                {
                    "status": "created",
                }
            )

        if page == "spatialquery-async":
            return FakeResponse(
                {
                    "status": "started",
                }
            )

        if page == "spatialquery-get-query-status":
            return FakeResponse(
                {
                    "row": [
                        {
                            "row": [
                                {
                                    "targetname": "Detaljplan",
                                    "status": "ready",
                                    "rowcount": "2",
                                    "formattedpos": "0",
                                },
                                {
                                    "targetname": "Tilläggsplan",
                                    "status": "ready",
                                    "rowcount": "0",
                                    "formattedpos": "1",
                                },
                                {
                                    "targetname": "Fastighetsplan",
                                    "status": "ready",
                                    "rowcount": "0",
                                    "formattedpos": "2",
                                },
                            ]
                        }
                    ]
                }
            )

        if page == "spatialquery-get-result-formatted":
            position = data["position"]

            if position == "0":
                return FakeResponse(
                    [
                        {
                            "targetname": "Detaljplan",
                        },
                        {
                            "targetdisplayname": "Detaljplan",
                        },
                        {
                            "datasource": (
                                "ds_td_detaljplan_dp_plan_y_detaljplan"
                            ),
                        },
                        {
                            "status": "ready",
                        },
                        {
                            "count": 2,
                        },
                        {
                            "columns": [
                                {
                                    "label": "Plannummer",
                                    "value": "S59",
                                },
                                {
                                    "label": "Plannamn",
                                    "value": None,
                                },
                                {
                                    "label": "Beteckning",
                                    "value": "0160-S59",
                                },
                                {
                                    "label": "Plandokument",
                                    "value": (
                                        "https://example.com/"
                                        "S59-planhandlingar.pdf"
                                    ),
                                    "format": "hyperlink",
                                },
                            ],
                        },
                        {
                            "columns": [
                                {
                                    "label": "Plannummer",
                                    "value": "S60",
                                },
                                {
                                    "label": "Plannamn",
                                    "value": None,
                                },
                                {
                                    "label": "Beteckning",
                                    "value": "0160-S60",
                                },
                                {
                                    "label": "Plandokument",
                                    "value": (
                                        "https://example.com/"
                                        "S60-planhandlingar.pdf"
                                    ),
                                    "format": "hyperlink",
                                },
                            ],
                        },
                    ]
                )

            raise AssertionError(
                f"Unexpected formatted position: {position}"
            )

        raise AssertionError(f"Unexpected page: {page}")


def test_resolve_detailed_plans_returns_all_records(
    monkeypatch,
) -> None:
    """Resolve all plan records returned for one geographic point."""

    monkeypatch.setattr(
        detailed_plan_service.httpx,
        "Client",
        FakeClient,
    )

    result = detailed_plan_service.resolve_detailed_plans(
        GeoPoint(
            latitude=59.4249881,
            longitude=18.0982575,
        )
    )

    assert result.status == DetailedPlanStatus.MULTIPLE_MATCHES
    assert result.provider == detailed_plan_service.PROVIDER_NAME
    assert len(result.records) == 2

    first_record = result.records[0]
    second_record = result.records[1]

    assert first_record.plan_type == DetailedPlanType.DETAILED_PLAN
    assert first_record.plan_number == "S59"
    assert first_record.designation == "0160-S59"
    assert len(first_record.documents) == 1

    assert second_record.plan_type == DetailedPlanType.DETAILED_PLAN
    assert second_record.plan_number == "S60"
    assert second_record.designation == "0160-S60"
    assert len(second_record.documents) == 1


def test_resolve_detailed_plans_returns_not_found(
    monkeypatch,
) -> None:
    """Return not found when all supported layers have zero rows."""

    class EmptyResultClient(FakeClient):
        def post(
            self,
            url: str,
            params: dict | None = None,
            data: dict | None = None,
        ) -> FakeResponse:
            params = params or {}
            data = data or {}

            self.post_calls.append(
                {
                    "url": url,
                    "params": params,
                    "data": data,
                }
            )

            page = params.get("page") or data.get("page")

            if page == "get-profile-and-tools":
                return FakeResponse(
                    {
                        "profile": {
                            "name": "csm_standard_profile",
                        }
                    }
                )

            if page == "spatialquery-is-query-pending":
                return FakeResponse(
                    {
                        "pending": False,
                    }
                )

            if page == "dynamiclayer-delete":
                return FakeResponse(
                    {
                        "status": "deleted",
                    }
                )

            if page == "minimap2.add-dynamiclayer-from-singlerow-expr":
                return FakeResponse(
                    {
                        "status": "created",
                    }
                )

            if page == "spatialquery-async":
                return FakeResponse(
                    {
                        "status": "started",
                    }
                )

            if page == "spatialquery-get-query-status":
                return FakeResponse(
                    {
                        "row": [
                            {
                                "row": [
                                    {
                                        "targetname": "Detaljplan",
                                        "status": "ready",
                                        "rowcount": "0",
                                        "formattedpos": "0",
                                    },
                                    {
                                        "targetname": "Tilläggsplan",
                                        "status": "ready",
                                        "rowcount": "0",
                                        "formattedpos": "1",
                                    },
                                    {
                                        "targetname": "Fastighetsplan",
                                        "status": "ready",
                                        "rowcount": "0",
                                        "formattedpos": "2",
                                    },
                                ]
                            }
                        ]
                    }
                )

            raise AssertionError(f"Unexpected page: {page}")

    monkeypatch.setattr(
        detailed_plan_service.httpx,
        "Client",
        EmptyResultClient,
    )

    result = detailed_plan_service.resolve_detailed_plans(
        GeoPoint(
            latitude=59.4249881,
            longitude=18.0982575,
        )
    )

    assert result.status == DetailedPlanStatus.NOT_FOUND
    assert result.records == []
    