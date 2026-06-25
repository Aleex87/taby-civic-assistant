from enum import StrEnum

from pydantic import BaseModel, Field


class InquiryDomain(StrEnum):
    """Supported high-level municipal inquiry domains."""

    BUILDING_AND_PLANNING = "building_and_planning"
    NEIGHBOUR_AND_PROPERTY = "neighbour_and_property"
    WASTE_AND_ENVIRONMENT = "waste_and_environment"
    MUNICIPAL_SERVICE = "municipal_service"
    UNKNOWN = "unknown"


class InquiryIntent(StrEnum):
    """Supported citizen inquiry intents."""

    GENERAL_INFORMATION = "general_information"
    PERMISSION_QUESTION = "permission_question"
    REPORT_POSSIBLE_VIOLATION = "report_possible_violation"
    REQUEST_CONTACT = "request_contact"
    CASE_STATUS = "case_status"
    SUBMIT_COMPLAINT = "submit_complaint"
    UNKNOWN = "unknown"


class ClassificationSource(StrEnum):
    """Source used to classify a citizen inquiry."""

    LLM = "llm"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class AddressData(BaseModel):
    """Address information extracted from a citizen inquiry."""

    street: str | None = Field(
        default=None,
        description="Street name extracted from the inquiry.",
    )
    house_number: str | None = Field(
        default=None,
        description="House number extracted from the inquiry.",
    )
    municipality: str | None = Field(
        default=None,
        description="Municipality mentioned in the inquiry.",
    )


class InquiryEntities(BaseModel):
    """Structured entities extracted from a citizen inquiry."""

    address: AddressData = Field(
        default_factory=AddressData,
        description="Address associated with the inquiry.",
    )
    subject: str | None = Field(
        default=None,
        description=(
            "Main object or issue mentioned, such as garage, balcony, "
            "waste collection, or noise."
        ),
    )
    neighbour_related: bool = Field(
        default=False,
        description="Whether the inquiry concerns a neighbour.",
    )
    reported_address: AddressData | None = Field(
        default=None,
        description=(
            "Address of another property involved in the inquiry, "
            "when explicitly provided."
        ),
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Information still needed to process the inquiry.",
    )

class InquiryAnalysis(BaseModel):
    """Complete structured analysis returned by the language model."""

    language: str = Field(
        min_length=2,
        description="Detected language code, such as sv, en, or it.",
    )
    domain: InquiryDomain = Field(
        description="High-level municipal domain assigned to the inquiry.",
    )
    intent: InquiryIntent = Field(
        description="Specific intent expressed by the citizen.",
    )
    requires_location: bool = Field(
        description="Whether an address or geographic location is required.",
    )
    requires_human_review: bool = Field(
        description="Whether the inquiry requires municipal officer review.",
    )
    entities: InquiryEntities = Field(
        description="Structured entities extracted from the inquiry.",
    )

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
    intent: InquiryIntent = Field(
        default=InquiryIntent.UNKNOWN,
        description="Specific intent expressed by the citizen.",
    )
    entities: InquiryEntities = Field(
        default_factory=InquiryEntities,
        description="Structured entities extracted from the inquiry.",
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
    intent: InquiryIntent = Field(
        description="Specific intent expressed by the citizen.",
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
    