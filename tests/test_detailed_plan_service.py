from src.schemas import (
    DetailedPlanStatus,
    DetailedPlanType,
    GeoPoint,
)
from src.services import detailed_plan_service


class FakeResponse:
    """Minimal HTTP response used by SpatialMap tests."""

    def __init__(
        self,
        payload: dict,
        status_code: int = 200,
    ) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("Simulated HTTP failure")

    def json(self) -> dict:
        return self._payload


class FakeClient:
    """Fake session preserving the SpatialMap request sequence."""

    def __init__(self, *args, **kwargs) -> None:
        self.post_calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def get(self, url: str) -> FakeResponse:
        return FakeResponse({})

    def post(
        self,
        url: str,
        params: dict,
        data: dict,
    ) -> FakeResponse:
        self.post_calls.append(
            {
                "url": url,
                "params": params,
                "data": data,
            }
        )

        page = params["page"]

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
                                    "rowcount": "1",
                                    "formattedpos": "0",
                                },
                                {
                                    "targetname": "Tilläggsplan",
                                    "status": "ready",
                                    "rowcount": "1",
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
                    {
                        "targetdisplayname": "Detaljplan",
                        "datasource": (
                            "ds_td_detaljplan_dp_plan_y_detaljplan"
                        ),
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
                    }
                )

            if position == "1":
                return FakeResponse(
                    {
                        "targetdisplayname": "Tilläggsplan",
                        "datasource": (
                            "ds_td_detaljplan_dp_plan_y_tillaggsplan"
                        ),
                        "columns": [
                            {
                                "label": "Plannummer",
                                "value": "T12",
                            },
                            {
                                "label": "Beteckning",
                                "value": "0160-T12",
                            },
                            {
                                "label": "Plandokument",
                                "value": (
                                    "https://example.com/"
                                    "T12-planhandlingar.pdf"
                                ),
                                "format": "hyperlink",
                            },
                        ],
                    }
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

    assert (
        second_record.plan_type
        == DetailedPlanType.SUPPLEMENTARY_PLAN
    )
    assert second_record.plan_number == "T12"
    assert second_record.designation == "0160-T12"


def test_resolve_detailed_plans_returns_not_found(
    monkeypatch,
) -> None:
    """Return not found when all supported layers have zero rows."""

    class EmptyResultClient(FakeClient):
        def post(
            self,
            url: str,
            params: dict,
            data: dict,
        ) -> FakeResponse:
            self.post_calls.append(
                {
                    "url": url,
                    "params": params,
                    "data": data,
                }
            )

            page = params["page"]

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
                                        "formattedpos": "0",
                                    },
                                    {
                                        "targetname": "Fastighetsplan",
                                        "status": "ready",
                                        "rowcount": "0",
                                        "formattedpos": "0",
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
