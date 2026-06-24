from typing import Any

import httpx

from src.config import get_openrouter_api_key


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(RuntimeError):
    """Base error raised for OpenRouter client issues."""


class OpenRouterUserFacingError(OpenRouterError):
    """Error with a message suitable for display in the UI."""


def _extract_error_message(response: httpx.Response) -> str:
    """Extract a readable error message from an OpenRouter response."""

    try:
        data = response.json()
    except ValueError:
        return response.text.strip() or "No additional error details were provided."

    if isinstance(data, dict):
        error_data = data.get("error")

        if isinstance(error_data, dict):
            message = error_data.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()

        message = data.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

    return response.text.strip() or "No additional error details were provided."


def _build_user_facing_error(response: httpx.Response) -> OpenRouterUserFacingError:
    """Convert an HTTP error response into a user-friendly exception."""

    status_code = response.status_code
    details = _extract_error_message(response)

    if status_code == 400:
        message = (
            "The AI request could not be processed because the request format "
            "was invalid."
        )
    elif status_code == 401:
        message = (
            "The OpenRouter API key is invalid or missing. "
            "Please check the local configuration."
        )
    elif status_code == 402:
        message = (
            "The AI request could not be completed because the model quota or "
            "available credits may have been exhausted. Please try again later "
            "or switch to another model."
        )
    elif status_code == 403:
        message = (
            "Access to the selected model was denied."
        )
    elif status_code == 404:
        message = (
            "The selected model or API endpoint could not be found."
        )
    elif status_code == 429:
        message = (
            "Too many requests were sent in a short period of time. "
            "Please wait a moment and try again."
        )
    elif 500 <= status_code < 600:
        message = (
            "The AI service is temporarily unavailable. Please try again later."
        )
    else:
        message = (
            f"OpenRouter returned an unexpected HTTP error ({status_code})."
        )

    return OpenRouterUserFacingError(
        f"{message} Details: {details}"
    )


def send_chat_message(
    message: str,
    model: str,
) -> str:
    """Send one message to OpenRouter and return the assistant text."""

    headers = {
        "Authorization": f"Bearer {get_openrouter_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/",
        "X-OpenRouter-Title": "Täby Civic Assistant",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": message,
            }
        ],
    }

    try:
        response = httpx.post(
            OPENROUTER_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise _build_user_facing_error(exc.response) from exc
    except httpx.RequestError as exc:
        raise OpenRouterUserFacingError(
            "The application could not connect to OpenRouter. "
            "Please check the internet connection and try again."
        ) from exc

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError(
            "OpenRouter returned an unexpected response structure."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError(
            "OpenRouter returned an empty response."
        )

    return content.strip()
