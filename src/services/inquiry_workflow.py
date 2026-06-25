from src.schemas import CitizenInquiry, InquiryClassificationResult
from src.services.entity_extractor import extract_entities_with_llm
from src.services.inquiry_classifier import classify_inquiry_with_llm


def analyze_inquiry(
    inquiry: CitizenInquiry,
) -> InquiryClassificationResult:
    """Run the complete inquiry analysis workflow."""

    classification_result = classify_inquiry_with_llm(inquiry)

    enriched_inquiry = extract_entities_with_llm(
        classification_result.inquiry
    )

    return classification_result.model_copy(
        update={
            "inquiry": enriched_inquiry,
        }
    )
