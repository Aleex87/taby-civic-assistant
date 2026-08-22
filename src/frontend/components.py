from typing import Any

import streamlit as st

from src.schemas import (
    ClassificationSource,
    DetailedPlanResult,
    GeocodingResult,
    InquiryClassificationResult,
    InquiryContext,
)


def render_page_header() -> None:
    """Render the main application title and description."""

    st.title("Taby Civic Assistant")

    st.caption(
        "AI-assisted municipal inquiry triage and case preparation."
    )

    st.divider()


def render_inquiry_form() -> tuple[str, bool]:
    """Render the citizen inquiry form and return its values."""

    with st.form("citizen_inquiry_form"):
        citizen_inquiry = st.text_area(
            "Citizen inquiry",
            height=220,
            placeholder=(
                "Example: Jag vill veta om jag behöver bygglov för att "
                "glasa in min balkong."
            ),
        )

        submitted = st.form_submit_button(
            "Analyze inquiry",
            type="primary",
        )

    return citizen_inquiry, submitted


def _format_address(
    street: str | None,
    house_number: str | None,
    municipality: str | None,
) -> str:
    """Format an address from optional components."""

    address_parts = [
        part
        for part in (street, house_number)
        if part
    ]

    formatted_address = " ".join(address_parts)

    if municipality:
        if formatted_address:
            formatted_address = f"{formatted_address}, {municipality}"
        else:
            formatted_address = municipality

    return formatted_address or "Not identified"


def _format_confidence(
    confidence: float | None,
) -> str:
    """Format an optional confidence score."""

    if confidence is None:
        return "Unknown"

    return f"{confidence:.0%}"


def _format_optional_value(
    value: Any,
) -> str:
    """Format optional display values safely."""

    if value is None:
        return "Not returned"

    text = str(value).strip()

    return text or "Not returned"


def _get_primary_address_from_context(
    context: InquiryContext,
) -> str:
    """Return the best available primary address label."""

    if (
        context.primary_location is not None
        and context.primary_location.matched_address is not None
    ):
        address = context.primary_location.matched_address

        return _format_address(
            street=address.street,
            house_number=address.house_number,
            municipality=address.municipality,
        )

    entities = context.analysis.inquiry.entities

    return _format_address(
        street=entities.address.street,
        house_number=entities.address.house_number,
        municipality=entities.address.municipality,
    )


def _has_reported_property(
    context: InquiryContext,
) -> bool:
    """Check whether the inquiry contains a separate reported property."""

    reported_address = context.analysis.inquiry.entities.reported_address

    if reported_address is None:
        return False

    return bool(
        reported_address.street
        or reported_address.house_number
        or reported_address.municipality
    )


def _get_primary_plan_records(
    context: InquiryContext,
) -> list:
    """Return primary detailed-plan records if available."""

    if context.primary_detailed_plans is None:
        return []

    return context.primary_detailed_plans.records


def _get_main_plan_label(
    result: DetailedPlanResult | None,
) -> str:
    """Return a compact plan label for summaries."""

    if result is None or not result.records:
        return "Not found"

    labels = []

    for record in result.records:
        plan_number = record.plan_number
        designation = record.designation
        plan_name = record.plan_name

        if plan_number and designation:
            labels.append(f"{plan_number} / {designation}")
        elif plan_number:
            labels.append(plan_number)
        elif designation:
            labels.append(designation)
        elif plan_name:
            labels.append(plan_name)
        else:
            labels.append(record.plan_type.value)

    return ", ".join(labels)


def _render_citizen_answer(
    context: InquiryContext,
) -> None:
    """Render a citizen-facing preliminary answer."""

    inquiry = context.analysis.inquiry
    entities = inquiry.entities

    address = _get_primary_address_from_context(context)
    primary_plans = context.primary_detailed_plans
    plan_label = _get_main_plan_label(primary_plans)

    st.subheader("Preliminary answer")

    with st.container(border=True):
        st.markdown("### Answer to the citizen")

        st.write(
            "Based on the information identified so far, this case should "
            "be checked against Täby municipality's official rules before "
            "the work starts."
        )

        subject = entities.subject or "the described measure"

        st.write(
            f"For **{subject}**, the assistant has identified the address "
            f"as **{address}**."
        )

        if primary_plans is None:
            st.warning(
                "No detailed-plan lookup could be performed because the "
                "address did not produce valid coordinates."
            )
        elif primary_plans.error_message:
            st.warning(
                "The address was processed, but the detailed-plan lookup "
                "returned an error. A manual check in Täbykartan is needed."
            )
        elif primary_plans.records:
            st.success(
                f"The property appears to be connected to the following "
                f"planning record(s): **{plan_label}**."
            )
        else:
            st.info(
                "No detailed plan was found automatically for this location. "
                "A manual check may still be needed."
            )

        st.markdown("#### Preliminary guidance")

        st.write(
            "- This is not a final legal decision or building-permit "
            "decision."
        )
        st.write(
            "- The current version has identified the property location and "
            "the relevant planning records."
        )
        st.write(
            "- Before giving a definite answer, the assistant should read "
            "the relevant official municipal documents and cite them."
        )

        st.markdown("#### Recommended next step")

        if primary_plans is not None and primary_plans.records:
            st.write(
                "Open the official plan document below and continue with "
                "document-based retrieval before giving a final answer."
            )
        else:
            st.write(
                "Open Täbykartan and verify the property manually before "
                "giving a final answer."
            )

        st.link_button(
            "Open Täbykartan",
            "https://karta.taby.se/",
        )


def _render_key_case_summary(
    context: InquiryContext,
) -> None:
    """Render compact key case data before technical details."""

    st.subheader("Key case data")

    address = _get_primary_address_from_context(context)
    primary_location = context.primary_location
    primary_plans = context.primary_detailed_plans

    geocoding_status = (
        primary_location.status.value
        if primary_location is not None
        else "not_performed"
    )

    geocoding_confidence = (
        _format_confidence(primary_location.confidence)
        if primary_location is not None
        else "Unknown"
    )

    plan_status = (
        primary_plans.status.value
        if primary_plans is not None
        else "not_performed"
    )

    plan_label = _get_main_plan_label(primary_plans)

    summary_rows = [
        {
            "Item": "Primary address",
            "Value": address,
        },
        {
            "Item": "Geocoding",
            "Value": f"{geocoding_status} / {geocoding_confidence}",
        },
        {
            "Item": "Planning lookup",
            "Value": plan_status,
        },
        {
            "Item": "Planning record(s)",
            "Value": plan_label,
        },
        {
            "Item": "Human review required",
            "Value": (
                "Yes"
                if context.analysis.inquiry.requires_human_review
                else "No"
            ),
        },
    ]

    st.table(summary_rows)


def _render_plan_document_links(
    plan_number: str | None,
    documents,
) -> None:
    """Render official document links for one plan record."""

    if not documents:
        st.caption("No official plan document link was returned.")
        return

    for index, document in enumerate(documents, start=1):
        title = document.title or f"Document {index}"

        button_label = (
            f"Open {title}"
            if plan_number is None
            else f"Open {plan_number} {title}"
        )

        st.link_button(
            button_label,
            document.url,
        )


def _render_compact_plan_records(
    result: DetailedPlanResult | None,
) -> None:
    """Render plan records in a compact citizen-friendly way."""

    if result is None:
        st.info(
            "No detailed-plan lookup was performed because no valid "
            "coordinates were available."
        )
        return

    if result.error_message:
        st.error(result.error_message)
        st.link_button(
            "Open Täbykartan for manual check",
            "https://karta.taby.se/",
        )
        return

    if not result.records:
        st.warning(
            "No applicable detailed plan was found automatically for this "
            "location."
        )
        st.link_button(
            "Open Täbykartan for manual check",
            "https://karta.taby.se/",
        )
        return

    if len(result.records) == 1:
        st.success("One planning record was found for this location.")
    else:
        st.warning(
            "Multiple planning records were found. Keep all records until "
            "a municipal officer or the document retrieval step confirms "
            "which one is relevant."
        )

    for index, record in enumerate(result.records, start=1):
        plan_number = _format_optional_value(record.plan_number)
        designation = _format_optional_value(record.designation)
        plan_name = _format_optional_value(record.plan_name)
        plan_type = record.plan_type.value

        with st.container(border=True):
            st.markdown(f"### Planning record {index}")

            st.markdown(
                f"""
                **Plan number:** {plan_number}  
                **Designation:** {designation}  
                **Plan name:** {plan_name}  
                **Plan type:** {plan_type}
                """
            )

            _render_plan_document_links(
                plan_number=record.plan_number,
                documents=record.documents,
            )

            with st.expander("Technical planning fields"):
                st.write(f"Datasource: {record.datasource or 'Not returned'}")
                st.json(record.additional_fields)


def _render_planning_information(
    context: InquiryContext,
) -> None:
    """Render planning information with primary focus."""

    st.subheader("Planning information")

    st.markdown("### Primary property")

    _render_compact_plan_records(context.primary_detailed_plans)

    if _has_reported_property(context):
        st.markdown("### Reported property")
        _render_compact_plan_records(context.reported_detailed_plans)


def _render_geocoding_result(
    title: str,
    result: GeocodingResult | None,
) -> None:
    """Render one structured geocoding result."""

    st.write(f"**{title}**")

    if result is None:
        st.write("No complete address was available for geocoding.")
        return

    if result.matched_address is not None:
        matched_address = _format_address(
            street=result.matched_address.street,
            house_number=result.matched_address.house_number,
            municipality=result.matched_address.municipality,
        )
    else:
        matched_address = "Not identified"

    summary_rows = [
        {
            "Item": "Geocoding status",
            "Value": result.status.value,
        },
        {
            "Item": "Confidence",
            "Value": _format_confidence(result.confidence),
        },
        {
            "Item": "Provider",
            "Value": result.provider,
        },
        {
            "Item": "Matched address",
            "Value": matched_address,
        },
    ]

    if result.coordinates is not None:
        coordinates = result.coordinates

        summary_rows.append(
            {
                "Item": "Coordinates",
                "Value": (
                    f"{coordinates.latitude:.6f}, "
                    f"{coordinates.longitude:.6f}"
                ),
            }
        )

    st.table(summary_rows)

    if result.coordinates is not None:
        coordinates = result.coordinates

        st.map(
            [
                {
                    "latitude": coordinates.latitude,
                    "longitude": coordinates.longitude,
                }
            ],
            latitude="latitude",
            longitude="longitude",
            zoom=15,
        )

    if result.raw_label:
        st.caption(f"Provider label: {result.raw_label}")

    if result.error_message:
        st.warning(result.error_message)


def _render_location_section(
    context: InquiryContext,
) -> None:
    """Render geocoding and map information."""

    st.subheader("Location and map")

    if _has_reported_property(context):
        location_col1, location_col2 = st.columns(2)

        with location_col1:
            _render_geocoding_result(
                title="Primary property",
                result=context.primary_location,
            )

        with location_col2:
            _render_geocoding_result(
                title="Reported property",
                result=context.reported_location,
            )
    else:
        _render_geocoding_result(
            title="Primary property",
            result=context.primary_location,
        )


def render_classification_result(
    result: InquiryClassificationResult,
) -> None:
    """Render the structured classification result."""

    st.subheader("Classification")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Language**")
        st.write(result.inquiry.language)

        st.write("**Domain**")
        st.write(result.inquiry.domain.value)

    with col2:
        st.write("**Intent**")
        st.write(result.inquiry.intent.value)

        st.write("**Location required**")
        st.write("Yes" if result.inquiry.requires_location else "No")

    with col3:
        st.write("**Human review required**")
        st.write(
            "Yes"
            if result.inquiry.requires_human_review
            else "No"
        )

        st.write("**Classification source**")
        st.write(result.source.value)

    st.subheader("Extracted case information")

    entities = result.inquiry.entities

    entity_col1, entity_col2 = st.columns(2)

    with entity_col1:
        st.write("**Primary address**")

        primary_address = _format_address(
            street=entities.address.street,
            house_number=entities.address.house_number,
            municipality=entities.address.municipality,
        )

        st.write(primary_address)

        st.write("**Subject**")
        st.write(entities.subject or "Not identified")

    with entity_col2:
        st.write("**Neighbour related**")
        st.write("Yes" if entities.neighbour_related else "No")

        st.write("**Reported property address**")

        if entities.reported_address is not None:
            reported_address = _format_address(
                street=entities.reported_address.street,
                house_number=entities.reported_address.house_number,
                municipality=entities.reported_address.municipality,
            )
        else:
            reported_address = "Not identified"

        st.write(reported_address)

    st.write("**Missing information**")

    if entities.missing_information:
        for item in entities.missing_information:
            st.write(f"- {item}")
    else:
        st.write("No missing information identified.")

    if result.source == ClassificationSource.LLM:
        st.info("The inquiry was classified by the language model.")
    else:
        st.warning(
            "The language model was unavailable or returned an invalid "
            "response. The deterministic fallback was used."
        )


def _render_official_sources(
    context: InquiryContext,
) -> None:
    """Render official municipal source snippets."""

    st.subheader("Official municipal sources")

    if context.retrieval is None:
        st.info("No source retrieval was performed.")
    elif not context.retrieval.sources:
        st.warning(
            "No official municipal source could be retrieved."
        )

        if context.retrieval.error_message:
            st.caption(context.retrieval.error_message)
    else:
        for source in context.retrieval.sources:
            with st.container(border=True):
                st.markdown(f"### {source.title}")
                st.write(source.excerpt or "No excerpt available.")
                st.link_button(
                    "Open official source",
                    source.url,
                )

                if source.municipality:
                    st.caption(
                        f"Municipality: {source.municipality}"
                    )


def render_inquiry_context(
    context: InquiryContext,
) -> None:
    """Render citizen answer, case data, and technical context."""

    st.success("The inquiry was analyzed successfully.")

    _render_citizen_answer(context)

    _render_key_case_summary(context)

    _render_planning_information(context)

    with st.expander("Location map and geocoding details"):
        _render_location_section(context)

    _render_official_sources(context)

    with st.expander("Technical details for municipal officer"):
        st.subheader("Submitted inquiry")
        st.write(context.analysis.inquiry.original_text)

        render_classification_result(context.analysis)

        st.subheader("Complete structured context")
        st.json(
            context.model_dump(mode="json"),
        )
        