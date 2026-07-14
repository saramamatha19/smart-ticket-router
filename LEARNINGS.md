# Learnings

## Prompts that failed (and why)

Full before/after detail lives in `backend/app/prompts/PROMPT_CHANGELOG.md`
and the three versions under `backend/app/prompts/versions/`. Summary:

1. **Policing format in prose doesn't work reliably.** The original prompt
   spent roughly a third of its length telling the model to "return ONLY
   JSON," avoid markdown fences, and re-verify its own output against a
   "FINAL CHECK" list before responding. It still occasionally came back
   malformed, because compliance depended entirely on the model following
   instructions correctly on every single call — there was no mechanism
   forcing it. Switching to OpenAI Structured Outputs
   (`text_format=TicketResponse`) turned "please return valid JSON
   matching this shape" into "the API will not let you return anything
   else." The formatting section became dead weight and was deleted.

2. **Duplicated business rules drift out of sync.** Category keywords and
   the category→team mapping were originally two separate structures.
   Nothing enforced that they stayed consistent, so adding or adjusting a
   category meant remembering to edit both. They were unified into one
   block per category specifically so there's exactly one place to edit.

3. **"Use your best judgment" is not a rule.** Two decision points —
   Billing-vs-Sales pricing questions, and how to route a truly vague
   ticket — were originally left to unstated judgment, which meant the
   same message could plausibly get classified differently across runs.
   Both were replaced with an explicit, deterministic tie-break rule.
   This is the single biggest lesson from this project: an LLM prompt
   that says "decide sensibly" where a real decision procedure exists is
   a bug, not flexibility.

## Hardest edge case

**Ambiguous tickets with zero concrete signal** ("Something is wrong with
my account, please check.", "It failed again, not sure why."). These are
hard for a structural reason, not a prompt-wording reason: there is
genuinely no information in the message that maps to any category more
than any other. `backend/evaluation/labeled_tickets.py` says this
explicitly in its own notes — a different, equally defensible label could
be argued for these two tickets, and the expected labels were written
down before the model ever saw them, specifically so that ambiguity
couldn't be quietly resolved by tuning the labels to match the output
after the fact.

The fix isn't a smarter prompt — it's a documented default plus a
downstream release valve: default to `General / Low / Support` (the same
default as a too-short message, for the same reason — nothing concrete to
route on), and now, on top of that, flag `needs_human_review: true`
whenever confidence lands below `CONFIDENCE_REVIEW_THRESHOLD` (50, on this
project's 0–100 scale). A model that's honestly uncertain should say so
loud enough that a human sees it, rather than silently picking a default
and looking exactly as confident as a clear-cut ticket.

The measured cost of this ambiguity is in
`backend/evaluation/evaluation.md`: 95% priority accuracy (19/20), with
the one documented miss being a Billing ticket ("My invoice shows the
wrong amount...") predicted High instead of Medium — not one of the
three designed edge cases, which is itself a useful signal that
real-world ambiguity doesn't only show up where you planned for it.

## What we'd do next

- **Human-review queue, not just a flag.** `needs_human_review` currently
  surfaces as a badge on the single most recent result and a count on the
  dashboard. The natural next step is a dedicated filtered view (like
  `TicketHistory`'s existing filters, but defaulting to
  `needs_human_review=true`) so a reviewer has an actual queue to work
  through, not just a number to notice.
- **A real feedback loop.** Nothing today captures "a human corrected
  this AI decision." Adding a `corrected_category`/`corrected_priority`
  pair on review, even just logged rather than fed back into anything
  automated, would let a future pass measure real-world accuracy (not
  just the 20-ticket evaluation set) and identify which prompt rules are
  actually wrong versus just untested.
- **Temperature comparison.** Currently ships at a single fixed
  `temperature=0.2` with a written rationale, but never measured against
  the alternatives. Running the same 20 labeled tickets at 0, 0.3, and
  0.7 and tracking valid-parse rate and category/priority consistency
  (does the same ticket get the same answer twice?) would either
  confirm 0.2 was the right call or show it wasn't — right now that's an
  informed guess, not a measurement. Skipped in this pass to prioritize
  the must-do list first; the harness in `run_evaluation.py` already has
  everything needed to run it.
- **Multi-language support.** The prompt and evaluation set are
  English-only. A ticket in another language today either gets
  misclassified or classified correctly by accident (GPT-4.1 is
  multilingual, but nothing in the prompt says how to handle it, and
  nothing in the evaluation set tests it) — this should be an explicit,
  tested capability, not an unverified side effect.
- **RAG over an actual knowledge base.** `suggested_reply` is generated
  from the ticket text alone, with an explicit instruction not to invent
  account/order details. That's the right call today because there's no
  real data to ground it in — but it also caps how useful the reply can
  be. Grounding it in a real KB/macros library would let it reference
  actual policy instead of staying deliberately generic.
