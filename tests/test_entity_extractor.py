from src.schemas import CitizenInquiry
from src.services import entity_extractor


def test_entity_extractor_updates_inquiry(
    monkeypatch,
) -> None:
    """Extract structured entities from a valid model response."""

    def fake_send_chat_message(**kwargs) -> str:
        return """
        {
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
        """

    monkeypatch.setattr(
        entity_extractor,
        "send_chat_message",
        fake_send_chat_message,
    )

    monkeypatch.setattr(
        entity_extractor,
        "get_openrouter_model",
        lambda: "openrouter/free",
    )

    inquiry = CitizenInquiry(
        original_text=(
            "Jag bor på Parkvägen 12. Min granne på Parkvägen 14 "
            "har byggt ett garage nära tomtgränsen."
        )
    )

    result = entity_extractor.extract_entities_with_llm(inquiry)

    assert result.entities.address.street == "Parkvägen"
    assert result.entities.address.house_number == "12"
    assert result.entities.address.municipality == "Taby"
    assert result.entities.subject == "garage"
    assert result.entities.neighbour_related is True
    assert result.entities.reported_address is not None
    assert result.entities.reported_address.street == "Parkvägen"
    assert result.entities.reported_address.house_number == "14"
    assert result.entities.missing_information == [
        "Exact distance from the property boundary"
    ]


def test_entity_extractor_returns_original_inquiry_on_failure(
    monkeypatch,
) -> None:
    """Return the original inquiry when entity extraction fails."""

    def fake_send_chat_message(**kwargs) -> str:
        raise RuntimeError("Simulated model failure")

    monkeypatch.setattr(
        entity_extractor,
        "send_chat_message",
        fake_send_chat_message,
    )

    monkeypatch.setattr(
        entity_extractor,
        "get_openrouter_model",
        lambda: "openrouter/free",
    )

    inquiry = CitizenInquiry(
        original_text="Jag vill veta vilka regler som gäller för avfall."
    )

    result = entity_extractor.extract_entities_with_llm(inquiry)

    assert result == inquiry
    assert result.entities.address.street is None
    assert result.entities.subject is None
    assert result.entities.neighbour_related is False
    