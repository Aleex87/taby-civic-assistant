from src.schemas import CitizenInquiry, InquiryIntent
from src.services.inquiry_classifier import classify_inquiry_with_llm


def main() -> None:
    """Run a manual classification check with a Swedish inquiry."""

    inquiry = CitizenInquiry(
        original_text=(
            "Min granne har byggt ett garage mycket nära tomtgränsen. "
            "Jag vill veta om det är tillåtet."
        )
    )

    result = classify_inquiry_with_llm(inquiry)

    print("Classification result:")
    print(result.inquiry.model_dump_json(indent=2))

    print(f"Classification source: {result.source}")
def test_fallback_detects_permission_question(
    monkeypatch,
) -> None:
    """Detect a permission question with deterministic fallback rules."""

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
        original_text=(
            "Jag vill glasa in min balkong. Behöver jag bygglov?"
        )
    )

    result = inquiry_classifier.classify_inquiry_with_llm(inquiry)

    assert result.source == ClassificationSource.DETERMINISTIC_FALLBACK
    assert result.inquiry.domain == InquiryDomain.BUILDING_AND_PLANNING
    assert result.inquiry.intent == InquiryIntent.PERMISSION_QUESTION


def test_fallback_detects_possible_violation(
    monkeypatch,
) -> None:
    """Detect a possible violation with deterministic fallback rules."""

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
        original_text=(
            "Min granne har byggt ett garage utan bygglov."
        )
    )

    result = inquiry_classifier.classify_inquiry_with_llm(inquiry)

    assert result.source == ClassificationSource.DETERMINISTIC_FALLBACK
    assert result.inquiry.domain == InquiryDomain.BUILDING_AND_PLANNING
    assert (
        result.inquiry.intent
        == InquiryIntent.REPORT_POSSIBLE_VIOLATION
    )



if __name__ == "__main__":
    main()
