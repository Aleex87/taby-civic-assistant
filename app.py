import streamlit as st
from pydantic import ValidationError

from src.frontend.components import (
    render_inquiry_context,
    render_inquiry_form,
    render_page_header,
)
from src.schemas import CitizenInquiry
from src.services.inquiry_context import build_inquiry_context

st.set_page_config(
    page_title="Taby Civic Assistant",
    page_icon="🏛️",
    layout="wide",
)

render_page_header()

citizen_inquiry, submitted = render_inquiry_form()

if submitted:
    try:
        inquiry = CitizenInquiry(
            original_text=citizen_inquiry.strip(),
        )
    except ValidationError:
        st.warning("Please enter a citizen inquiry before continuing.")
    else:
        with st.spinner("Analyzing the inquiry..."):
            context = build_inquiry_context(inquiry)
        
        render_inquiry_context(context)
      
