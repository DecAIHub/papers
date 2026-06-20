"""Quick tier count from the current Zenodo extract."""

import json, os, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

# Path to the Zenodo dataset (project_cards.json), DOI 10.5281/zenodo.18900950.
# Pass it as argv[1], set the PROJECT_CARDS env var, or place project_cards.json
# in the working directory.
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROJECT_CARDS", "project_cards.json")

with open(DATA, "r", encoding="utf-8") as f:
    cards = json.load(f)

tiers = Counter()
for c in cards:
    for e in c["evidence"]:
        tiers[e["tier"]] += 1

for k in sorted(tiers):
    print(f"{k}: {tiers[k]}")

total = sum(tiers.values())
print(f"Total: {total}")
print()

bt = sum(1 for c in cards for e in c["evidence"] if "`" in e["source_url"])
print(f"\nRemaining backtick URLs: {bt}")

unique_t1 = len(set(e["source_url"] for c in cards for e in c["evidence"] if e["tier"] == "Tier-1"))
print(f"Unique Tier-1 URLs (global): {unique_t1}")
