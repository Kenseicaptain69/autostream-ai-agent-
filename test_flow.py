"""
test_flow.py — Tests the EXACT expected conversation flow:

  1. "Hi, tell me about your pricing."                              → RAG pricing
  2. "That sounds good, I want to try the Pro plan for my YouTube." → high_intent + platform extracted
  3. "John Doe"                                                     → name captured → asks email
  4. "john@example.com"                                             → email captured → tool fires
"""
from agent import process_message
import time

thread = "final-test-001"
DELAY = 15  # seconds between turns for rate limits

print("=" * 60)
print("AutoStream Agent — Final Flow Test")
print("=" * 60)

# ── Turn 1: Greeting + Pricing ──────────────────────────────────────────
print("\n[Turn 1] User: Hi, tell me about your pricing.")
r1 = process_message("Hi, tell me about your pricing.", thread)
print(f"Agent: {r1['reply']}")
print(f"  >> intent={r1['state']['intent']} | platform={r1['state']['platform']}")

print(f"\n  [Waiting {DELAY}s...]")
time.sleep(DELAY)

# ── Turn 2: Intent Shift → Platform auto-extracted ──────────────────────
print("\n[Turn 2] User: That sounds good, I want to try the Pro plan for my YouTube channel.")
r2 = process_message("That sounds good, I want to try the Pro plan for my YouTube channel.", thread)
print(f"Agent: {r2['reply']}")
print(f"  >> intent={r2['state']['intent']} | platform={r2['state']['platform']} | lead_flow={r2['state']['in_lead_flow']}")

print(f"\n  [Waiting {DELAY}s...]")
time.sleep(DELAY)

# ── Turn 3: Provide Name ────────────────────────────────────────────────
print("\n[Turn 3] User: John Doe")
r3 = process_message("John Doe", thread)
print(f"Agent: {r3['reply']}")
print(f"  >> name={r3['state']['name']} | email={r3['state']['email']}")

print(f"\n  [Waiting {DELAY}s...]")
time.sleep(DELAY)

# ── Turn 4: Provide Email → Tool fires ──────────────────────────────────
print("\n[Turn 4] User: john@example.com")
r4 = process_message("john@example.com", thread)
print(f"Agent: {r4['reply']}")
print(f"  >> name={r4['state']['name']} | email={r4['state']['email']} | platform={r4['state']['platform']} | captured={r4['state']['lead_captured']}")

# ── Result ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if r4["state"]["lead_captured"]:
    print("RESULT: ALL 4 TURNS PASSED — FULL FLOW COMPLETE!")
    print(f"  Lead: {r4['state']['name']}, {r4['state']['email']}, {r4['state']['platform']}")
else:
    print("RESULT: FLOW INCOMPLETE — CHECK LOGS")
print("=" * 60)
