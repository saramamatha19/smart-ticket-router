# Smart Ticket Router

An AI-powered support ticket classifier. A customer message goes in; a structured, validated routing decision comes out — category, priority, assigned team, reasoning, sentiment, confidence, a suggested reply, and more — backed by **GPT-4.1** and a **PostgreSQL** history/analytics dashboard.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Evaluation Results](#evaluation-results)
- [Engineering Deep Dives](#engineering-deep-dives)
- [Learnings](#learnings)
- [Project Limitations](#project-limitations)
- [Future Improvements](#future-improvements)
- [Screenshots](#screenshots)
- [License](#license)

## Overview

Smart Ticket Router takes a raw support message and, in one API call, returns a fully-validated routing decision — no manual triage. It uses **OpenAI Structured Outputs** to guarantee the AI's response always matches an exact schema (never malformed JSON), persists every ticket to PostgreSQL, and ships with a React dashboard for browsing history and analytics.

## Features

- **AI-powered classification** — category, priority, assigned team, sentiment, confidence score, resolution ETA, and a suggested reply, generated in a single GPT-4.1 call.
- **Guaranteed-valid responses** — OpenAI Structured Outputs constrains generation to a strict JSON Schema, eliminating malformed-JSON failures by construction.
- **Confidence-driven human review** — `needs_human_review` is recalculated server-side from `confidence` (not trusted from the model's own guess), surfaced as a banner on the result and a count on the dashboard.
- **Ticket history & analytics dashboard** — a React frontend for browsing past tickets and visualizing trends (by category, priority, sentiment).
- **Resilient backend** — smart retries (only for transient errors), 15s request timeouts, response caching for repeat submissions, and indexed, paginated queries. On exhausted retries or an unparseable response, `route_ticket_with_diagnostics()` returns a structured error dict instead of raising, for batch/CLI callers that shouldn't crash on one bad ticket.
- **Per-call telemetry** — every OpenAI call logs latency and token usage; `scripts/batch_summary.py` runs a batch and prints a parse-rate/latency/token summary.
- **Measured accuracy, not assumed** — a hand-labeled 20-ticket evaluation set reports real accuracy and confidence-calibration numbers on every run.
- **Fully tested** — 17 backend pytest tests + 10 frontend Vitest/RTL tests.

## Tech Stack

| Layer        | Technology                                              |
|--------------|----------------------------------------------------------|
| **Frontend** | React (Vite), Axios, Recharts, lucide-react               |
| **Backend**  | FastAPI, SQLAlchemy, PostgreSQL                            |
| **AI**       | OpenAI GPT-4.1, via the Responses API with Structured Outputs |
| **Testing**  | pytest (backend), Vitest + React Testing Library (frontend) |

## Architecture

```
backend/
  app/
    router/       API endpoints (POST /route-ticket, GET /tickets, GET /tickets/stats) — the "api.py" layer
    services/     AI integration — route_ticket(), route_ticket_with_diagnostics(), retry + logging — the "router.py" layer
    prompts/      The system prompt GPT-4.1 is given, plus versions/ (v1-v3) and PROMPT_CHANGELOG.md
    schemas/      Pydantic request/response contracts (also the AI's JSON Schema) — the "models.py" layer
    models/       SQLAlchemy ORM tables
    crud/         Database read/write functions
    database/     Engine, session, connection setup
  evaluation/     Labeled test tickets + accuracy report
  tests/          pytest suite for the AI pipeline
  scripts/        seed_tickets.py (20 demo tickets), batch_summary.py (parse rate / latency / token report)
frontend/
  src/
    components/   TicketForm, TicketResult, TicketHistory, DashboardStats, TicketChart, ...
    services/     api.js — Axios client (base URL from VITE_API_URL)
```

Split across three files by convention (`schemas/`, `services/`, `router/` + `main.py`) rather than a flat `models.py`/`router.py`/`api.py`, but the separation of concerns is the same: Pydantic models, LLM-call logic, and endpoints each live in exactly one place, not mixed together.

**Request flow:**

1. Frontend posts `{ message }` to `POST /route-ticket` (max 4000 characters, enforced by Pydantic).
2. `app/router/routes.py` calls `route_ticket(message)`.
3. `app/services/router_service.py` sends the message + system prompt to GPT-4.1 via `client.responses.parse(text_format=TicketResponse)`.
4. OpenAI Structured Outputs guarantees the response is valid JSON matching `TicketResponse`'s schema.
5. `route_ticket()` overwrites `needs_human_review` deterministically from `confidence` (never trusts the model's own guess for that field).
6. The validated `TicketResponse` is saved to PostgreSQL and returned to the frontend.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (running locally or accessible remotely)
- An OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` in `backend/` and fill in real values — never commit `.env` itself (it's already gitignored):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/smart_ticket_router
OPENAI_API_KEY=sk-...
```

If you have an existing database from before `needs_human_review` was added, add the column once (non-destructive, matches how the priority/category/created_at indexes were rolled out live):

```sql
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS needs_human_review BOOLEAN;
```

Seed the database with demo tickets (optional):

```bash
python scripts/seed_tickets.py
```

Run a batch and get a parse-rate/latency/token summary (optional, makes real GPT-4.1 calls):

```bash
python scripts/batch_summary.py
```

Run the API:

```bash
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend
npm install
```

Copy `.env.example` to `.env` in `frontend/`:

```env
VITE_API_URL=http://localhost:8000
```

Run the dev server:

```bash
npm run dev
```

The app is now available at `http://localhost:5173`.

## API Reference

| Method | Endpoint             | Description                                                              |
|--------|-----------------------|---------------------------------------------------------------------------|
| `POST` | `/route-ticket`       | Classifies a ticket message and returns the full routing decision.        |
| `GET`  | `/tickets`            | Lists saved tickets, newest first. Supports optional `limit`/`offset`.    |
| `GET`  | `/tickets/stats`      | Returns dashboard analytics (totals by priority, category, sentiment, and a `needs_human_review_count`). |
| `GET`  | `/test-db`            | Health check — verifies database connectivity.                            |

**Example request:**

```bash
curl -X POST http://localhost:8000/route-ticket \
  -H "Content-Type: application/json" \
  -d '{"message": "My invoice shows a charge I do not recognize."}'
```

**Example response** (shape matches `TicketResponse` in `app/schemas/ticket_schema.py`; values illustrative):

```json
{
  "category": "Billing",
  "priority": "High",
  "assigned_team": "Finance",
  "reason": "Customer reports an unrecognized charge on their invoice, which requires billing investigation.",
  "confidence": 88,
  "sentiment": "Neutral",
  "summary": "Customer sees a charge on their invoice they don't recognize.",
  "keywords": ["invoice", "charge", "billing", "unrecognized"],
  "estimated_resolution_time": "1-4 Hours",
  "suggested_reply": "Thanks for flagging this — we're looking into the charge on your invoice and will follow up shortly with details.",
  "escalation_needed": false,
  "needs_human_review": false
}
```

## Environment Variables

| File | Variable | Description |
|------|----------|--------------|
| `backend/.env` | `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:password@localhost:5432/smart_ticket_router`. |
| `backend/.env` | `OPENAI_API_KEY` | OpenAI API key used for GPT-4.1 classification calls. |
| `frontend/.env` | `VITE_API_URL` | Base URL the frontend uses to reach the backend API, e.g. `http://127.0.0.1:8000`. |

Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env`, then fill in real values. Both `.env` files are gitignored and never committed.

## Testing

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

```bash
cd frontend
npm run test
```

**Backend:** 17 tests. 15 mock the OpenAI client (no network calls, no API cost) — valid response, unparseable/invalid response, retry-then-succeed, retry-exhausted, non-retryable auth error, one per required edge case, two proving the response cache works correctly, two proving `needs_human_review` is recalculated from `confidence` even when the model's own guess disagrees, and three covering `route_ticket_with_diagnostics()`'s structured-success/structured-error contract. Plus an API-level test proving `/route-ticket` fails cleanly without leaking exception detail, and an integration test proving pagination against real rows.

**Frontend:** 10 Vitest + React Testing Library tests (`Badge`, `TicketForm`, `TicketChart`) covering validation, loading states, and variant/empty-state rendering.

## Evaluation Results

`backend/evaluation/labeled_tickets.py` hand-labels 20 sample tickets with expected category/priority/team **before** running anything — labels aren't adjusted after seeing the model's predictions.

```bash
cd backend
source venv/bin/activate
python evaluation/run_evaluation.py
```

This runs all 20 tickets through the live classifier and writes `backend/evaluation/evaluation.md` with a full per-ticket comparison table and accuracy percentages.

**Latest recorded results** (from `backend/evaluation/evaluation.md`):

| Metric | Result |
|--------|--------|
| Overall accuracy (category + priority + team all correct) | 95.0% |
| Category accuracy | 100.0% |
| Priority accuracy | 95.0% |
| Team accuracy | 100.0% |
| Avg. confidence on correct predictions | 92.2 |
| Avg. confidence on incorrect predictions | 95.0 |

The one miss (a Billing ticket predicted `High` instead of `Medium`) wasn't one of the three designed edge cases — a useful signal that real-world ambiguity doesn't only show up where it was anticipated. Confidence was **not** lower on the miss in this run, so self-reported confidence should not be treated as a reliable correctness signal on its own (see the `needs_human_review` field in the "Validation" deep dive below).

## Engineering Deep Dives

<details>
<summary><strong>Prompt Engineering</strong></summary>

<br>

The system prompt (`app/prompts/ticket_prompt.py`) defines:

- The 5 allowed categories, 3 priorities, and 5 teams, with keyword guidance for each.
- Explicit priority rules (e.g. "angry tone alone does not mean High priority — the underlying issue must be genuinely urgent").
- The 3 required edge cases (see [Edge Cases](#edge-cases) below).
- Field-by-field guidance for the extended analysis fields (confidence, sentiment, summary, keywords, resolution ETA, suggested reply, escalation).

The prompt handles the *reasoning* work (which category, how urgent); **Structured Outputs handles the *format* work** — conflating those two jobs was the project's biggest earlier gap. Once Structured Outputs took over format enforcement, the old "return ONLY JSON, no markdown..." policing section and the "FINAL CHECK" compliance checklist became dead weight repeated on every request — removed, cutting the prompt from 436 to 353 lines with no loss of business-logic guidance.

Two further rounds of tightening, both aimed at removing ambiguity rather than just shrinking text:

- **Category/team mapping unified** — previously a keyword list per category plus a separate category-to-team table; now one section per category, so adding a category later means editing one block, not two. Net effect: 218 lines despite *adding* the two rules below, because removing duplication outweighed the added guidance.
- **Explicit, deterministic tie-break rules** replace vaguer judgment calls:
  - *Billing vs. Sales* on pricing questions: does the customer already have this charge/plan (Billing), or are they asking about one they don't have yet (Sales)?
  - *Ambiguous tickets*: if the message names a concrete symptom, route on that symptom even with missing details; if it's vague with no concrete signal at all ("something's wrong"), default to `General / Low / Support` — the same default used for very-short messages, and for the same reason.

</details>

<details>
<summary><strong>Structured Outputs (replaces prompt-only JSON enforcement)</strong></summary>

<br>

Previously, JSON validity depended entirely on the model following prose instructions, with `json_repair` and a blind retry loop patching up whatever came back.

Now, `TicketResponse` (in `app/schemas/ticket_schema.py`) is passed directly as `text_format` to `client.responses.parse()`. OpenAI converts that Pydantic model into a strict JSON Schema and constrains its own token generation to match it — the response is *guaranteed* valid JSON with exactly the right fields and types. `response.output_parsed` comes back as an already-validated `TicketResponse` instance. `json_repair` is gone; it has nothing left to repair.

</details>

<details>
<summary><strong>Retry Strategy</strong></summary>

<br>

`app/services/router_service.py` retries only failures a second attempt can plausibly fix:

| Error type | Retried? | Why |
|---|---|---|
| Rate limit, timeout, network error, 5xx server error | Yes, with exponential backoff | Transient — likely to succeed a moment later |
| Authentication error, invalid request | No — raised immediately | Retrying repeats the same failure |
| `output_parsed is None` (model refusal / unparseable) | No — raised immediately | A content/schema failure, not an infrastructure one |

Every OpenAI call has `timeout=15` seconds, so a hung request can't block the server indefinitely, and logs real input/output token usage.

**Why these specific numbers** (full rationale as comments in `router_service.py`):

- `timeout=15` — long enough that a normal response (1–4s) never times out; short enough that a genuinely hung request fails fast.
- `MAX_ATTEMPTS=2` (one retry) — this blocks an interactive request, so more retries trade reliability for user-visible delay. One retry recovers the common case (a single dropped request).
- `temperature=0.2` — low but not `0.0`. The answer space is small and fixed (5 categories × 3 priorities × 5 teams), so classification stays effectively deterministic — but `0.0` makes `summary`/`suggested_reply` read as a robotic repeated template across tickets.

</details>

<details>
<summary><strong>Validation</strong></summary>

<br>

`TicketResponse` uses `Literal` types instead of plain strings, so an out-of-vocabulary value fails validation instead of silently reaching the database:

- `category`: `Billing | Technical | Sales | General | Network`
- `priority`: `High | Medium | Low`
- `assigned_team`: `Finance | Engineering | Network Operations | Sales | Support`
- `sentiment`: `Positive | Neutral | Angry`
- `confidence`: `int`, `0–100`
- `escalation_needed`: `bool`
- `needs_human_review`: `bool` — the model provides a best-effort value, but `route_ticket()` always overwrites it deterministically from `confidence < CONFIDENCE_REVIEW_THRESHOLD` (50) before it's returned, so it can't drift from the threshold due to model inconsistency.
- Incoming `message`: capped at `max_length=4000`

`TicketRouting` is an exported alias for `TicketResponse` (same model) — see `backend/app/prompts/PROMPT_CHANGELOG.md` for why this project uses Structured Outputs (`text_format=`) rather than `response_format={"type": "json_object"}` + manual `model_validate_json()`.

### Edge Cases

The prompt and the evaluation set both exercise 3 required cases:

1. **Angry tone** — anger alone must not force High priority; the underlying issue must be genuinely serious too.
2. **Very short message** ("Help", "Not working") — defaults to `General / Low / Support` rather than inventing detail.
3. **Ambiguous ticket** — the model picks the most likely category and states its uncertainty in `reason`, never fabricating specifics.

</details>

<details>
<summary><strong>Scalability & Backend Hardening</strong></summary>

<br>

Kept deliberately modest — this project's stated goal is a strong demo, not production scale — but a few close-to-free improvements were made:

- `category`, `priority`, and `created_at` are indexed (applied live via `CREATE INDEX IF NOT EXISTS`, no data loss).
- `pool_pre_ping=True` on the SQLAlchemy engine, so a connection dropped by the DB while idle surfaces as a retry, not a confusing failure.
- `GET /tickets` accepts optional `limit`/`offset` query params, with total row count exposed via an `X-Total-Count` header — the JSON body stays a bare array, so existing callers see no difference.
- `route_ticket()` is cached with `functools.lru_cache` on the exact message text. An identical repeat (a demo re-run, a double-submit) returns instantly and skips a paid GPT-4.1 call. A failed call is never cached, so failures are always retried for real.
- CORS now allows only `GET`/`POST` and `Content-Type` instead of `"*"`.

**Not done, on purpose:** API versioning, response caching, async request handling — each would be a real architecture change, not a same-behavior hardening pass.

</details>

<details>
<summary><strong>Code Quality</strong></summary>

<br>

- `ruff check .` runs clean (config in `backend/pyproject.toml`).
- Dark mode via CSS custom properties (`prefers-color-scheme: dark`) — verified visually.
- Verified at a 390px mobile viewport: no horizontal overflow, correct responsive stacking, and the Ticket History table scrolls inside its own container. Every interactive button has visible text alongside its icon.

</details>

## Learnings

[`LEARNINGS.md`](LEARNINGS.md) covers, in the project's own words: which prompt versions failed and why (with the actual before/after in `backend/app/prompts/PROMPT_CHANGELOG.md`), the hardest edge case and why it's structurally hard rather than a wording problem, and what's next (a real human-review queue, a feedback loop, a temperature comparison, multi-language support, RAG-grounded replies).

## Project Limitations

- **English-only.** The prompt and 20-ticket evaluation set are English-only; messages in other languages are neither explicitly handled nor tested.
- **`needs_human_review` is a flag, not a queue.** It surfaces as a banner on the latest result and a count on the dashboard — there's no dedicated filtered view for a reviewer to work through flagged tickets.
- **No feedback loop.** A human correcting an AI decision isn't captured anywhere, so real-world accuracy beyond the 20-ticket evaluation set isn't measured.
- **`suggested_reply` isn't grounded in real data.** It's generated from the ticket text alone (explicitly instructed not to invent account/order details), so it stays generic rather than referencing actual policy or history.
- **Single fixed `temperature=0.2`.** The value has a written rationale but hasn't been measured against alternatives on the evaluation set.
- **Deliberately modest scale.** Per the "Scalability & Backend Hardening" deep dive above, this project targets a strong demo, not production scale — no API versioning, no async request handling.
- **Self-reported model confidence isn't fully reliable.** Per the evaluation results above, confidence was not measurably lower on the one incorrect prediction in the latest run.

## Future Improvements

- A dedicated human-review queue (filtered by `needs_human_review=true`), not just a badge/count.
- A feedback loop that logs human corrections (`corrected_category`/`corrected_priority`) to measure real-world accuracy over time.
- A temperature comparison (0, 0.3, 0.7) against the labeled evaluation set to confirm or revise the current `0.2` choice.
- Explicit, tested multi-language support.
- RAG-grounded `suggested_reply`, referencing an actual knowledge base/macros library instead of ticket text alone.

## Screenshots

_Placeholder — add screenshots of the ticket submission form, the routing result, and the analytics dashboard here before publishing._

## License

This project is licensed under the [MIT License](LICENSE).
