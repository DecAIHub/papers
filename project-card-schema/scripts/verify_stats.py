"""Verify key statistics from the Zenodo JSON export."""

import json, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ZENODO = r"c:\var\www\www-root\data\www\DecAIHub\docs\scientific_articles_final\G_data_paper\zenodo"

with open(ZENODO + r"\project_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

print(f"N = {len(cards)}")
print()

print("=== CATEGORY DISTRIBUTION (multi-label, pipe-split) ===")
cat_counter = Counter()
multi = 0
for c in cards:
    cat = c["passport"].get("Category")
    if cat:
        labels = [x.strip() for x in cat.split("|")]
        labels = [x for x in labels if x]
        if len(labels) > 1:
            multi += 1
        for l in labels:
            cat_counter[l] += 1
    else:
        cat_counter["(missing)"] += 1

print(f"Cards with multi-label Category: {multi}")
for label, cnt in cat_counter.most_common(30):
    pct = cnt / len(cards) * 100
    print(f"  {label}: {cnt} ({pct:.1f}%)")

print()
print("=== TRAILING BACKSLASH CHECK ===")
bad = 0
for c in cards:
    cat = c["passport"].get("Category", "")
    if cat and cat.rstrip().endswith("\\"):
        bad += 1
        if bad <= 5:
            print(f"  {c['project_id']}: {cat!r}")
print(f"Total with trailing backslash: {bad}")

print()
print("=== HIGH-LEVEL GROUPS ===")
groups = Counter()
for c in cards:
    cat = c["passport"].get("Category", "")
    labels = [x.strip() for x in cat.split("|")] if cat else ["(missing)"]
    for l in labels:
        if l.startswith("AI/"):
            groups["AI/*"] += 1
        elif l == "Infra":
            groups["Infra"] += 1
        elif l == "DeFi":
            groups["DeFi"] += 1
        elif l == "Meme":
            groups["Meme"] += 1
        elif l == "Gaming":
            groups["Gaming"] += 1
        elif l == "(missing)":
            groups["(missing)"] += 1
        else:
            groups["Other"] += 1

for g, cnt in groups.most_common():
    print(f"  {g}: {cnt}")

print()
print("=== PASSPORT COMPLETENESS ===")
fields = ["Category", "chain", "type", "token_type", "ai_component", "use_case"]
for f in fields:
    missing = sum(1 for c in cards if not c["passport"].get(f))
    pct = missing / len(cards) * 100
    print(f"  {f}: {len(cards)-missing} present, {missing} missing ({pct:.1f}%)")

print()
print("=== EVIDENCE ===")
ev_total = sum(len(c["evidence"]) for c in cards)
ev_mean = ev_total / len(cards)
print(f"  Total entries: {ev_total}")
print(f"  Mean per card: {ev_mean:.1f}")

tiers = Counter()
for c in cards:
    for e in c["evidence"]:
        tiers[e["tier"]] += 1
for t in sorted(tiers):
    print(f"  {t}: {tiers[t]}")

print()
print("=== CHAIN DISTRIBUTION (top 10) ===")
chain_counter = Counter()
for c in cards:
    ch = c["passport"].get("chain")
    if ch:
        chain_counter[ch] += 1
    else:
        chain_counter["(missing)"] += 1
for label, cnt in chain_counter.most_common(10):
    pct = cnt / len(cards) * 100
    print(f"  {label}: {cnt} ({pct:.1f}%)")
