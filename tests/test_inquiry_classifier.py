from src.schemas import (
    CitizenInquiry,
    ClassificationSource,
    InquiryDomain,
)
from src.services import inquiry_classifier


def test_classification_uses_llm_response(
    monkeypatch,
) -> None:
    """Use a valid language model response when available."""

    def fake_send_chat_message(**kwargs) -> str:
        return """
        {
          "language": "sv",
          "domain": "neighbour_and_property",
          "requires_location": true,
          "requires_human_review": true
        }
        """

    monkeypatch.setattr(
        inquiry_classifier,
        "send_chat_message",
        fake_send_chat_message,
    )

    monkeypatch.setattr(
        inquiry_classifier,
        "get_openrouter_model",
        lambda: "openrouter/free",
    )

    inquiry = CitizenInquiry(
        original_text=(
            "Min granne har byggt ett garage nära tomtgränsen."
        )
    )

    result = inquiry_classifier.classify_inquiry_with_llm(inquiry)

    assert result.source == ClassificationSource.LLM
    assert result.inquiry.language == "sv"
    assert result.inquiry.domain == InquiryDomain.NEIGHBOUR_AND_PROPERTY
    assert result.inquiry.requires_location is True
    assert result.inquiry.requires_human_review is True


def test_classification_uses_fallback_when_llm_fails(
    monkeypatch,
) -> None:
    """Use deterministic rules when the language model fails."""

    def fake_send_chat_message(**kwargs) -> str:
        raise RuntimeError("Simulated model failure")

    monkeypatch.setattr(
        inquiry_classifier,
        "send_chat_message",
        fake_send_chat_message,
    )

    monkeypatch.setattr(
        inquiry_classifier,
        "get_openrouter_model",
        lambda: "openrouter/free",
    )

    inquiry = CitizenInquiry(
        original_text="Jag vill glasa in min balkong."
    )

    result = inquiry_classifier.classify_inquiry_with_llm(inquiry)

    assert result.source == ClassificationSource.DETERMINISTIC_FALLBACK
    assert result.inquiry.domain == InquiryDomain.BUILDING_AND_PLANNING
    