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

from app.schemas.ticket_schema import TicketBatchResponse, TicketResponse


# Load .env variables
load_dotenv()
#Say's error related to particular file
logger = logging.getLogger(__name__)

# Create OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL_NAME = "gpt-4.1"

REQUEST_TIMEOUT_SECONDS = 15

MAX_ATTEMPTS = 2

BACKOFF_BASE_SECONDS = 1

MODEL_TEMPERATURE = 0.2

ROUTE_TICKET_CACHE_SIZE = 128

TRANSIENT_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)

NON_RETRYABLE_ERRORS = (AuthenticationError, BadRequestError)

CONFIDENCE_REVIEW_THRESHOLD = 50


def _call_openai(message: str):

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
    
    return result.model_copy(
        update={"needs_human_review": result.confidence < CONFIDENCE_REVIEW_THRESHOLD}
    )

#decorator runs before function and caches the results
@lru_cache(maxsize=ROUTE_TICKET_CACHE_SIZE)
def route_ticket(message: str) -> list[TicketResponse]:
    response = _call_openai(message)
    #response.output contains the raw output from the model.
    #response.output_parsed contains the already validated Pydantic object.
    result = response.output_parsed

    if result is None:
        logger.error("AI response could not be parsed into TicketBatchResponse")
        raise ValueError("AI did not return a valid structured response")

    return [_apply_human_review_flag(ticket) for ticket in result.tickets]
