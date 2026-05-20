"""
Recompute Tables 5, 7 from current Zenodo extract and compare with article values.
"""

import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ZENODO = r"c:\var\www\www-root\data\www\DecAIHub\docs\scientific_articles_final\G_data_paper\zenodo"

with open(ZENODO + r"\project_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# ── Table 7: Per-segment Tier-1 proxies ──

segment_cards = defaultdict(list)
for c in cards:
    cat = c["passport"].get("Category") or ""
    labels = [x.strip() for x in cat.split("|")] if cat else ["(no category)"]
    labels = [x for x in labels if x] or ["(no category)"]
    for label in labels:
        total = len(c["evidence"])
        t1 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-1")
        share = t1 / total if total > 0 else 0
        segment_cards[label].append({"total": total, "t1": t1, "share": share})

# Article Table 7 values for comparison
article_t7 = {
    "Infra":          {"N": 384, "share": 0.870, "gap": 0.130, "present": 100.0, "count": 5.2},
    "AI/Other":       {"N": 247, "share": 0.802, "gap": 0.198, "present": 100.0, "count": 4.0},
    "AI/Agents":      {"N": 221, "share": 0.834, "gap": 0.166, "present": 100.0, "count": 4.6},
    "DeFi":           {"N": 112, "share": 0.863, "gap": 0.137, "present": 100.0, "count": 4.9},
    "Meme":           {"N": 104, "share": 0.693, "gap": 0.307, "present": 100.0, "count": 2.3},
    "AI/Compute":     {"N":  55, "share": 0.864, "gap": 0.136, "present": 100.0, "count": 5.6},
    "Consumer":       {"N":  52, "share": 0.861, "gap": 0.139, "present": 100.0, "count": 4.4},
    "AI/Data":        {"N":  44, "share": 0.873, "gap": 0.127, "present": 100.0, "count": 5.2},
    "Gaming":         {"N":  35, "share": 0.845, "gap": 0.155, "present": 100.0, "count": 5.0},
    "(no category)":  {"N":  27, "share": 0.689, "gap": 0.311, "present": 100.0, "count": 2.0},
}

print("=" * 90)
print("TABLE 7 VERIFICATION")
print("=" * 90)
print(f"{'Segment':<15} {'N':>4} {'Art.N':>5} | {'Share':>6} {'Art.':>6} {'Δ':>7} | {'Gap':>6} {'Art.':>6} | {'Count':>6} {'Art.':>6} {'Δ':>7}")
print("-" * 90)

all_ok = True
for seg in ["Infra", "AI/Other", "AI/Agents", "DeFi", "Meme", "AI/Compute",
            "Consumer", "AI/Data", "Gaming", "(no category)"]:
    data = segment_cards.get(seg, [])
    n = len(data)
    if n == 0:
        continue
    mean_share = sum(d["share"] for d in data) / n
    mean_gap = 1 - mean_share
    present_pct = sum(1 for d in data if d["t1"] > 0) / n * 100
    mean_count = sum(d["t1"] for d in data) / n

    art = article_t7.get(seg, {})
    art_n = art.get("N", "?")
    art_share = art.get("share", 0)
    art_gap = art.get("gap", 0)
    art_count = art.get("count", 0)

    d_share = mean_share - art_share
    d_count = mean_count - art_count

    flag_s = " !" if abs(d_share) >= 0.005 else ""
    flag_c = " !" if abs(d_count) >= 0.05 else ""

    print(f"{seg:<15} {n:>4} {art_n:>5} | {mean_share:>6.3f} {art_share:>6.3f} {d_share:>+7.3f}{flag_s} | {mean_gap:>6.3f} {art_gap:>6.3f} | {mean_count:>6.1f} {art_count:>6.1f} {d_count:>+7.1f}{flag_c}")

    if abs(d_share) >= 0.005 or abs(d_count) >= 0.05:
        all_ok = False

print()
if all_ok:
    print(">>> ALL TABLE 7 VALUES MATCH (within rounding)")
else:
    print(">>> SOME TABLE 7 VALUES DIFFER — see ! marks")

# ── Table 5: Overlap analysis ──
print()
print("=" * 90)
print("TABLE 5 VERIFICATION (Overlap of completeness dimensions)")
print("=" * 90)

nullable_fields = ["token_type", "ai_component", "use_case"]

passport_incomp = {}
evidence_incomp = {}

for c in cards:
    pid = c["project_id"]
    missing = sum(1 for f in nullable_fields if not c["passport"].get(f))
    passport_incomp[pid] = missing / len(nullable_fields)

    total = len(c["evidence"])
    t1 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-1")
    share = t1 / total if total > 0 else 0
    evidence_incomp[pid] = 1 - share

passport_ranked = sorted(passport_incomp.keys(), key=lambda x: -passport_incomp[x])
evidence_ranked = sorted(evidence_incomp.keys(), key=lambda x: -evidence_incomp[x])

article_t5 = {50: (5, 10.0), 100: (23, 23.0), 200: (63, 31.5)}

for k in [50, 100, 200]:
    top_p = set(passport_ranked[:k])
    top_e = set(evidence_ranked[:k])
    overlap = len(top_p & top_e)
    pct = overlap / k * 100

    art_n, art_pct = article_t5[k]
    flag = " !" if overlap != art_n else ""
    print(f"  Top-{k}: overlap = {overlap}/{k} ({pct:.1f}%) | Article: {art_n}/{k} ({art_pct:.1f}%){flag}")

# ── Inline prose values ──
print()
print("=" * 90)
print("INLINE PROSE VERIFICATION")
print("=" * 90)

# Meme and no-category Tier-1 share/count
for seg in ["Meme", "(no category)"]:
    data = segment_cards.get(seg, [])
    n = len(data)
    mean_share = sum(d["share"] for d in data) / n
    mean_count = sum(d["t1"] for d in data) / n
    print(f"  {seg}: mean Tier-1 share = {mean_share:.3f}, mean count = {mean_count:.1f}")

# AI/Compute and AI/Data
for seg in ["AI/Compute", "AI/Data"]:
    data = segment_cards.get(seg, [])
    n = len(data)
    mean_share = sum(d["share"] for d in data) / n
    mean_count = sum(d["t1"] for d in data) / n
    print(f"  {seg}: mean Tier-1 share = {mean_share:.3f}, mean count = {mean_count:.1f}")

# 23 cards in both top-100 — mean evidence-gap
top_p_100 = set(passport_ranked[:100])
top_e_100 = set(evidence_ranked[:100])
both = top_p_100 & top_e_100
if both:
    mean_gap_both = sum(evidence_incomp[pid] for pid in both) / len(both)
    print(f"  Cards in both top-100: n={len(both)}, mean evidence-gap = {mean_gap_both:.3f} (article: 0.439)")

# Temporal: cards with launch_date (we don't have this in extract, skip)
print(f"  Temporal patterns: CANNOT VERIFY (launch_date not in Zenodo schema)")

# Corpus-level mean evidence per card
total_ev = sum(len(c["evidence"]) for c in cards)
mean_ev = total_ev / len(cards)
print(f"  Corpus mean evidence per card: {mean_ev:.1f} (README: 5.2)")
