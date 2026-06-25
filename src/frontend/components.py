
import streamlit as st

from src.schemas import (
    ClassificationSource,
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Geocoding status",
            value=result.status.value,
        )

    with col2:
        confidence = (
            f"{result.confidence:.0%}"
            if result.confidence is not None
            else "Unknown"
        )

        st.metric(
            label="Confidence",
            value=confidence,
        )

    with col3:
        st.metric(
            label="Provider",
            value=result.provider,
        )

    st.write(f"**Matched address:** {matched_address}")

    if result.coordinates is not None:
        coordinates = result.coordinates

        st.write(
            f"**Coordinates:** "
            f"{coordinates.latitude:.6f}, "
            f"{coordinates.longitude:.6f}"
        )

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


def render_classification_result(
    result: InquiryClassificationResult,
) -> None:
    """Render the structured classification result."""

    st.success("The inquiry was analyzed successfully.")

    st.subheader("Submitted inquiry")
    st.write(result.inquiry.original_text)

    st.subheader("Classification")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Language",
            value=result.inquiry.language,
        )

        st.metric(
            label="Domain",
            value=result.inquiry.domain.value,
        )

    with col2:
        st.metric(
            label="Intent",
            value=result.inquiry.intent.value,
        )

        st.metric(
            label="Location required",
            value="Yes" if result.inquiry.requires_location else "No",
        )

    with col3:
        st.metric(
            label="Human review required",
            value=(
                "Yes"
                if result.inquiry.requires_human_review
                else "No"
            ),
        )

        st.metric(
            label="Classification source",
            value=result.source.value,
        )

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


def render_inquiry_context(
    context: InquiryContext,
) -> None:
    """Render analysis, location resolution, and official sources."""

    render_classification_result(context.analysis)

    st.subheader("Location resolution")

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

    with st.expander("View complete structured context"):
        st.json(
            context.model_dump(mode="json"),
        )
