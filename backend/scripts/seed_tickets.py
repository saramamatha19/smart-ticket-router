"""
Posts 20 curated sample tickets to the running API so the dashboard,
ticket history, and chart are populated before a live mentor demo,
instead of typing tickets in live.

The set below deliberately covers all 5 categories, all 3 priorities,
and the 3 required edge cases (angry tone, very short message,
ambiguous ticket).

Usage:
    1. Start the backend:  uvicorn main:app --reload
    2. In another terminal: python scripts/seed_tickets.py
"""

import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/route-ticket"

# A fixed demo account -- /route-ticket now requires a logged-in customer.
# Registers on first run; every run after that just logs in instead.
SEED_EMAIL = "seed-demo@example.com"
SEED_PASSWORD = "seed-demo-password"

SAMPLE_TICKETS = [
    # --- Billing ---
    "I was charged three times for my subscription this month, please refund immediately!",
    "My invoice shows the wrong amount, can someone check my last payment?",
    "Do you offer any discount if I switch to the annual plan?",

    # --- Technical ---
    "Our production system is down and customers can't check out. This is critical!",
    "The app crashes every time I try to upload a profile picture.",
    "I forgot my password and the reset email never arrived.",

    # --- Network ---
    "Our office WiFi keeps disconnecting every few minutes, the VPN is unusable.",
    "I can't connect to the company VPN from home today.",
    "The firewall seems to be blocking our API calls to your service.",

    # --- Sales ---
    "Can I get a demo of the enterprise plan for my team of 50 people?",
    "What's the pricing difference between the Pro and Business tiers?",
    "We're interested in upgrading, please send a quotation.",

    # --- General ---
    "Just wanted to say the new update looks great, nice work!",
    "Do you have a dark mode planned for the mobile app?",
    "Where can I find your API documentation?",

    # --- Edge case 1: angry tone (must route on real issue, not the emotion) ---
    "THIS IS RIDICULOUS!!! I've emailed THREE TIMES about my account being LOCKED and nobody replies!!! FIX THIS NOW!!!",

    # --- Edge case 2: very short / low-context messages ---
    "Help",
    "Not working",

    # --- Edge case 3: ambiguous ticket ---
    "Something is wrong with my account, please check.",
    "It failed again, not sure why.",
]


def _get_seed_customer_token(client: httpx.Client) -> str:
    credentials = {"email": SEED_EMAIL, "password": SEED_PASSWORD}

    response = client.post(f"{BASE_URL}/login", json=credentials)
    if response.status_code != 200:
        response = client.post(f"{BASE_URL}/register", json=credentials)
        response.raise_for_status()

    return response.json()["access_token"]


def seed():
    with httpx.Client(timeout=30) as client:
        token = _get_seed_customer_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        for i, message in enumerate(SAMPLE_TICKETS, start=1):
            started_at = time.time()
            response = client.post(API_URL, json={"message": message}, headers=headers)
            elapsed = time.time() - started_at

            if response.status_code == 200:
                data = response.json()
                print(
                    f"[{i:02}/20] OK ({elapsed:.1f}s) "
                    f"-> {data['category']} / {data['priority']} / {data['assigned_team']}"
                )
            else:
                print(f"[{i:02}/20] FAILED ({response.status_code}): {message[:50]}")


if __name__ == "__main__":
    seed()
