from pydantic import BaseModel, Field


class CitizenInquiry(BaseModel):
    """Structured representation of a citizen inquiry."""

    original_text: str = Field(
        min_length=1,
        description="Original message submitted by the citizen.",
    )
    