"""
Tests for app.schemas.ticket_schema.TicketRequest -- validates that the
`message` field rejects empty/whitespace-only input while still allowing
normal ticket text and respecting the existing max_length constraint.
"""

import pytest
from pydantic import ValidationError

from app.schemas.ticket_schema import TicketRequest


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
