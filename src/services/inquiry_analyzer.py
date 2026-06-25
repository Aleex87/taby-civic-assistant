import json
import logging
import time

from pydantic import ValidationError

from src.config import get_openrouter_model
from src.llm.openrouter_client import (
    OpenRouterError,
    OpenRouterUserFacingError,
    send_chat_message,
)
from src.schemas import (
    CitizenInquiry,
    ClassificationSource,
    InquiryAnalysis,
    InquiryClassificationResult,
)
from src.triage import classify_inquiry


logger = logging.getLogger(__name__)

MAX_LLM_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 1.0


SYSTEM_MESSAGE = """
You analyze citizen inquiries addressed to the Municipality of Taby.

Return only a valid JSON object with these fields:
- language: ISO 639-1 language code, such as sv, en, or it
- domain: one of:
  - building_and_planning
  - neighbour_and_property
  - waste_and_environment
  - municipal_service
  - unknown
- intent: one of:
  - general_information
  - permission_question
  - report_possible_violation
  - request_contact
  - case_status
  - submit_complaint
  - unknown
- requires_location: boolean
- requires_human_review: boolean
- entities:
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
- Detect the language from the surrounding sentence grammar and vocabulary.
- Do not classify the inquiry as Swedish only because it contains a Swedish
  street name, municipality name, personal name, or other proper noun.
- Preserve the original spelling of addresses independently from the detected
  inquiry language.
- Preserve only Swedish street names exactly as written.
- Do not invent addresses or facts.
- Preserve Swedish street names exactly as written.
- Use reported_address only for another explicitly mentioned property.
- Use requires_location=true when the answer depends on an address,
  property, building, neighbour, local plan, complaint location,
  or another geographic place.
- Use requires_human_review=true for legal interpretation,
  property-specific planning rules, possible violations,
  neighbour disputes, ambiguous information, or complaints.
- Use subject for the main object or issue.
- Include only missing information that is relevant to the case.
- Do not add explanations, markdown, or extra fields.
""".strip()


def _parse_analysis(content: str) -> InquiryAnalysis:
    """Parse and validate the complete analysis returned by the model."""

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The language model returned invalid analysis JSON."
        ) from exc

    try:
        return InquiryAnalysis.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(
            "The language model returned an invalid inquiry analysis."
        ) from exc


def analyze_inquiry_with_llm(
    inquiry: CitizenInquiry,
) -> InquiryClassificationResult:
    """Analyze an inquiry with OpenRouter and fall back safely."""

    last_error: Exception | None = None

    for attempt in range(MAX_LLM_ATTEMPTS):
        try:
            content = send_chat_message(
                message=inquiry.original_text,
                model=get_openrouter_model(),
                system_message=SYSTEM_MESSAGE,
                response_format={
                    "type": "json_object",
                },
            )

            analysis = _parse_analysis(content)

            analyzed_inquiry = inquiry.model_copy(
                update={
                    "language": analysis.language,
                    "domain": analysis.domain,
                    "intent": analysis.intent,
                    "entities": analysis.entities,
                    "requires_location": analysis.requires_location,
                    "requires_human_review": (
                        analysis.requires_human_review
                    ),
                }
            )

            return InquiryClassificationResult(
                inquiry=analyzed_inquiry,
                source=ClassificationSource.LLM,
            )

        except (
            OpenRouterUserFacingError,
            OpenRouterError,
            RuntimeError,
            ValueError,
        ) as exc:
            last_error = exc

            logger.warning(
                "Inquiry analysis attempt %s failed: %s",
                attempt + 1,
                exc,
            )

            if attempt < MAX_LLM_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY_SECONDS)

    logger.error(
        "Inquiry analysis failed after %s attempts: %s",
        MAX_LLM_ATTEMPTS,
        last_error,
    )

    fallback_inquiry = classify_inquiry(inquiry)

    return InquiryClassificationResult(
        inquiry=fallback_inquiry,
        source=ClassificationSource.DETERMINISTIC_FALLBACK,
    )
