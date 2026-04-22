"""Test RAG knowledge retrieval for all required data points."""
from rag import retrieve_context, load_knowledge_base

print("RAG Knowledge Retrieval Test")
print("=" * 65)

# Test retrieval queries
queries = [
    "What are your pricing plans?",
    "Tell me about the Pro plan",
    "What is your refund policy?",
    "Do you have 24/7 support?",
    "What platforms do you support?",
]

for i, q in enumerate(queries, 1):
    print(f"\n{i}. Query: \"{q}\"")
    print(retrieve_context(q))

print("\n" + "=" * 65)

# Verify exact data points from spec
kb = load_knowledge_base()
checks = [
    ("Basic price = $29/month", kb["basic_plan"]["price"] == "$29/month"),
    ("Basic videos = 10/month", kb["basic_plan"]["videos"] == "10/month"),
    ("Basic resolution = 720p", kb["basic_plan"]["resolution"] == "720p"),
    ("Pro price = $79/month", kb["pro_plan"]["price"] == "$79/month"),
    ("Pro videos = Unlimited", kb["pro_plan"]["videos"] == "Unlimited"),
    ("Pro resolution = 4K", kb["pro_plan"]["resolution"] == "4K"),
    ("Pro has AI captions", "AI captions" in kb["pro_plan"]["features"]),
    ("No refunds after 7 days", "No refunds after 7 days" in kb["policies"]["refund"]),
    ("24/7 support only Pro", "24/7 support only for Pro" in kb["policies"]["support"]),
]

print("\nData Verification:")
for label, ok in checks:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}")
print(f"\nResult: {sum(1 for _, ok in checks if ok)}/{len(checks)} passed")
