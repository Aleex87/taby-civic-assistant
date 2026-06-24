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

def get_openrouter_model() -> str:
    """Return the configured OpenRouter model identifier."""

    model = os.getenv("OPENROUTER_MODEL")

    if not model:
        raise RuntimeError(
            "OPENROUTER_MODEL is not configured. "
            "Add it to the local .env file."
        )

    return model