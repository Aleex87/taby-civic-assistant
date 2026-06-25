from src.services.taby_retriever import retrieve_known_pages


def main() -> None:
    """Run one real retrieval against an official Taby page."""

    urls = [
        (
            "https://www.taby.se/bygga-bo-och-miljo/"
            "bygga-riva-och-forandra/"
            "behover-jag-bygglov/komplementbyggnad"
        )
    ]

    result = retrieve_known_pages(
        query="garage bygglov detaljplan",
        urls=urls,
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
