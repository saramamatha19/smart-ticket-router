from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class TicketRequest(BaseModel):
    message: str = Field(
        ...,
        max_length=4000,
        description="The raw customer support message to classify.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty or whitespace-only")
        return value

class TicketResponse(BaseModel):
    category: Literal["Billing", "Technical", "Sales", "General", "Network", "Off-Topic"] = Field(
        description="The support category this ticket belongs to."
    )
    priority: Literal["High", "Medium", "Low"] = Field(
        description="Urgency of the ticket based on business impact."
    )
    assigned_team: Literal[
        "Finance", "Engineering", "Network Operations", "Sales", "Support", "Unassigned"
    ] = Field(description="The team responsible for handling this ticket.")
    reason: str = Field(description="One-sentence explanation for the routing decision.")

    # Extended AI analysis fields
    confidence: int = Field(ge=0, le=100, description="Confidence in this classification, 0-100.")
    sentiment: Literal["Positive", "Neutral", "Angry"] = Field(
        description="The customer's emotional tone."
    )
    summary: str = Field(description="One-sentence plain-language summary of the issue.")
    keywords: list[str] = Field(description="3-5 relevant keywords extracted from the ticket.")
    estimated_resolution_time: str = Field(
        description="Human-readable resolution estimate, e.g. '1-4 Hours'."
    )
    suggested_reply: str = Field(description="A short, professional draft reply to the customer.")
    escalation_needed: bool = Field(description="Whether this ticket should be escalated.")
    needs_human_review: bool = Field(
        description="Whether this classification is confident enough to trust without a human check."
    )

class TicketDB(TicketResponse):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    customer_id: int | None = None
    created_at: datetime

TicketRouting = TicketResponse

class TicketBatchResponse(BaseModel):
    tickets: list[TicketResponse] = Field(
        min_length=1,
        description=(
            "One fully-classified entry per distinct request/intent found "
            "in the message. A single-intent message still produces a "
            "list with exactly one entry."
        ),
    )

'''
Pydantic validates incoming requests and outgoing responses.
It ensures that the API receives and returns data in the expected format, reducing errors and making the API more reliable.
'''
