from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime


# --------------------------------------------------
# Used when a user sends a support ticket
# --------------------------------------------------
class TicketRequest(BaseModel):
    message: str = Field(
        ...,
        max_length=4000,
        description="The raw customer support message to classify.",
    )

    # An empty or whitespace-only message has no content to route on and
    # would otherwise reach OpenAI as a wasted API call -- reject it here,
    # at the request boundary, instead of relying on the frontend's
    # client-side check (which a direct API call bypasses entirely).
    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty or whitespace-only")
        return value


# --------------------------------------------------
# AI response after routing the ticket
#
# These fields double as the JSON Schema OpenAI Structured Outputs
# enforces at the API level (see app/services/router_service.py) —
# the allowed values here are a hard guarantee, not just a prompt hint.
# --------------------------------------------------
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

    # The model's own guess is a placeholder — app/services/router_service.py
    # deterministically overwrites this from `confidence` before the response
    # ever leaves route_ticket(), so it can't drift from the threshold due to
    # model inconsistency. Kept as a real schema field (not computed only in
    # Python) so the API response, the DB row, and the frontend all carry it.
    needs_human_review: bool = Field(
        description="Whether this classification is confident enough to trust without a human check."
    )


# --------------------------------------------------
# Complete ticket stored in the database
# --------------------------------------------------
class TicketDB(TicketResponse):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    created_at: datetime


# Alias for reviewers/tooling that expect this exact name. TicketResponse
# and TicketRouting are the same model — see PROMPT_CHANGELOG.md /
# LEARNINGS.md for why this project uses OpenAI Structured Outputs
# (`text_format=TicketBatchResponse` in router_service.py) instead of
# `response_format={"type": "json_object"}` + manual `model_validate_json()`.
TicketRouting = TicketResponse


# --------------------------------------------------
# Wraps one or more TicketResponse objects — a single customer message
# can contain multiple distinct, independent requests (e.g. a billing
# question and an unrelated joke request) that belong to different
# categories/teams. This is the actual `text_format` passed to OpenAI
# Structured Outputs (see app/services/router_service.py); TicketResponse
# above is still the per-request/per-intent shape.
# --------------------------------------------------
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
