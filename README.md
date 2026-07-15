# Smart Ticket Router

An AI-powered support ticket classifier. A raw customer message goes in, and a fully-validated routing decision comes back: category, priority, assigned team, sentiment, confidence score, a suggested reply, and more, generated in a single GPT-4.1 call and guaranteed to match an exact schema via OpenAI Structured Outputs. A single message can also contain more than one independent request (e.g. a billing issue and an unrelated question); the router splits and classifies each one separately instead of forcing a single label onto a mixed message.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai&logoColor=white)

---

## Features

- **AI-powered ticket classification** — category, priority, assigned team, sentiment, confidence, resolution ETA, and a suggested reply, generated in one GPT-4.1 call via the OpenAI Responses API.
- **Multi-intent splitting** — a message with more than one independent request (e.g. "I was charged twice. Also, tell me a joke.") comes back as one fully-classified entry per request instead of one blended guess.
- **Structured Outputs** — `client.responses.parse(text_format=TicketBatchResponse)` constrains the model's token generation to an exact JSON Schema, so a malformed or off-schema response is structurally impossible, not just discouraged by prompt wording.
- **Pydantic validation** — `Literal` types on category/priority/team/sentiment reject any out-of-vocabulary value before it reaches the database; `message` is capped at 4000 characters and rejected if blank.
- **Confidence score** — every classification includes a 0–100 self-reported confidence, shown as a meter in the UI.
- **Human review flag** — `needs_human_review` is recalculated server-side from `confidence < 50`, overwriting the model's own guess so it can never drift from the threshold.
- **Retry logic** — transient OpenAI errors (rate limits, timeouts, network errors, 5xx) get one retry with exponential backoff; authentication/invalid-request errors and unparseable responses fail immediately instead of retrying a failure that can't self-heal.
- **Prompt versioning** — five documented prompt revisions (`v1.txt`–`v5.txt`) with a changelog explaining what broke and what fixed it at each step.
- **Evaluation framework** — a 20-ticket hand-labeled set, graded automatically against the live classifier, reporting real accuracy and confidence-calibration numbers.
- **Automated tests** — 28 backend pytest tests and 10 frontend Vitest/React Testing Library tests.
- **React frontend** — a two-page app: a ticket submission form and an admin dashboard with history, filtering, search, CSV export, and analytics charts.
- **FastAPI backend** — a thin, typed API layer over the AI pipeline and a PostgreSQL-backed ticket store.

## Architecture

```
User
  │  types a support message
  ▼
React (UserPage → TicketForm)
  │  POST /route-ticket { message }
  ▼
FastAPI (app/router/routes.py)
  │  calls route_ticket(message)
  ▼
OpenAI GPT-4.1 (app/services/router_service.py)
  │  client.responses.parse(text_format=TicketBatchResponse)
  ▼
Structured Output
  │  guaranteed valid JSON: { tickets: [TicketResponse, ...] }
  ▼
Validation
  │  Pydantic Literal types + needs_human_review recomputed from confidence
  ▼
Database (PostgreSQL via SQLAlchemy)
  │  one row per classified sub-ticket, tied by group_id if split
  ▼
Response
  │  list[TicketResponse] returned to the caller
  ▼
UI (TicketResult / TicketHistory / DashboardStats)
```

**Request flow, step by step:**

1. The frontend posts `{ message }` to `POST /route-ticket` (max 4000 characters, rejected if blank — enforced by Pydantic before any OpenAI call is made).
2. `app/router/routes.py` calls `route_ticket(message)`.
3. `app/services/router_service.py` sends the message and the system prompt to GPT-4.1 via `client.responses.parse(text_format=TicketBatchResponse)`.
4. OpenAI Structured Outputs guarantees the response is valid JSON matching `TicketBatchResponse` — a `tickets` array with one entry per distinct request found in the message.
5. For each entry, `needs_human_review` is overwritten deterministically from `confidence < 50` (never trusted from the model's own guess for that field).
6. Every entry is saved as its own row in PostgreSQL — entries from the same submission share a `group_id` — and the full list is returned to the frontend.

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI 0.139, Python 3.11+, Uvicorn |
| **Frontend** | React 19, Vite 8, React Router 7, Axios, Recharts, lucide-react |
| **AI** | OpenAI GPT-4.1 via the Responses API (`client.responses.parse`, Structured Outputs) |
| **Database** | PostgreSQL, SQLAlchemy 2.0, psycopg2 |
| **Testing** | pytest (backend), Vitest + React Testing Library (frontend) |
| **Development Tools** | ruff (linting), python-dotenv, ESLint |

## Project Structure

```
backend/
  app/
    router/routes.py         API endpoints: POST /route-ticket, GET /tickets, GET /tickets/stats
    services/router_service.py  OpenAI call, retry/backoff, caching, human-review logic
    prompts/ticket_prompt.py    The system prompt sent to GPT-4.1
    prompts/versions/           v1.txt – v5.txt, the prompt's revision history
    prompts/PROMPT_CHANGELOG.md What changed between each prompt version, and why
    schemas/ticket_schema.py    Pydantic request/response models — also the AI's JSON Schema
    models/ticket.py            SQLAlchemy ORM table (tickets)
    crud/ticket_crud.py         Database read/write functions
    database/connection.py      Engine, session factory, Base class
    database/init_db.py         create_all() table setup
  evaluation/
    labeled_tickets.py          20 hand-labeled tickets with expected category/priority/team
    run_evaluation.py           Runs the labeled set through the live classifier, writes evaluation.md
    evaluation.md                Latest recorded accuracy results
  tests/                       pytest suite (router service, routes, schema, CRUD)
  scripts/
    seed_tickets.py            Posts 20 demo tickets to a running API
    batch_summary.py           Runs a batch through route_ticket_with_diagnostics(), prints parse-rate/latency/token summary
  main.py                      FastAPI app, CORS config, health/db-check endpoints
frontend/
  src/
    pages/UserPage.jsx          Ticket submission page
    pages/AdminPage.jsx         Analytics dashboard page
    components/                 TicketForm, TicketResult, TicketHistory, DashboardStats, TicketChart, TimeSavings, Toast, Spinner, Badge
    services/api.js             Axios client (base URL from VITE_API_URL)
LEARNINGS.md                  Project retrospective: what failed, hardest edge case, what's next
```

## How It Works

A user types a message into the submission form and submits it. The frontend sends the raw text to `POST /route-ticket`; a blank or whitespace-only message is rejected at the Pydantic layer with a 422 before any AI call happens. The backend hands the message to `route_ticket()`, which sends it, together with the system prompt, to GPT-4.1 through the OpenAI Responses API using `text_format=TicketBatchResponse`. Because Structured Outputs constrains the model's own token generation, the response is guaranteed to be valid JSON containing a `tickets` array — one fully-classified entry per distinct request in the message, even if the message mixed a real support issue with something unrelated like a joke.

For each entry, the backend overwrites `needs_human_review` based on whether `confidence` fell below 50, regardless of what the model itself reported for that field. If the OpenAI call fails with a transient error (rate limit, timeout, network issue, 5xx), it is retried once with exponential backoff; an authentication error, invalid request, or an unparseable response is raised immediately since retrying would only repeat the same failure. An identical repeat message is served from an in-process cache instead of triggering another paid API call.

Each classified entry is saved as its own row in PostgreSQL — rows from a multi-intent submission share a `group_id` so they can still be traced back to one original message — and the full list is returned to the frontend, which renders one result card per entry. The admin dashboard separately polls `GET /tickets` and `GET /tickets/stats` to show ticket history and aggregate analytics.

## AI Design

**Prompt engineering.** The system prompt (`app/prompts/ticket_prompt.py`) defines the allowed categories (Billing, Technical, Sales, General, Network, Off-Topic), priorities (High/Medium/Low), and teams, with keyword guidance and worked examples for each. It states explicit, deterministic tie-break rules rather than leaving decisions to "best judgment": Billing-vs-Sales pricing questions are decided by whether the customer already holds the charge/plan in question, and ambiguous tickets are routed on any concrete symptom if one exists, defaulting to `General / Low / Support` only when there is truly no signal at all. It also defines a MULTI-INTENT MESSAGES section instructing the model when to split a message into multiple `tickets` entries and when not to (a single issue described across several sentences is still one ticket).

**Structured Outputs.** `TicketBatchResponse` (in `app/schemas/ticket_schema.py`) is passed directly as `text_format` to `client.responses.parse()`. OpenAI converts that Pydantic model into a strict JSON Schema and constrains generation to match it exactly, so `response.output_parsed` comes back as an already-validated object — no markdown fences, no missing fields, no manual JSON parsing or repair step.

**Why Structured Outputs were chosen.** Before this, format compliance depended entirely on prose instructions ("return ONLY JSON," a "FINAL CHECK" compliance checklist) plus a blind repair pass on whatever came back — and it still occasionally failed, because nothing actually forced the model to comply. Structured Outputs turns "please return valid JSON" into "the API will not let you return anything else," which let the formatting-policing section of the prompt be deleted entirely.

**Confidence score.** The model reports an integer 0–100 confidence with every classification, with explicit prompt guidance to use lower values for short, vague, or ambiguous tickets and higher values when the issue and category are explicit.

**Human review logic.** `needs_human_review` is a real schema field the model fills in, but `app/services/router_service.py`'s `_apply_human_review_flag()` always overwrites it with `confidence < CONFIDENCE_REVIEW_THRESHOLD` (50) before the response leaves `route_ticket()`. This guarantees the flag matches the threshold exactly, rather than depending on the model doing that arithmetic correctly and consistently on every call.

**Retry strategy.** Only transient infrastructure errors (`RateLimitError`, `APITimeoutError`, `APIConnectionError`, `InternalServerError`) are retried, once, with exponential backoff (`BACKOFF_BASE_SECONDS * 2^(attempt-1)`). Authentication and invalid-request errors are raised immediately, since a second attempt would fail identically. Every call has a 15-second timeout — long enough that a normal 1–4s response never trips it, short enough that a genuinely hung request fails fast. Temperature is fixed at 0.2: low enough to keep classification effectively deterministic over a small, fixed answer space, but not `0.0`, so generated text (`summary`, `suggested_reply`) doesn't read as a robotic repeated template.

**Error handling.** `route_ticket()` raises on failure — the route handler in `app/router/routes.py` catches any exception, logs the full detail server-side, and returns a 502 with a generic message, never leaking exception internals to the caller. For batch/CLI use where a single bad ticket shouldn't halt a run, `route_ticket_with_diagnostics()` never raises: it returns a structured `{success, tickets, error, latency_ms, input_tokens, output_tokens, total_tokens}` dict instead, used by `scripts/batch_summary.py`.

## Prompt Evolution

The system prompt went through five documented revisions (`backend/app/prompts/versions/v1.txt`–`v5.txt`, summarized in `backend/app/prompts/PROMPT_CHANGELOG.md`):

- **v1 → v2:** Removed prose-based format policing ("return ONLY JSON," a "FINAL CHECK" checklist) in favor of OpenAI Structured Outputs, which enforces the schema mechanically instead of hoping the model complies.
- **v2 → v3:** Unified the previously-duplicated category-keyword list and category→team mapping into one block per category, and replaced two "use your best judgment" decision points (Billing-vs-Sales, ambiguous tickets) with explicit, deterministic tie-break rules.
- **v3:** Added the `needs_human_review` field, bundled into the same revision, so a low-confidence classification could be flagged for a human rather than displayed identically to a confident one.
- **v3 → v4:** Added multi-intent support — a `TicketBatchResponse` wrapping a `tickets: list[TicketResponse]` — so a message with more than one independent request no longer forces a single blended classification.
- **v4 → v5 (current):** Added the `Off-Topic → Unassigned` category so content unrelated to the product (jokes, trivia, small talk) stops landing in the Support team's queue alongside real work.

## Evaluation

`backend/evaluation/labeled_tickets.py` hand-labels 20 sample tickets with an expected category/priority/team **before** the classifier is run against them — labels are not adjusted after seeing the model's predictions. `backend/evaluation/run_evaluation.py` runs all 20 through the live classifier (`route_ticket`, real GPT-4.1 calls) and writes the results to `backend/evaluation/evaluation.md`.

```bash
cd backend
source venv/bin/activate
python evaluation/run_evaluation.py
```

**Latest recorded results** (from `backend/evaluation/evaluation.md`):

| Metric | Result |
|---|---|
| Overall accuracy (category + priority + team all correct) | 95.0% (19/20) |
| Category accuracy | 100.0% |
| Priority accuracy | 95.0% |
| Team accuracy | 100.0% |
| Avg. confidence on correct predictions | 92.2 |
| Avg. confidence on incorrect predictions | 95.0 |

The one miss was a Billing ticket ("My invoice shows the wrong amount...") predicted `High` instead of `Medium` — not one of the three designed edge cases, which is itself a signal that real-world ambiguity doesn't only show up where it was anticipated. Confidence was **not** lower on that miss, so the report explicitly notes that self-reported model confidence should not be treated as a reliable correctness signal on its own. The evaluation also breaks accuracy down by confidence band (90–100, 70–89, below 70) to check whether confidence actually tracks correctness rather than relying on a single average that could hide a badly-miscalibrated band.

## Testing

**Backend — 28 pytest tests** across four files:

- `test_router_service.py` (16 tests): a valid response, multi-intent splitting, response caching (including that different messages aren't conflated), an unparseable response raising without retrying, retry-then-succeed, retry-exhausted, a non-retryable auth error, the 3 required edge cases (angry tone, very short message, ambiguous ticket), `needs_human_review` being recalculated from confidence regardless of the model's own guess (both directions), and `route_ticket_with_diagnostics()`'s success/error contract.
- `test_routes.py` (2 tests): `/route-ticket` returns a 502 without leaking exception detail on failure, and a 422 for a blank message.
- `test_ticket_crud.py` (1 test): an integration test against a real database proving `GET /tickets` pagination and ordering — skips (not fails) if no database is reachable.
- `test_ticket_schema.py` (9 tests): message validation (blank, whitespace, max length), `TicketBatchResponse`'s non-empty `tickets` constraint, and the `Off-Topic`/`Unassigned` category/team pairing.

All OpenAI-dependent tests mock `client.responses.parse`, so the suite makes no real network calls and spends no API credits.

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

**Frontend — 10 Vitest + React Testing Library tests:**

- `Badge.test.jsx` (4 tests): renders nothing without a label, applies the correct priority/sentiment color class, falls back to a default style for an unrecognized value.
- `TicketForm.test.jsx` (4 tests): inline validation on empty submit, submits and clears the textarea, disables inputs while loading, surfaces a server-side error passed in via props.
- `TicketChart.test.jsx` (2 tests): shows an empty state with no data, switches between category/priority/sentiment tabs.

```bash
cd frontend
npm run test
```

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (running locally or accessible remotely)
- An OpenAI API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in real values (never commit `.env` — it's gitignored):

```bash
cp .env.example .env
```

Optional demo data:

```bash
python scripts/seed_tickets.py     # posts 20 sample tickets to a running API
python scripts/batch_summary.py    # real GPT-4.1 calls; prints parse-rate/latency/token summary
```

Run the API:

```bash
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The app is now available at `http://localhost:5173`.

## Environment Variables

| File | Variable | Description |
|---|---|---|
| `backend/.env` | `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:password@localhost:5432/smart_ticket_router`. |
| `backend/.env` | `OPENAI_API_KEY` | OpenAI API key used for GPT-4.1 classification calls. |
| `frontend/.env` | `VITE_API_URL` | Base URL the frontend uses to reach the backend API, e.g. `http://127.0.0.1:8000`. |

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — confirms the API is running. |
| `GET` | `/test-db` | Verifies database connectivity; returns 503 if unreachable. |
| `POST` | `/route-ticket` | Classifies a ticket message; returns a list of one or more routing decisions. |
| `GET` | `/tickets` | Lists saved tickets, newest first. Optional `limit` (1–500) and `offset` query params; total row count is returned via the `X-Total-Count` header. |
| `GET` | `/tickets/stats` | Returns dashboard analytics: totals by priority, category, sentiment, and a `needs_human_review_count`. |

**`POST /route-ticket`**

```bash
curl -X POST http://localhost:8000/route-ticket \
  -H "Content-Type: application/json" \
  -d '{"message": "My invoice shows a charge I do not recognize."}'
```

```json
[
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
]
```

A message with more than one independent request returns more than one entry in this array, each with its own category/team/priority.

**`GET /tickets/stats`**

```json
{
  "total": 42,
  "by_priority": { "High": 10, "Medium": 20, "Low": 12 },
  "by_category": { "Billing": 8, "Technical": 15, "Sales": 9, "General": 6, "Network": 3, "Off-Topic": 1 },
  "by_sentiment": { "Positive": 5, "Neutral": 30, "Angry": 7 },
  "needs_human_review_count": 4
}
```

## Screenshots

_Placeholder — add screenshots of the ticket submission form, the AI analysis result, and the admin dashboard here before publishing._

## Limitations

- **English-only.** The prompt and 20-ticket evaluation set are English-only; other languages are neither explicitly handled nor tested.
- **`needs_human_review` is a flag, not a queue.** It surfaces as a banner on the latest result and a count/filter toggle in ticket history — there's no dedicated queue view built specifically for reviewers to work through.
- **No feedback loop.** A human correcting an AI decision isn't captured anywhere, so real-world accuracy beyond the 20-ticket evaluation set isn't measured.
- **`suggested_reply` isn't grounded in real data.** It's generated from the ticket text alone (explicitly instructed not to invent account/order details), so it stays generic rather than referencing actual policy or history.
- **Single fixed `temperature=0.2`.** The value has a written rationale but hasn't been measured against alternatives on the evaluation set.
- **Deliberately modest scale.** This project targets a strong demo, not production scale — no API versioning, no async request handling.
- **Self-reported model confidence isn't fully reliable.** Confidence was not measurably lower on the one incorrect prediction in the latest evaluation run.

## Future Improvements

- A dedicated human-review queue (filtered by `needs_human_review=true`), not just a badge/toggle.
- A feedback loop that logs human corrections (`corrected_category`/`corrected_priority`) to measure real-world accuracy over time.
- A temperature comparison (0, 0.3, 0.7) against the labeled evaluation set to confirm or revise the current `0.2` choice.
- Explicit, tested multi-language support.
- RAG-grounded `suggested_reply`, referencing an actual knowledge base/macros library instead of ticket text alone.

## Learning Outcomes

This project is a working demonstration of:

- **Structured, schema-constrained LLM output** — using OpenAI Structured Outputs (`text_format=`) so a Pydantic model doubles as both the API's response contract and a hard guarantee on the model's generation, eliminating an entire class of malformed-JSON failures by construction rather than by prompt-worded convention.
- **Separating format enforcement from reasoning** — the prompt's job is narrowed to the actual classification logic; the schema's job is the shape of the answer. Conflating the two (as in early prompt versions) makes both harder to get right.
- **Deterministic tie-breaks over "best judgment"** — replacing ambiguous prompt instructions with explicit decision rules, learned directly from observing inconsistent outputs across runs.
- **Not trusting a model's self-report blindly** — `needs_human_review` is recomputed server-side from `confidence` rather than accepted as-is, and the evaluation harness explicitly checks whether confidence tracks correctness instead of assuming it does.
- **Resilience engineering for a synchronous, user-facing AI call** — distinguishing retryable infrastructure failures from non-retryable content/auth failures, bounding retries and timeouts against real measured latency, and caching a pure function of its input.
- **Evaluation as evidence, not assumption** — a hand-labeled set with expected answers fixed before the model sees them, graded automatically, with confidence-calibration analysis rather than a single headline accuracy number.
- **Iterative documentation of failure** — prompt versions, a changelog, and a learnings doc that record what didn't work and why, not just the current state.

## License

This project is licensed under the [MIT License](LICENSE).
