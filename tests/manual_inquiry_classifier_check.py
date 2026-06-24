from src.schemas import CitizenInquiry
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


if __name__ == "__main__":
    main()
