from src.schemas import (
    CitizenInquiry,
    ClassificationSource,
    InquiryClassificationResult,
    InquiryDomain,
    InquiryEntities,
    InquiryIntent,
)
from src.services import inquiry_workflow


def test_analyze_inquiry_combines_classification_and_entities(
    monkeypatch,
) -> None:
    """Combine classification and entity extraction results."""

    classified_inquiry = CitizenInquiry(
        original_text=(
            "Jag bor på Parkvägen 12 och vill veta om jag kan "
            "glasa in min balkong."
        ),
        language="sv",
        domain=InquiryDomain.BUILDING_AND_PLANNING,
        intent=InquiryIntent.PERMISSION_QUESTION,
        requires_location=True,
        requires_human_review=True,
    )

    classification_result = InquiryClassificationResult(
        inquiry=classified_inquiry,
        source=ClassificationSource.LLM,
    )

    extracted_entities = InquiryEntities(
        subject="balcony glazing",
        neighbour_related=False,
        missing_information=[
            "Property type",
            "Building heritage status",
        ],
    )

    def fake_classify_inquiry_with_llm(
        inquiry: CitizenInquiry,
    ) -> InquiryClassificationResult:
        return classification_result

    def fake_extract_entities_with_llm(
        inquiry: CitizenInquiry,
    ) -> CitizenInquiry:
        return inquiry.model_copy(
            update={
                "entities": extracted_entities,
            }
        )

    monkeypatch.setattr(
        inquiry_workflow,
        "classify_inquiry_with_llm",
        fake_classify_inquiry_with_llm,
    )

    monkeypatch.setattr(
        inquiry_workflow,
        "extract_entities_with_llm",
        fake_extract_entities_with_llm,
    )

    inquiry = CitizenInquiry(
        original_text=classified_inquiry.original_text,
    )

    result = inquiry_workflow.analyze_inquiry(inquiry)

    assert result.source == ClassificationSource.LLM
    assert result.inquiry.language == "sv"
    assert result.inquiry.domain == InquiryDomain.BUILDING_AND_PLANNING
    assert result.inquiry.intent == InquiryIntent.PERMISSION_QUESTION
    assert result.inquiry.entities.subject == "balcony glazing"
    assert result.inquiry.entities.neighbour_related is False
    assert result.inquiry.entities.missing_information == [
        "Property type",
        "Building heritage status",
    ]
    