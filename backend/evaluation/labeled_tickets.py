"""
20 manually labeled sample tickets used to evaluate the classifier in
evaluation.md. The same 20 messages used in scripts/seed_tickets.py.

Expected labels were assigned BEFORE running the evaluation, by hand,
using only the rules already documented in app/prompts/ticket_prompt.py
(category keyword lists, priority rules, team mapping) — not by looking
at what the model predicts. Some tickets are genuinely ambiguous by
design (the 3 required edge cases); that ambiguity is noted inline.
"""

LABELED_TICKETS = [
    {
        "message": "I was charged three times for my subscription this month, please refund immediately!",
        "expected_category": "Billing",
        "expected_priority": "High",
        "expected_team": "Finance",
        "note": "Matches the prompt's own HIGH-priority example verbatim.",
    },
    {
        "message": "My invoice shows the wrong amount, can someone check my last payment?",
        "expected_category": "Billing",
        "expected_priority": "Medium",
        "expected_team": "Finance",
        "note": "Billing question, no urgency/fraud language -> refund-without-urgency bucket.",
    },
    {
        "message": "Do you offer any discount if I switch to the annual plan?",
        "expected_category": "Sales",
        "expected_priority": "Low",
        "expected_team": "Sales",
        "note": "Commercial/pricing inquiry, not an existing billing problem.",
    },
    {
        "message": "Our production system is down and customers can't check out. This is critical!",
        "expected_category": "Technical",
        "expected_priority": "High",
        "expected_team": "Engineering",
        "note": "Production outage + explicit 'critical' keyword.",
    },
    {
        "message": "The app crashes every time I try to upload a profile picture.",
        "expected_category": "Technical",
        "expected_priority": "Medium",
        "expected_team": "Engineering",
        "note": "Single-user bug report, no business-critical language.",
    },
    {
        "message": "I forgot my password and the reset email never arrived.",
        "expected_category": "Technical",
        "expected_priority": "Medium",
        "expected_team": "Engineering",
        "note": "Matches the prompt's own MEDIUM-priority example verbatim.",
    },
    {
        "message": "Our office WiFi keeps disconnecting every few minutes, the VPN is unusable.",
        "expected_category": "Network",
        "expected_priority": "High",
        "expected_team": "Network Operations",
        "note": "Office-wide (multi-user) + VPN 'unusable' reads as business-critical.",
    },
    {
        "message": "I can't connect to the company VPN from home today.",
        "expected_category": "Network",
        "expected_priority": "Medium",
        "expected_team": "Network Operations",
        "note": "Single user, workaround plausible (office network).",
    },
    {
        "message": "The firewall seems to be blocking our API calls to your service.",
        "expected_category": "Network",
        "expected_priority": "Medium",
        "expected_team": "Network Operations",
        "note": "Specific integration issue, no explicit outage/critical wording.",
    },
    {
        "message": "Can I get a demo of the enterprise plan for my team of 50 people?",
        "expected_category": "Sales",
        "expected_priority": "Low",
        "expected_team": "Sales",
        "note": "Matches the prompt's own Sales/Low examples verbatim.",
    },
    {
        "message": "What's the pricing difference between the Pro and Business tiers?",
        "expected_category": "Sales",
        "expected_priority": "Low",
        "expected_team": "Sales",
        "note": "Pricing question -> exact Low-priority example.",
    },
    {
        "message": "We're interested in upgrading, please send a quotation.",
        "expected_category": "Sales",
        "expected_priority": "Low",
        "expected_team": "Sales",
        "note": "Quotation/upgrade -> exact Sales examples.",
    },
    {
        "message": "Just wanted to say the new update looks great, nice work!",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "Appreciation -> exact General/Low example.",
    },
    {
        "message": "Do you have a dark mode planned for the mobile app?",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "This exact sentence is the prompt's own Low-priority example.",
    },
    {
        "message": "Where can I find your API documentation?",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "Documentation/info request, not an API malfunction -> General, not Technical.",
    },
    {
        "message": (
            "THIS IS RIDICULOUS!!! I've emailed THREE TIMES about my account being "
            "LOCKED and nobody replies!!! FIX THIS NOW!!!"
        ),
        "expected_category": "Technical",
        "expected_priority": "High",
        "expected_team": "Engineering",
        "note": "EDGE CASE 1 (angry tone): account locked is High on its own merits, "
        "independent of the angry tone -- tests that anger isn't the only signal used.",
    },
    {
        "message": "Help",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "EDGE CASE 2 (very short message) -- this exact word is the prompt's own example.",
    },
    {
        "message": "Not working",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "EDGE CASE 2 (very short message) -- this exact phrase is the prompt's own example.",
    },
    {
        "message": "Something is wrong with my account, please check.",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "EDGE CASE 3 (ambiguous) -- genuinely underspecified; 'Technical' would "
        "also be a defensible read. Flagged, not treated as unambiguous ground truth.",
    },
    {
        "message": "It failed again, not sure why.",
        "expected_category": "General",
        "expected_priority": "Low",
        "expected_team": "Support",
        "note": "EDGE CASE 3 (ambiguous) -- same caveat as above.",
    },
]
