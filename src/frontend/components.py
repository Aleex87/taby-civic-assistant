import streamlit as st

from src.schemas import ClassificationSource, InquiryClassificationResult


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

    with st.expander("View structured case data"):
        st.json(
            result.model_dump(mode="json"),
        )
        