"""
Runs a batch of tickets through route_ticket_with_diagnostics() (real
GPT-4.1 calls) and prints a one-line batch summary — parse success
rate, average latency, average total tokens — plus a per-ticket log
line for each one as it runs.

Reuses the same 20 messages already hand-labeled in
evaluation/labeled_tickets.py, so this doesn't introduce a second,
possibly-drifting sample set. This script is about throughput/cost/
reliability telemetry (parsed? how long? how many tokens?) — accuracy
against expected labels is what evaluation/run_evaluation.py measures.

Usage (from backend/, with the venv active and .env present):
    python scripts/batch_summary.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.router_service import route_ticket_with_diagnostics  # noqa: E402
from evaluation.labeled_tickets import LABELED_TICKETS  # noqa: E402


def run():
    messages = [t["message"] for t in LABELED_TICKETS]
    total = len(messages)

    parsed = 0
    latencies = []
    total_tokens = []
    review_flagged = 0

    for i, message in enumerate(messages, start=1):
        outcome = route_ticket_with_diagnostics(message)

        if outcome["success"]:
            parsed += 1
            # A message can split into multiple sub-tickets; summarize
            # each one on its own segment of the status line.
            segments = []
            for ticket in outcome["tickets"]:
                segment = f"{ticket.category}/{ticket.priority} (confidence={ticket.confidence})"
                if ticket.needs_human_review:
                    review_flagged += 1
                    segment += " [NEEDS HUMAN REVIEW]"
                segments.append(segment)
            status = "OK -> " + " | ".join(segments)
        else:
            status = f"FAILED -> {outcome['error']['type']}: {outcome['error']['message']}"

        if outcome["latency_ms"] is not None:
            latencies.append(outcome["latency_ms"])
        if outcome["total_tokens"] is not None:
            total_tokens.append(outcome["total_tokens"])

        latency_note = f"{outcome['latency_ms'] / 1000:.2f}s" if outcome["latency_ms"] else "n/a"
        print(f"[{i:02}/{total}] ({latency_note}) {message[:50]!r}: {status}")

    avg_latency_s = (sum(latencies) / len(latencies) / 1000) if latencies else 0.0
    avg_tokens = (sum(total_tokens) / len(total_tokens)) if total_tokens else 0

    print()
    print(
        f"{parsed}/{total} parsed, avg latency {avg_latency_s:.1f}s, "
        f"avg tokens {avg_tokens:.0f}, {review_flagged} flagged for human review"
    )


if __name__ == "__main__":
    run()
