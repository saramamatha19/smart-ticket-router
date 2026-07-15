# Prompt Changelog

The versions in `versions/` (`v1.txt`, `v2.txt`, `v3.txt`, `v4.txt`) track
the system prompt's evolution. `v4.txt` is byte-for-byte what ships in
`ticket_prompt.py` today. `v1.txt` and `v2.txt` are reconstructed from the
evolution already narrated in the root `README.md`'s "Prompt Engineering"
deep dive (which described the changes in prose before this folder
existed) — they are not recovered from git history, because this project
was not under version control until this pass. They're accurate to what
actually changed and why; treat the exact line-for-line wording as a
faithful reconstruction, not a byte-for-byte historical artifact.

## v1 -> v2: stop policing format, let Structured Outputs do it

**What broke:** v1 spent roughly a third of its length on
formatting instructions — "return ONLY JSON," "no markdown fences," a
"FINAL CHECK" compliance checklist re-verifying bracket-matching and key
names before every response. This was necessary at the time because
format compliance depended entirely on the model following prose
instructions, patched up further by a `json_repair` pass on whatever
came back. Two concrete problems: (1) the formatting section competed
with the actual classification guidance for the model's attention on
every single request, and (2) it was still occasionally wrong — a
model that forgets a closing brace once every N requests isn't fixed by
asking it more firmly to remember the brace.

**Fix:** Adopted OpenAI Structured Outputs
(`client.responses.parse(text_format=TicketResponse)` in
`router_service.py`). The API now constrains token generation to match
`TicketResponse`'s JSON Schema directly — malformed JSON became
structurally impossible instead of merely discouraged. `json_repair`
was removed (nothing left to repair), and the entire formatting/FINAL
CHECK section was deleted from the prompt, since prose can no longer
compensate for or interfere with something now enforced mechanically.

## v2 -> v3: stop duplicating the category/team mapping, add deterministic tie-breaks

**What broke:** v2 still had two separate structures for the same
information — a per-category keyword list, and a separate
category-to-team lookup table below it. Adding or adjusting a category
meant editing two places, and they could silently drift out of sync.
Separately, two decision points were left to unstated judgment calls
that produced inconsistent results across runs:
- Pricing questions ("what does this cost") could land in either
  Billing or Sales with no rule to decide between them.
- Ambiguous tickets ("something is wrong") were told to "use best
  judgment," which is not a rule — running the same message twice could
  plausibly produce two different categories.

**Fix:** Unified each category's keywords and its team into one block
(`CATEGORY GUIDELINES AND TEAM MAPPING` in `ticket_prompt.py`) so
there's exactly one place to edit per category. Added two explicit,
deterministic tie-break rules: Billing vs. Sales is decided by whether
the customer already has the charge/plan in question (default: Sales,
if no existing charge is named), and ambiguous tickets are routed on
any concrete symptom if one exists, defaulting to
`General / Low / Support` only when there is truly no signal at all —
the same default used for very-short messages, for the same reason.

## v3 -> v4: added `needs_human_review`

**What broke:** Nothing observed yet in production, since this ships
in the same pass as the field itself — but the risk this closes is
real: the model's own `confidence` score was displayed to a human, but
nothing acted on it. A ticket the model was 20% confident about was
stored and shown identically to one it was 99% confident about, with no
signal telling a reviewer which one to double-check.

**Fix:** Added `needs_human_review: bool` to the schema and prompt.
The model gives its own best-effort estimate, but
`app/services/router_service.py` deterministically overwrites it based
on `confidence < CONFIDENCE_REVIEW_THRESHOLD` (50, on this project's
0-100 scale) before the response ever leaves `route_ticket()` — so the
flag can't drift from the threshold due to model inconsistency, the
way a model-computed boolean could.

## v4 (current): multi-intent messages now split into multiple tickets

**What broke:** A single customer message could contain more than one
independent request (e.g. "I was charged twice, also tell me a joke"),
but the schema only ever had room for one classification. The model
was forced to pick a single category/team for the whole message, so
one of the requests was always silently dropped or blended into a
classification that didn't really fit it.

**Fix:** `TicketResponse` (one classification) is now wrapped in a new
`TicketBatchResponse` with a `tickets: list[TicketResponse]` field —
that's the actual `text_format` passed to Structured Outputs now (see
`router_service.py`). The prompt gained a MULTI-INTENT MESSAGES section
instructing the model to emit one fully-independent classification per
distinct request, with an explicit rule for when NOT to split (a single
issue described across multiple sentences or symptoms is still one
ticket). `route_ticket()` returns `list[TicketResponse]` — a
single-intent message still returns a one-item list, so this is not a
special case downstream, just the common case of the array. Each
sub-ticket is saved as its own row in `tickets`, tied together by a
shared `group_id` (see `app/models/ticket.py`) so history/reporting can
still tell they came from one submission.
