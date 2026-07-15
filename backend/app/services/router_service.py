# Used for exponential backoff between retries
import time

# Used to read environment variables
import os

# Used for structured, filterable logs instead of print()
import logging

# Used to cache identical repeat tickets in-process (stdlib, no new dependency)
from functools import lru_cache

# Loads variables from .env
from dotenv import load_dotenv

# OpenAI SDK + the specific exceptions we treat as transient vs. fatal
from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
    AuthenticationError,
    BadRequestError,
)

# Import our prompt
from app.prompts.ticket_prompt import SYSTEM_PROMPT

# Import our response schemas — TicketBatchResponse doubles as the JSON
# Schema that OpenAI Structured Outputs enforces at the API level;
# TicketResponse is the per-request/per-intent shape inside it
from app.schemas.ticket_schema import TicketBatchResponse, TicketResponse


# Load .env variables
load_dotenv()

logger = logging.getLogger(__name__)

# Create OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL_NAME = "gpt-4.1"

# Model configuration rationale (why these specific numbers, not just
# what they are):
#
# REQUEST_TIMEOUT_SECONDS = 15 -- this call blocks a synchronous FastAPI
# request end-to-end (the frontend shows a spinner the whole time). 15s
# is long enough that a normal GPT-4.1 structured-output response (which
# in practice takes 1-4s, see the token/latency logging below) never
# times out, but short enough that a genuinely hung request fails fast
# instead of leaving a user staring at a spinner indefinitely.
REQUEST_TIMEOUT_SECONDS = 15

# MAX_ATTEMPTS = 2 -- one retry. A support-ticket submission is an
# interactive, user-facing action, not a background batch job: piling on
# more retries trades a small reliability gain for a user-visible delay
# multiplied by however many attempts are made. One retry already
# recovers from the common transient case (a single dropped request);
# beyond that, the failure is more likely to be a real outage that a
# 3rd or 4th attempt won't fix either.
MAX_ATTEMPTS = 2
BACKOFF_BASE_SECONDS = 1

# MODEL_TEMPERATURE = 0.2 -- low but non-zero. This is a classification
# task with a fixed, small answer space (5 categories x 3 priorities x 5
# teams), so category/priority/team decisions stay effectively
# deterministic run-to-run at this temperature. It is not set to 0.0
# because summary/suggested_reply are short generated text, not
# classifications, and 0.0 tends to make repeated phrasing feel
# robotic/templated across many tickets; 0.2 leaves just enough room for
# natural phrasing there without destabilizing the classification fields.
MODEL_TEMPERATURE = 0.2

# ROUTE_TICKET_CACHE_SIZE -- the classifier is a pure function of the
# message text (same input, same intended output), so identical repeat
# tickets (a demo re-run, a user double-submitting the same text) can
# skip a paid GPT-4.1 call entirely. 128 is generous for this project's
# realistic demo/session scale without holding an unbounded amount of
# memory.
ROUTE_TICKET_CACHE_SIZE = 128

# Transient infrastructure failures: worth retrying, since the exact
# same request may succeed a moment later.
TRANSIENT_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)

# Non-retryable failures: the request itself is invalid or
# unauthorized, so trying again would just repeat the same failure.
NON_RETRYABLE_ERRORS = (AuthenticationError, BadRequestError)

# CONFIDENCE_REVIEW_THRESHOLD -- below this, a ticket is flagged
# needs_human_review=True regardless of what the model itself reported
# for that field. This project's `confidence` is an int on a 0-100
# scale (matches the DB column, the frontend confidence meter, and the
# evaluation harness's confidence-band buckets), so 50 is the direct
# equivalent of a 0.5 threshold on a 0-1 float scale -- same cutoff,
# same fraction of the range, just not re-scaled everywhere else for a
# purely cosmetic change.
CONFIDENCE_REVIEW_THRESHOLD = 50


def _call_openai(message: str):
    """
    Calls the OpenAI Responses API with Structured Outputs
    (text_format=TicketBatchResponse), so the response is guaranteed by
    OpenAI to be valid JSON matching that schema — a `tickets` array
    with one fully-classified TicketResponse per distinct request found
    in the message — this replaces relying on prompt instructions alone.

    Only retries transient errors (rate limits, timeouts, network
    issues, temporary server errors), with exponential backoff.
    Authentication/invalid-request errors are raised immediately since
    retrying them can never succeed.
    """
    attempt = 0

    while True:
        attempt += 1
        started_at = time.monotonic()

        try:
            response = client.responses.parse(
                model=MODEL_NAME,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                text_format=TicketBatchResponse,
                timeout=REQUEST_TIMEOUT_SECONDS,
                temperature=MODEL_TEMPERATURE,
            )

            latency_ms = (time.monotonic() - started_at) * 1000
            response._latency_ms = latency_ms  # noqa: SLF001 -- stash for route_ticket_with_diagnostics

            if response.usage:
                logger.info(
                    "OpenAI call usage: input=%s output=%s total=%s tokens, latency=%.0fms",
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    response.usage.total_tokens,
                    latency_ms,
                )

            return response

        except NON_RETRYABLE_ERRORS:
            logger.error("Non-retryable OpenAI error", exc_info=True)
            raise

        except TRANSIENT_ERRORS as exc:
            if attempt >= MAX_ATTEMPTS:
                logger.error(
                    "OpenAI call failed after %s attempt(s)", attempt, exc_info=True
                )
                raise

            backoff_seconds = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Transient OpenAI error on attempt %s/%s (%s). Retrying in %ss.",
                attempt,
                MAX_ATTEMPTS,
                exc.__class__.__name__,
                backoff_seconds,
            )
            time.sleep(backoff_seconds)


def _apply_human_review_flag(result: TicketResponse) -> TicketResponse:
    """
    Overwrites needs_human_review deterministically from `confidence`,
    regardless of what the model itself put there. Guarantees the flag
    always matches CONFIDENCE_REVIEW_THRESHOLD instead of depending on
    the model doing its own arithmetic correctly on every request.
    """
    return result.model_copy(
        update={"needs_human_review": result.confidence < CONFIDENCE_REVIEW_THRESHOLD}
    )


@lru_cache(maxsize=ROUTE_TICKET_CACHE_SIZE)
def route_ticket(message: str) -> list[TicketResponse]:
    """
    Sends the support ticket to GPT and returns one validated
    TicketResponse per distinct request found in the message (a
    single-intent message still returns a one-item list).

    JSON schema conformance is guaranteed by OpenAI Structured Outputs,
    not by prompt instructions or post-hoc JSON repair.

    Cached on the exact message text: the same ticket text always
    deserves the same classification, so a repeat submission returns
    instantly instead of paying for another GPT-4.1 call. lru_cache
    never caches a raised exception, so a failed call is always retried
    for real on the next attempt rather than replaying the failure.

    This is the interactive API path (used by POST /route-ticket) and
    keeps its existing raise-on-failure contract — the route handler
    turns that into a clean 502. For batch/CLI use where you want
    per-call telemetry and a structured result instead of an exception,
    use route_ticket_with_diagnostics() below.
    """
    response = _call_openai(message)

    result = response.output_parsed

    if result is None:
        # Structured Outputs didn't produce a parseable response
        # (e.g. the model refused). This is a content/schema failure,
        # not a transient one, so it is not retried.
        logger.error("AI response could not be parsed into TicketBatchResponse")
        raise ValueError("AI did not return a valid structured response")

    return [_apply_human_review_flag(ticket) for ticket in result.tickets]


def route_ticket_with_diagnostics(message: str) -> dict:
    """
    Like route_ticket(), but:
    - bypasses the lru_cache, so latency/tokens reflect a real call
      every time (needed for a batch summary to mean anything)
    - never raises: on failure (retries exhausted, non-retryable error,
      or an unparseable response), returns a structured error dict
      instead of crashing the caller
    - always returns latency_ms and token usage, for per-ticket logging
      and batch reporting (see scripts/batch_summary.py)

    Intended for batch/evaluation/CLI tooling, not the interactive API
    path — a single flaky ticket in a 20-ticket batch should not stop
    the other 19 from being processed and reported on.
    """
    try:
        response = _call_openai(message)
    except Exception as exc:
        logger.error("route_ticket_with_diagnostics: call failed", exc_info=True)
        return {
            "success": False,
            "tickets": None,
            "error": {"type": exc.__class__.__name__, "message": str(exc)},
            "latency_ms": None,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        }

    result = response.output_parsed
    usage = response.usage

    if result is None:
        logger.error("route_ticket_with_diagnostics: unparseable response")
        return {
            "success": False,
            "tickets": None,
            "error": {
                "type": "UnparseableResponse",
                "message": "AI did not return a valid structured response",
            },
            "latency_ms": getattr(response, "_latency_ms", None),
            "input_tokens": usage.input_tokens if usage else None,
            "output_tokens": usage.output_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
        }

    return {
        "success": True,
        "tickets": [_apply_human_review_flag(ticket) for ticket in result.tickets],
        "error": None,
        "latency_ms": getattr(response, "_latency_ms", None),
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
    }
