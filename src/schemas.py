from enum import StrEnum

from pydantic import BaseModel, Field


class InquiryDomain(StrEnum):
    """Supported high-level municipal inquiry domains."""

    BUILDING_AND_PLANNING = "building_and_planning"
    NEIGHBOUR_AND_PROPERTY = "neighbour_and_property"
    WASTE_AND_ENVIRONMENT = "waste_and_environment"
    MUNICIPAL_SERVICE = "municipal_service"
    UNKNOWN = "unknown"


class ClassificationSource(StrEnum):
    """Source used to classify a citizen inquiry."""

    LLM = "llm"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class CitizenInquiry(BaseModel):
    """Structured representation of a citizen inquiry."""

    original_text: str = Field(
        min_length=1,
        description="Original message submitted by the citizen.",
    )
    language: str = Field(
        default="unknown",
        description="Detected language code or language name.",
    )
    domain: InquiryDomain = Field(
        default=InquiryDomain.UNKNOWN,
        description="High-level domain assigned to the inquiry.",
    )
    requires_location: bool = Field(
        default=False,
        description="Whether the inquiry requires an address or location.",
    )
    requires_human_review: bool = Field(
        default=True,
        description=(
            "Whether the inquiry should be reviewed by a municipal officer."
        ),
    )


class InquiryClassification(BaseModel):
    """Validated classification returned by the language model."""

    language: str = Field(
        min_length=2,
        description="Detected language code, such as sv, en, or it.",
    )
    domain: InquiryDomain = Field(
        description="High-level municipal domain assigned to the inquiry.",
    )
    requires_location: bool = Field(
        description="Whether an address or geographic location is required.",
    )
    requires_human_review: bool = Field(
        description="Whether the inquiry requires municipal officer review.",
    )


class InquiryClassificationResult(BaseModel):
    """Result returned by the inquiry classification service."""

    inquiry: CitizenInquiry
    source: ClassificationSource
    