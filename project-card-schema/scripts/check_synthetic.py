"""Check for synthetic (fallback) Tier-1 evidence entries and report tier distribution."""

import json, os, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

# Path to the Zenodo dataset (project_cards.json), DOI 10.5281/zenodo.18900950.
# Pass it as argv[1], set the PROJECT_CARDS env var, or place project_cards.json
# in the working directory.
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROJECT_CARDS", "project_cards.json")

with open(DATA, "r", encoding="utf-8") as f:
    cards = json.load(f)

synthetic_count = 0
synthetic_pids = []
for c in cards:
    ev = c["evidence"]
    if len(ev) == 1 and ev[0]["claim_field"] == "Category" and ev[0]["tier"] == "Tier-1":
        url = ev[0].get("source_url", "")
        website = c["links"].get("website", "")
        if url == website or url == "https://unknown":
            synthetic_count += 1
            synthetic_pids.append(c["project_id"])

print(f"Cards with synthetic (fallback) Tier-1 evidence: {synthetic_count}")
for pid in synthetic_pids[:30]:
    print(f"  {pid}")
print()

total_all = sum(len(c["evidence"]) for c in cards)
total_no_synth = total_all - synthetic_count

print(f"Total evidence entries (all): {total_all}")
print(f"Total evidence entries (minus synthetic): {total_no_synth}")
print()

tiers_all = Counter()
tiers_real = Counter()
for c in cards:
    ev = c["evidence"]
    is_synth = (
        len(ev) == 1
        and ev[0]["claim_field"] == "Category"
        and ev[0]["tier"] == "Tier-1"
        and (ev[0].get("source_url") == c["links"].get("website") or ev[0].get("source_url") == "https://unknown")
    )
    for e in ev:
        tiers_all[e["tier"]] += 1
        if not is_synth:
            tiers_real[e["tier"]] += 1

print("Tier breakdown (all):")
for t in sorted(tiers_all):
    print(f"  {t}: {tiers_all[t]}")

print("Tier breakdown (minus synthetic):")
for t in sorted(tiers_real):
    print(f"  {t}: {tiers_real[t]}")
print()

# Check for duplicate URLs within same card
dup_count = 0
for c in cards:
    urls = [e["source_url"] for e in c["evidence"]]
    if len(urls) != len(set(urls)):
        dup_count += 1
        dups = [u for u in urls if urls.count(u) > 1]
        if dup_count <= 5:
            print(f"  Duplicate URLs in {c['project_id']}: {set(dups)}")
print(f"\nCards with duplicate evidence URLs: {dup_count}")

# Unique Tier-1 URLs
tier1_urls = set()
for c in cards:
    for e in c["evidence"]:
        if e["tier"] == "Tier-1":
            tier1_urls.add(e["source_url"])
print(f"Unique Tier-1 URLs (all): {len(tier1_urls)}")
