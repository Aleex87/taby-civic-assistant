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
        