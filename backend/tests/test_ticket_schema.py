"""
Tests for app.schemas.ticket_schema -- TicketRequest validates that the
`message` field rejects empty/whitespace-only input while still allowing
normal ticket text and respecting the existing max_length constraint.
TicketBatchResponse validates that the `tickets` array (the actual
Structured Outputs text_format) can never come back empty.
"""

import pytest
from pydantic import ValidationError

from app.schemas.ticket_schema import TicketBatchResponse, TicketRequest, TicketResponse


def test_empty_message_is_rejected():
    with pytest.raises(ValidationError):
        TicketRequest(message="")


def test_whitespace_only_message_is_rejected():
    with pytest.raises(ValidationError):
        TicketRequest(message="   ")


def test_valid_message_is_accepted():
    request = TicketRequest(message="My WiFi keeps dropping every few minutes")
    assert request.message == "My WiFi keeps dropping every few minutes"


def test_message_over_max_length_is_still_rejected():
    with pytest.raises(ValidationError):
        TicketRequest(message="a" * 4001)


def _make_ticket_response(**overrides):
    defaults = dict(
        category="Billing",
        priority="High",
        assigned_team="Finance",
        reason="Customer was charged twice.",
        confidence=95,
        sentiment="Angry",
        summary="Customer reports a duplicate charge.",
        keywords=["billing", "refund"],
        estimated_resolution_time="1-4 Hours",
        suggested_reply="We're sorry for the inconvenience and are looking into it.",
        escalation_needed=True,
        needs_human_review=False,
    )
    defaults.update(overrides)
    return TicketResponse(**defaults)


def test_batch_response_accepts_a_single_ticket():
    batch = TicketBatchResponse(tickets=[_make_ticket_response()])
    assert len(batch.tickets) == 1


def test_batch_response_accepts_multiple_tickets():
    batch = TicketBatchResponse(
        tickets=[
            _make_ticket_response(),
            _make_ticket_response(category="General", assigned_team="Support", priority="Low"),
        ]
    )
    assert len(batch.tickets) == 2


def test_batch_response_rejects_an_empty_tickets_list():
    with pytest.raises(ValidationError):
        TicketBatchResponse(tickets=[])


def test_off_topic_category_and_unassigned_team_are_valid():
    ticket = _make_ticket_response(
        category="Off-Topic",
        priority="Low",
        assigned_team="Unassigned",
        estimated_resolution_time="N/A - no action required",
    )
    assert ticket.category == "Off-Topic"
    assert ticket.assigned_team == "Unassigned"


def test_off_topic_category_rejects_a_real_team():
    with pytest.raises(ValidationError):
        _make_ticket_response(category="Off-Topic", assigned_team="NotARealTeam")
