from src.schemas import (
    DetailedPlanRecord,
    DetailedPlanType,
    PlanDocument,
)


PLAN_TYPE_BY_DISPLAY_NAME = {
    "detaljplan": DetailedPlanType.DETAILED_PLAN,
    "tilläggsplan": DetailedPlanType.SUPPLEMENTARY_PLAN,
    "fastighetsplan": DetailedPlanType.PROPERTY_PLAN,
}


def _normalize_label(label: str) -> str:
    """Normalize a provider column label for stable matching."""

    return " ".join(label.casefold().split())


def _extract_column_map(payload: dict) -> dict[str, str | None]:
    """Convert provider columns into a normalized label-value mapping."""

    columns = payload.get("columns", [])

    if not isinstance(columns, list):
        return {}

    values: dict[str, str | None] = {}

    for column in columns:
        if not isinstance(column, dict):
            continue

        label = column.get("label")

        if not isinstance(label, str) or not label.strip():
            continue

        value = column.get("value")

        if value is not None and not isinstance(value, str):
            value = str(value)

        values[_normalize_label(label)] = value

    return values


def _extract_documents(payload: dict) -> list[PlanDocument]:
    """Extract all hyperlink columns as official plan documents."""

    columns = payload.get("columns", [])

    if not isinstance(columns, list):
        return []

    documents: list[PlanDocument] = []

    for column in columns:
        if not isinstance(column, dict):
            continue

        value = column.get("value")
        column_format = column.get("format")

        if (
            column_format != "hyperlink"
            or not isinstance(value, str)
            or not value.strip()
        ):
            continue

        label = column.get("label")

        documents.append(
            PlanDocument(
                title=label if isinstance(label, str) else None,
                url=value.strip(),
            )
        )

    return documents


def _detect_plan_type(payload: dict) -> DetailedPlanType:
    """Map the provider display name to an internal plan type."""

    display_name = payload.get("targetdisplayname")

    if not isinstance(display_name, str):
        return DetailedPlanType.UNKNOWN

    return PLAN_TYPE_BY_DISPLAY_NAME.get(
        _normalize_label(display_name),
        DetailedPlanType.UNKNOWN,
    )


def parse_detailed_plan_record(
    payload: dict,
) -> DetailedPlanRecord:
    """Parse one SpatialMap result into a stable planning record."""

    values = _extract_column_map(payload)

    known_labels = {
        "plannummer",
        "plannamn",
        "beteckning",
        "plandokument",
    }

    additional_fields = {
        label: value
        for label, value in values.items()
        if label not in known_labels
    }

    return DetailedPlanRecord(
        plan_type=_detect_plan_type(payload),
        plan_number=values.get("plannummer"),
        plan_name=values.get("plannamn"),
        designation=values.get("beteckning"),
        datasource=(
            payload.get("datasource")
            if isinstance(payload.get("datasource"), str)
            else None
        ),
        documents=_extract_documents(payload),
        additional_fields=additional_fields,
    )
