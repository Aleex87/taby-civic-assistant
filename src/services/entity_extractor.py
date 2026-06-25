import json

from pydantic import ValidationError

from src.config import get_openrouter_model
from src.llm.openrouter_client import (
    OpenRouterError,
    OpenRouterUserFacingError,
    send_chat_message,
)
from src.schemas import CitizenInquiry, InquiryEntities


SYSTEM_MESSAGE = """
You extract structured information from citizen inquiries addressed
to the Municipality of Taby.

Return only a valid JSON object with these fields:
- address:
  - street: string or null
  - house_number: string or null
  - municipality: string or null
- subject: short string or null
- neighbour_related: boolean
- reported_address:
  - street: string or null
  - house_number: string or null
  - municipality: string or null
  or null when no second property is explicitly mentioned
- missing_information: list of short strings

Rules:
- Do not invent an address.
- Preserve Swedish street names exactly as written.
- The primary address belongs to the citizen or the property discussed
  as the main subject.
- Use reported_address only for another explicitly mentioned property,
  such as a neighbour's property.
- Use subject for the main object or issue, such as garage,
  balcony glazing, waste collection, noise, or case status.
- Include only information that is genuinely missing and relevant.
- Do not add explanations, markdown, or extra fields.
""".strip()


def _parse_entities(content: str) -> InquiryEntities:
    """Parse and validate entities returned by the language model."""

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The language model returned invalid entity JSON."
        ) from exc

    try:
        return InquiryEntities.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(
            "The language model returned invalid inquiry entities."
        ) from exc


def extract_entities_with_llm(
    inquiry: CitizenInquiry,
) -> CitizenInquiry:
    """Extract structured entities and update the citizen inquiry."""

    try:
        content = send_chat_message(
            message=inquiry.original_text,
            model=get_openrouter_model(),
            system_message=SYSTEM_MESSAGE,
            response_format={
                "type": "json_object",
            },
        )

        entities = _parse_entities(content)

        return inquiry.model_copy(
            update={
                "entities": entities,
            }
        )

    except (
        OpenRouterUserFacingError,
        OpenRouterError,
        RuntimeError,
        ValueError,
    ):
        return inquiry
    