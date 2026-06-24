import json

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
    InquiryClassification,
    InquiryClassificationResult,
)
from src.triage import classify_inquiry


SYSTEM_MESSAGE = """
You classify citizen inquiries addressed to the Municipality of Taby.

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

Use requires_location=true when the answer depends on an address,
property, building, neighbour, local plan, complaint location,
or another geographic place.

Use requires_human_review=true when the inquiry involves:
- legal or administrative interpretation
- a possible unauthorised construction
- a neighbour dispute
- property-specific planning rules
- insufficient or ambiguous information

Choose the intent based on the citizen's main goal:
- general_information: asks for general rules or guidance
- permission_question: asks whether an action is allowed or requires permission
- report_possible_violation: reports a potentially unauthorised action
- request_contact: asks to speak with a municipal officer
- case_status: asks about an existing application or case
- submit_complaint: wants to submit a complaint or report a nuisance
- unknown: the goal cannot be determined

Do not add explanations, markdown, or extra fields.
""".strip()


def _parse_classification(content: str) -> InquiryClassification:
    """Parse and validate the classification returned by the model."""

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The language model returned invalid JSON."
        ) from exc

    try:
        return InquiryClassification.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(
            "The language model returned an invalid classification."
        ) from exc


def classify_inquiry_with_llm(
    inquiry: CitizenInquiry,
) -> InquiryClassificationResult:
    """Classify an inquiry with OpenRouter and use rules as fallback."""

    try:
        content = send_chat_message(
            message=inquiry.original_text,
            model=get_openrouter_model(),
            system_message=SYSTEM_MESSAGE,
            response_format={
                "type": "json_object",
            },
        )

        classification = _parse_classification(content)

        classified_inquiry = inquiry.model_copy(
            update={
                "language": classification.language,
                "domain": classification.domain,
                "intent": classification.intent,
                "requires_location": classification.requires_location,
                "requires_human_review": (
                    classification.requires_human_review
                ),
            }
        )

        return InquiryClassificationResult(
            inquiry=classified_inquiry,
            source=ClassificationSource.LLM,
        )

    except (
        OpenRouterUserFacingError,
        OpenRouterError,
        RuntimeError,
        ValueError,
    ):
        fallback_inquiry = classify_inquiry(inquiry)

        return InquiryClassificationResult(
            inquiry=fallback_inquiry,
            source=ClassificationSource.DETERMINISTIC_FALLBACK,
        )
    