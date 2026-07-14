"""Small builders for fake httpx request/response objects, needed to
construct real instances of OpenAI's SDK exception classes in tests
without making any actual network calls."""

import httpx


def fake_request():
    return httpx.Request("POST", "https://api.openai.com/v1/responses")


def fake_response(status_code):
    return httpx.Response(status_code, request=fake_request())
