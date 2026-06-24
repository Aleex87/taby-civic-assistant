import streamlit as st
from pydantic import ValidationError
from src.schemas import CitizenInquiry


st.set_page_config(
    page_title="Täby Civic Assistant",
    page_icon="🏛️",
    layout="wide",
)

st.title("Täby Civic Assistant")

st.caption(
    "AI-assisted municipal inquiry triage and case preparation."
)

st.divider()

with st.form("citizen_inquiry_form"):
    citizen_inquiry = st.text_area(
        "Citizen inquiry",
        height=220,
        placeholder=(
            "Example: I live at Examplevägen 12 in Täby and would like "
            "to know whether I can make changes to my property."
        ),
    )

    submitted = st.form_submit_button(
        "Analyze inquiry",
        type="primary",
    )

if submitted:
    try:
        inquiry = CitizenInquiry(
            original_text=citizen_inquiry.strip(),
        )
    except ValidationError:
        st.warning("Please enter a citizen inquiry before continuing.")
    else:
        st.success("The inquiry was received successfully.")

        st.subheader("Submitted inquiry")
        st.write(inquiry.original_text)
        st.subheader("Initial case state")
        st.json(inquiry.model_dump(mode="json"),
)