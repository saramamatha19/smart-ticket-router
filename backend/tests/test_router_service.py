"""
Tests for app.services.router_service — the core AI routing pipeline.

Every test mocks the OpenAI client, so the suite makes no real network
calls and spends no OpenAI credits. Real-model behavior (does GPT-4.1
actually classify well?) is measured separately in backend/evaluation/.
"""

from unittest.mock import MagicMock, patch

import pytest

from openai import (
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

from app.schemas.ticket_schema import TicketBatchResponse, TicketResponse
from app.services import router_service
from tests.helpers import fake_response


def make_ticket_response(**overrides):
    """Builds a valid TicketResponse, with individual fields overridden per test.

    needs_human_review defaults to whatever route_ticket() would compute
    from confidence, so tests that don't care about the review flag
    don't need to set it by hand -- and route_ticket()'s deterministic
    overwrite (see _apply_human_review_flag) means the returned object
    always matches this anyway.
    """
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
    )
    defaults.update(overrides)
    defaults.setdefault(
        "needs_human_review",
        defaults["confidence"] < router_service.CONFIDENCE_REVIEW_THRESHOLD,
    )
    return TicketResponse(**defaults)


def make_batch(*tickets):
    """Wraps one or more TicketResponse objects the way the real
    Structured Outputs call would -- route_ticket() reads `.tickets`
    off of whatever `.output_parsed` returns."""
    return TicketBatchResponse(tickets=list(tickets))


def make_parsed_response(output_parsed):
    """Stands in for openai's ParsedResponse. router_service only ever
    touches `.output_parsed`, so that's the only attribute we fake."""
    mock_response = MagicMock()
    mock_response.output_parsed = output_parsed
    return mock_response


def patch_parse(**kwargs):
    return patch.object(router_service.client.responses, "parse", **kwargs)


# ---------------------------------------------------------------------
# Valid AI response
# ---------------------------------------------------------------------
def test_valid_ai_response_is_returned():
    expected = make_ticket_response()

    with patch_parse(return_value=make_parsed_response(make_batch(expected))) as mock_parse:
        result = router_service.route_ticket("I was charged twice, please refund me.")

    assert result == [expected]
    mock_parse.assert_called_once()


# ---------------------------------------------------------------------
# Multi-intent: a message with several independent requests comes back
# as one TicketResponse per request, not merged/averaged into one.
# ---------------------------------------------------------------------
def test_multi_intent_message_returns_one_ticket_per_request():
    billing_ticket = make_ticket_response(category="Billing", assigned_team="Finance")
    # The joke half of the message is Off-Topic/Unassigned, not
    # General/Support -- it's not a support matter at all, so it must
    # not land in a real team's queue (see PROMPT_CHANGELOG.md v4->v5).
    joke_ticket = make_ticket_response(
        category="Off-Topic",
        priority="Low",
        assigned_team="Unassigned",
        reason="This request is unrelated to product support and requires no team action.",
        confidence=95,
        sentiment="Neutral",
        summary="Customer asked for a joke.",
        keywords=["joke"],
        estimated_resolution_time="N/A - no action required",
        suggested_reply="Happy to help with your billing issue above!",
        escalation_needed=False,
    )

    with patch_parse(
        return_value=make_parsed_response(make_batch(billing_ticket, joke_ticket))
    ) as mock_parse:
        result = router_service.route_ticket(
            "I was charged twice this month. Also, tell me a joke."
        )

    assert result == [billing_ticket, joke_ticket]
    mock_parse.assert_called_once()


# ---------------------------------------------------------------------
# Caching: an identical repeat message must not re-call OpenAI
# ---------------------------------------------------------------------
def test_identical_repeat_message_is_served_from_cache():
    expected = make_ticket_response()
    message = "My WiFi keeps dropping every few minutes"

    with patch_parse(return_value=make_parsed_response(make_batch(expected))) as mock_parse:
        first = router_service.route_ticket(message)
        second = router_service.route_ticket(message)

    assert first == [expected]
    assert second == [expected]
    mock_parse.assert_called_once()  # the second call must be served from cache


def test_different_messages_are_not_conflated_by_the_cache():
    billing_response = make_ticket_response(category="Billing", assigned_team="Finance")
    network_response = make_ticket_response(
        category="Network", assigned_team="Network Operations", priority="Medium"
    )

    with patch_parse(
        side_effect=[
            make_parsed_response(make_batch(billing_response)),
            make_parsed_response(make_batch(network_response)),
        ]
    ) as mock_parse:
        result_a = router_service.route_ticket("My invoice is wrong")
        result_b = router_service.route_ticket("My VPN won't connect")

    assert result_a[0].category == "Billing"
    assert result_b[0].category == "Network"
    assert mock_parse.call_count == 2


# ---------------------------------------------------------------------
# Invalid JSON / unparseable response
#
# With Structured Outputs, OpenAI guarantees the raw text is valid JSON
# matching the schema, so "invalid JSON" now shows up as
# `output_parsed is None` (e.g. a model refusal) instead of a
# json.JSONDecodeError. This must fail fast, not retry — a schema/content
# failure won't fix itself on a second attempt.
# ---------------------------------------------------------------------
def test_invalid_or_unparseable_response_raises_without_retrying():
    with patch_parse(return_value=make_parsed_response(None)) as mock_parse:
        with pytest.raises(ValueError):
            router_service.route_ticket("some message")

    assert mock_parse.call_count == 1


# ---------------------------------------------------------------------
# Retry success: a transient error on attempt 1, success on attempt 2
# ---------------------------------------------------------------------
def test_retry_succeeds_after_one_transient_failure():
    expected = make_ticket_response()
    transient_error = RateLimitError("Rate limited", response=fake_response(429), body=None)

    with patch_parse(
        side_effect=[transient_error, make_parsed_response(make_batch(expected))]
    ) as mock_parse, patch("app.services.router_service.time.sleep") as mock_sleep:
        result = router_service.route_ticket("a message")

    assert result == [expected]
    assert mock_parse.call_count == 2
    mock_sleep.assert_called_once()  # backoff happened between attempts


# ---------------------------------------------------------------------
# Retry failure: transient error on every attempt, all attempts used
# ---------------------------------------------------------------------
def test_retry_exhausted_raises_the_last_transient_error():
    transient_error = InternalServerError("Server error", response=fake_response(500), body=None)

    with patch_parse(side_effect=transient_error) as mock_parse, patch(
        "app.services.router_service.time.sleep"
    ):
        with pytest.raises(InternalServerError):
            router_service.route_ticket("a message")

    assert mock_parse.call_count == router_service.MAX_ATTEMPTS


# ---------------------------------------------------------------------
# Non-retryable errors must fail immediately, not consume all attempts
# ---------------------------------------------------------------------
def test_authentication_error_is_not_retried():
    auth_error = AuthenticationError("Invalid API key", response=fake_response(401), body=None)

    with patch_parse(side_effect=auth_error) as mock_parse:
        with pytest.raises(AuthenticationError):
            router_service.route_ticket("a message")

    assert mock_parse.call_count == 1


# ---------------------------------------------------------------------
# The 3 required edge cases from the mission brief.
#
# These prove the *pipeline* correctly returns whatever Structured
# Outputs response it's given for each case — they mock the AI
# response, so they verify the plumbing, not GPT-4.1's real judgment.
# Real-model accuracy on these exact cases is measured in
# backend/evaluation/evaluation.md.
# ---------------------------------------------------------------------
def test_angry_tone_ticket():
    expected = make_ticket_response(
        category="Technical",
        priority="High",
        assigned_team="Engineering",
        sentiment="Angry",
        escalation_needed=True,
    )

    with patch_parse(return_value=make_parsed_response(make_batch(expected))):
        result = router_service.route_ticket(
            "THIS IS RIDICULOUS!!! My account is LOCKED and nobody replies!!!"
        )[0]

    assert result.sentiment == "Angry"
    assert result.priority == "High"


def test_very_short_message_ticket():
    expected = make_ticket_response(
        category="General",
        priority="Low",
        assigned_team="Support",
        sentiment="Neutral",
        reason="The ticket does not contain enough information for accurate routing.",
        escalation_needed=False,
    )

    with patch_parse(return_value=make_parsed_response(make_batch(expected))):
        result = router_service.route_ticket("Help")[0]

    assert result.category == "General"
    assert result.priority == "Low"


def test_ambiguous_ticket():
    expected = make_ticket_response(
        category="Technical",
        priority="Low",
        assigned_team="Support",
        sentiment="Neutral",
        reason="The issue appears technical but lacks sufficient detail.",
        escalation_needed=False,
    )

    with patch_parse(return_value=make_parsed_response(make_batch(expected))):
        result = router_service.route_ticket("Something is wrong with my application.")[0]

    assert result.category == "Technical"
    assert result.priority == "Low"


# ---------------------------------------------------------------------
# needs_human_review is recalculated from confidence, not trusted from
# the model's own guess -- these use a raw TicketResponse.model_copy
# override so the model's self-reported flag deliberately disagrees
# with what the threshold says, to prove route_ticket() overwrites it.
# ---------------------------------------------------------------------
def test_low_confidence_is_flagged_for_human_review_even_if_model_says_no():
    model_reported = make_ticket_response(confidence=30).model_copy(
        update={"needs_human_review": False}
    )

    with patch_parse(return_value=make_parsed_response(make_batch(model_reported))):
        result = router_service.route_ticket("a vague message")[0]

    assert result.confidence == 30
    assert result.needs_human_review is True


def test_high_confidence_is_not_flagged_for_human_review_even_if_model_says_yes():
    model_reported = make_ticket_response(confidence=90).model_copy(
        update={"needs_human_review": True}
    )

    with patch_parse(return_value=make_parsed_response(make_batch(model_reported))):
        result = router_service.route_ticket("a clear message")[0]

    assert result.confidence == 90
    assert result.needs_human_review is False


# ---------------------------------------------------------------------
# route_ticket_with_diagnostics() -- structured error dict on failure
# instead of raising, plus latency/token telemetry, for batch/CLI use.
# ---------------------------------------------------------------------
def test_diagnostics_returns_structured_success_with_telemetry():
    expected = make_ticket_response(confidence=88)
    mock_response = make_parsed_response(make_batch(expected))
    mock_response.usage.input_tokens = 120
    mock_response.usage.output_tokens = 60
    mock_response.usage.total_tokens = 180

    with patch_parse(return_value=mock_response):
        outcome = router_service.route_ticket_with_diagnostics("a message")

    assert outcome["success"] is True
    assert outcome["error"] is None
    assert outcome["tickets"][0].category == expected.category
    assert outcome["input_tokens"] == 120
    assert outcome["output_tokens"] == 60
    assert outcome["total_tokens"] == 180
    assert outcome["latency_ms"] is not None


def test_diagnostics_returns_structured_error_instead_of_raising_when_retries_exhausted():
    transient_error = InternalServerError("Server error", response=fake_response(500), body=None)

    with patch_parse(side_effect=transient_error), patch(
        "app.services.router_service.time.sleep"
    ):
        outcome = router_service.route_ticket_with_diagnostics("a message")

    assert outcome["success"] is False
    assert outcome["tickets"] is None
    assert outcome["error"]["type"] == "InternalServerError"


def test_diagnostics_returns_structured_error_for_unparseable_response():
    with patch_parse(return_value=make_parsed_response(None)):
        outcome = router_service.route_ticket_with_diagnostics("a message")

    assert outcome["success"] is False
    assert outcome["tickets"] is None
    assert outcome["error"]["type"] == "UnparseableResponse"
