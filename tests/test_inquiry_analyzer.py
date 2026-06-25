from src.schemas import (
    CitizenInquiry,
    ClassificationSource,
    InquiryDomain,
    InquiryIntent,
)
from src.services import inquiry_analyzer


def test_analyzer_returns_complete_llm_analysis(
    monkeypatch,
) -> None:
    """Return classification and entities from one model response."""

    def fake_send_chat_message(**kwargs) -> str:
        return """
        {
          "language": "sv",
          "domain": "neighbour_and_property",
          "intent": "report_possible_violation",
          "requires_location": true,
          "requires_human_review": true,
          "entities": {
            "address": {
              "street": "Parkvägen",
              "house_number": "12",
              "municipality": "Taby"
            },
            "subject": "garage",
            "neighbour_related": true,
            "reported_address": {
              "street": "Parkvägen",
              "house_number": "14",
              "municipality": "Taby"
            },
            "missing_information": [
              "Exact distance from the property boundary"
            ]
          }
        }
        """

    monkeypatch.setattr(
        inquiry_analyzer,
        "send_chat_message",
        fake_send_chat_message,
    )

    monkeypatch.setattr(
        inquiry_analyzer,
        "get_openrouter_model",
        lambda: "openrouter/free",
    )

    inquiry = CitizenInquiry(
        original_text=(
            "Jag bor på Parkvägen 12 och min granne på Parkvägen 14 "
            "har byggt ett garage nära tomtgränsen."
        )
    )

    result = inquiry_analyzer.analyze_inquiry_with_llm(inquiry)

    assert result.source == ClassificationSource.LLM
    assert result.inquiry.language == "sv"
    assert result.inquiry.domain == InquiryDomain.NEIGHBOUR_AND_PROPERTY
    assert result.inquiry.intent == InquiryIntent.REPORT_POSSIBLE_VIOLATION
    assert result.inquiry.requires_location is True
    assert result.inquiry.requires_human_review is True

    assert result.inquiry.entities.address.street == "Parkvägen"
    assert result.inquiry.entities.address.house_number == "12"
    assert result.inquiry.entities.address.municipality == "Taby"

    assert result.inquiry.entities.subject == "garage"
    assert result.inquiry.entities.neighbour_related is True

    assert result.inquiry.entities.reported_address is not None
    assert result.inquiry.entities.reported_address.street == "Parkvägen"
    assert result.inquiry.entities.reported_address.house_number == "14"

    assert result.inquiry.entities.missing_information == [
        "Exact distance from the property boundary"
    ]


def test_analyzer_uses_fallback_when_llm_fails(
    monkeypatch,
) -> None:
    """Use deterministic classification when the model request fails."""

    def fake_send_chat_message(**kwargs) -> str:
        raise RuntimeError("Simulated model failure")

    monkeypatch.setattr(
        inquiry_analyzer,
        "send_chat_message",
        fake_send_chat_message,
    )

    monkeypatch.setattr(
        inquiry_analyzer,
        "get_openrouter_model",
        lambda: "openrouter/free",
    )

    inquiry = CitizenInquiry(
        original_text=(
            "Jag vill glasa in min balkong. Behöver jag bygglov?"
        )
    )

    result = inquiry_analyzer.analyze_inquiry_with_llm(inquiry)

    assert result.source == ClassificationSource.DETERMINISTIC_FALLBACK
    assert result.inquiry.domain == InquiryDomain.BUILDING_AND_PLANNING
    assert result.inquiry.intent == InquiryIntent.PERMISSION_QUESTION

    assert result.inquiry.entities.subject is None
    assert result.inquiry.entities.address.street is None
    