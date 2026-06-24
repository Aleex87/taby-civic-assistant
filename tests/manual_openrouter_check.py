from src.config import get_openrouter_model
from src.llm.openrouter_client import (
    OpenRouterError,
    OpenRouterUserFacingError,
    send_chat_message,
)


def main() -> None:
    """Send a simple test message to OpenRouter."""

    model = get_openrouter_model()

    print(f"Using model: {model}")

    try:
        response = send_chat_message(
            message=(
                "Reply with exactly this sentence: "
                "OpenRouter connection successful."
            ),
            model=model,
        )
    except OpenRouterUserFacingError as exc:
        print(f"User-facing error: {exc}")
        raise SystemExit(1) from exc
    except OpenRouterError as exc:
        print(f"Technical error: {exc}")
        raise SystemExit(1) from exc

    print("Response:")
    print(response)


if __name__ == "__main__":
    main()