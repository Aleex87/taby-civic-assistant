from src.schemas import CitizenInquiry
from src.services.inquiry_analyzer import analyze_inquiry_with_llm


def main() -> None:
    """Run a real inquiry analysis through OpenRouter."""

    inquiry = CitizenInquiry(
        original_text=(
            "Jag bor på Parkvägen 12 i Taby. "
            "Min granne på Parkvägen 14 bygger ett garage "
            "nära tomtgränsen. Behöver detta bygglov?"
        )
    )

    result = analyze_inquiry_with_llm(inquiry)

    print("Source:", result.source.value)
    print(result.inquiry.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
    