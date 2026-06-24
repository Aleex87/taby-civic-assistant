import os

from dotenv import load_dotenv


load_dotenv()


def get_openrouter_api_key() -> str:
    """Return the configured OpenRouter API key."""

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. "
            "Add it to the local .env file."
        )

    return api_key