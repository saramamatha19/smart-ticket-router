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
backend/app/{router,services,prompts,schemas,models,crud,database}
backend/{evaluation,tests,scripts}
frontend/src/{pages,components,services}
```

**Backend** (`backend/`)

| Path | Purpose |
|---|---|
| `app/router/routes.py` | API endpoints — `POST /route-ticket`, `GET /tickets`, `GET /tickets/stats` |
| `app/services/router_service.py` | OpenAI call, retry/backoff, caching, human-review logic |
| `app/prompts/ticket_prompt.py` | The system prompt sent to GPT-4.1 |
| `app/prompts/versions/` | `v1.txt`–`v5.txt`, the prompt's revision history |
| `app/prompts/PROMPT_CHANGELOG.md` | What changed between each prompt version, and why |
| `app/schemas/ticket_schema.py` | Pydantic request/response models — also the AI's JSON Schema |
| `app/models/ticket.py` | SQLAlchemy ORM table (`tickets`) |
| `app/crud/ticket_crud.py` | Database read/write functions |
| `app/database/connection.py` | Engine, session factory, `Base` class |
| `app/database/init_db.py` | `create_all()` table setup |
| `evaluation/labeled_tickets.py` | 20 hand-labeled tickets with expected category/priority/team |
| `evaluation/run_evaluation.py` | Runs the labeled set through the live classifier, writes `evaluation.md` |
| `evaluation/evaluation.md` | Latest recorded accuracy results |
| `tests/` | pytest suite (router service, routes, schema, CRUD) |
| `scripts/seed_tickets.py` | Posts 20 demo tickets to a running API |
| `scripts/batch_summary.py` | Runs a batch through `route_ticket_with_diagnostics()`, prints a parse-rate/latency/token summary |
| `main.py` | FastAPI app, CORS config, health/db-check endpoints |

**Frontend** (`frontend/`)

| Path | Purpose |
|---|---|
| `src/pages/UserPage.jsx` | Ticket submission page |
| `src/pages/AdminPage.jsx` | Analytics dashboard page |
| `src/components/` | `TicketForm`, `TicketResult`, `TicketHistory`, `DashboardStats`, `TicketChart`, `TimeSavings`, `Toast`, `Spinner`, `Badge` |
| `src/services/api.js` | Axios client (base URL from `VITE_API_URL`) |

`LEARNINGS.md` (repo root) — project retrospective: what failed, the hardest edge case, and what's next.

## How It Works

1. **Submit.** A user types a message into the submission form. The frontend sends the raw text to `POST /route-ticket`.
2. **Validate.** A blank or whitespace-only message is rejected at the Pydantic layer with a 422 — before any AI call happens.
3. **Classify.** The backend hands the message to `route_ticket()`, which sends it, with the system prompt, to GPT-4.1 via the OpenAI Responses API using `text_format=TicketBatchResponse`. Structured Outputs constrains the model's own token generation, so the response is guaranteed to be valid JSON containing a `tickets` array — one fully-classified entry per distinct request in the message, even if the message mixed a real support issue with something unrelated like a joke.
4. **Handle failures.**
   - A transient error (rate limit, timeout, network issue, 5xx) is retried once with exponential backoff.
   - An authentication error, invalid request, or unparseable response is raised immediately — retrying would only repeat the same failure.
   - An identical repeat message is served from an in-process cache instead of triggering another paid API call.
5. **Recompute review flag.** For each entry, the backend overwrites `needs_human_review` based on whether `confidence` fell below 50 — regardless of what the model itself reported for that field.
6. **Persist.** Each classified entry is saved as its own row in PostgreSQL; rows from a multi-intent submission share a `group_id` so they can still be traced back to one original message.
7. **Respond & display.** The full list is returned to the frontend, which renders one result card per entry. The admin dashboard separately polls `GET /tickets` and `GET /tickets/stats` to show ticket history and aggregate analytics.

## AI Design

- **Prompt engineering** — `app/prompts/ticket_prompt.py` defines the categories, priorities, and teams with keyword guidance, plus deterministic tie-break rules (e.g. Billing vs. Sales) instead of "best judgment," and a MULTI-INTENT section on when to split a message into multiple `tickets` entries.
- **Structured Outputs** — `TicketBatchResponse` is passed as `text_format` to `client.responses.parse()`. OpenAI constrains generation to match its JSON Schema exactly, so `response.output_parsed` is already validated — no repair step needed.
- **Why Structured Outputs** — they replace prose rules ("return ONLY JSON") that occasionally failed anyway. The API now makes malformed output impossible, not just discouraged.
- **Confidence score** — an integer 0–100 self-reported per classification; the prompt asks for lower values on vague/short tickets, higher on explicit ones.
- **Human review logic** — `needs_human_review` is recomputed server-side as `confidence < 50` in `_apply_human_review_flag()`, overriding the model's own guess so it can't drift from the threshold.
- **Retry strategy** — one retry with exponential backoff for transient errors (rate limit, timeout, network, 5xx); auth/invalid-request errors fail immediately. 15s timeout; temperature fixed at `0.2` (keeps classification effectively deterministic, but not so low that generated text feels templated).
- **Error handling** — `route_ticket()` raises on failure; the route handler logs details server-side and returns a generic 502. `route_ticket_with_diagnostics()` never raises — it returns a structured result dict instead, for batch/CLI use (`scripts/batch_summary.py`).

## Prompt Evolution

Five documented revisions (`backend/app/prompts/versions/v1.txt`–`v5.txt`, summarized in `backend/app/prompts/PROMPT_CHANGELOG.md`):

- **v1 → v2** — Replaced prose-based format policing with OpenAI Structured Outputs, enforcing the schema mechanically instead of hoping the model complies.
- **v2 → v3** — Unified the category-keyword/team mapping into one block; replaced two vague "best judgment" calls with deterministic tie-break rules.
- **v3** — Added `needs_human_review`, so a low-confidence classification gets flagged instead of looking as certain as any other.
- **v3 → v4** — Added multi-intent support (`TicketBatchResponse` wrapping `tickets: list[TicketResponse]`).
- **v4 → v5 (current)** — Added `Off-Topic → Unassigned` so unrelated content (jokes, trivia) stops landing in Support's queue.

## Evaluation

`labeled_tickets.py` hand-labels 20 tickets with an expected category/priority/team **before** the classifier runs — labels are never adjusted after seeing predictions. `run_evaluation.py` runs all 20 through the live classifier and writes `evaluation.md`.

```bash
cd backend
source venv/bin/activate
python evaluation/run_evaluation.py
```

**Latest results:**

| Metric | Result |
|---|---|
| Overall accuracy (category + priority + team all correct) | 95.0% (19/20) |
| Category accuracy | 100.0% |
| Priority accuracy | 95.0% |
| Team accuracy | 100.0% |
| Avg. confidence on correct predictions | 92.2 |
| Avg. confidence on incorrect predictions | 95.0 |

- The one miss: a Billing ticket predicted `High` instead of `Medium` — not one of the 3 designed edge cases.
- Confidence was **not** lower on that miss, so self-reported confidence alone isn't a reliable correctness signal.
- Accuracy is also broken down by confidence band (90–100, 70–89, below 70) to check calibration, not just a single average.

## Testing

**Backend — 28 pytest tests:**

- `test_router_service.py` (16) — valid & multi-intent responses, caching, retries, non-retryable errors, the 3 required edge cases, `needs_human_review` recompute, `route_ticket_with_diagnostics()`'s success/error contract.
- `test_routes.py` (2) — clean 502 with no leaked detail, 422 on a blank message.
- `test_ticket_crud.py` (1) — real-database pagination/ordering check (skips if no DB is reachable).
- `test_ticket_schema.py` (9) — message validation, non-empty `tickets` constraint, `Off-Topic`/`Unassigned` pairing.

All OpenAI calls are mocked — no real network calls, no API cost.

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

**Frontend — 10 Vitest + React Testing Library tests:**

- `Badge.test.jsx` (4) — label rendering, priority/sentiment color classes, default fallback.
- `TicketForm.test.jsx` (4) — inline validation, submit/clear, loading state, server error display.
- `TicketChart.test.jsx` (2) — empty state, tab switching.

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

**Submit a Ticket** — a multi-intent message (a billing complaint, a crash report, a vague account issue, and an off-topic question, all in one submission):

![Submit a Ticket page](docs/screenshots/submit-ticket.png)

**AI Analysis** — the multi-intent banner, plus each independently-routed result:

| Billing (High, escalation flagged) | Technical (High, escalation flagged) |
|---|---|
| ![Billing result](docs/screenshots/result-billing.png) | ![Technical result](docs/screenshots/result-technical.png) |

| General (ambiguous, `needs_human_review`) | Off-Topic (Unassigned) |
|---|---|
| ![Ambiguous General result](docs/screenshots/result-general-ambiguous.png) | ![Off-Topic result](docs/screenshots/result-offtopic.png) |

**Admin Dashboard** — stats, measured AI routing speed, and ticket distribution by category:

![Admin dashboard overview](docs/screenshots/admin-dashboard.png)

**Ticket distribution by priority**, and **ticket history filtered to `needs_human_review` only**:

| Priority distribution | Needs-review filter |
|---|---|
| ![Priority distribution](docs/screenshots/admin-priority-chart.png) | ![Needs human review filter](docs/screenshots/admin-needs-review-filter.png) |

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
