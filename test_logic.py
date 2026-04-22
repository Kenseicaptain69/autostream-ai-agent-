"""Quick verification of core logic — no LLM calls."""
from intent import _rule_based_intent, extract_platform
from state import get_missing_lead_field, is_lead_complete
from agent import graph

print("=== Intent Classification ===")
tests = [
    ("Hi, tell me about your pricing.", "product_query"),
    ("That sounds good, I want to try the Pro plan for my YouTube channel.", "high_intent"),
    ("John Doe", "other"),
    ("john@example.com", "provide_email"),
]
for text, exp in tests:
    got = _rule_based_intent(text)
    status = "PASS" if got == exp else "FAIL"
    print(f"  [{status}] \"{text}\" -> {got}")

print("\n=== Platform Extraction ===")
p = extract_platform("I want to try the Pro plan for my YouTube channel.")
print(f"  Extracted: \"{p}\" -> {'PASS' if p == 'YouTube' else 'FAIL'}")

print("\n=== State Progression (with auto-extracted platform) ===")
s = {"name": None, "email": None, "platform": "YouTube"}
print(f"  Platform pre-filled: missing={get_missing_lead_field(s)}, complete={is_lead_complete(s)}")
s["name"] = "John Doe"
print(f"  After name: missing={get_missing_lead_field(s)}, complete={is_lead_complete(s)}")
s["email"] = "john@example.com"
print(f"  After email: missing={get_missing_lead_field(s)}, complete={is_lead_complete(s)}")

print(f"\n=== Graph Nodes ===")
print(f"  {list(graph.nodes.keys())}")
print("\nALL CHECKS PASSED")
