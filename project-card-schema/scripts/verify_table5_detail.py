"""
Detailed verification of Table 5 overlap computation.
Shows tie distributions and sensitivity to tie-breaking.
"""

import json, os, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

# Path to the Zenodo dataset (project_cards.json), DOI 10.5281/zenodo.18900950.
# Pass it as argv[1], set the PROJECT_CARDS env var, or place project_cards.json
# in the working directory.
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROJECT_CARDS", "project_cards.json")

with open(DATA, "r", encoding="utf-8") as f:
    cards = json.load(f)

nullable_fields = ["token_type", "ai_component", "use_case"]

passport_scores = {}
evidence_scores = {}

for c in cards:
    pid = c["project_id"]
    missing = sum(1 for f in nullable_fields if not c["passport"].get(f))
    passport_scores[pid] = missing / len(nullable_fields)

    total = len(c["evidence"])
    t1 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-1")
    share = t1 / total if total > 0 else 0
    evidence_scores[pid] = 1 - share

# ── Passport score distribution ──
p_counter = Counter(passport_scores.values())
print("PASSPORT INCOMPLETENESS DISTRIBUTION:")
for score in sorted(p_counter.keys(), reverse=True):
    print(f"  score={score:.3f}: {p_counter[score]} cards")

# ── Evidence score distribution (binned) ──
print("\nEVIDENCE-GAP PROXY DISTRIBUTION (selected thresholds):")
ev_vals = sorted(evidence_scores.values(), reverse=True)
print(f"  score=0.000 (fully Tier-1): {sum(1 for v in ev_vals if v == 0)}")
print(f"  score>0.000 (some non-Tier-1): {sum(1 for v in ev_vals if v > 0)}")
print(f"  score>0.200: {sum(1 for v in ev_vals if v > 0.200)}")
print(f"  score>0.300: {sum(1 for v in ev_vals if v > 0.300)}")
print(f"  score>0.400: {sum(1 for v in ev_vals if v > 0.400)}")
print(f"  score>0.500: {sum(1 for v in ev_vals if v > 0.500)}")

# ── Show top-50 evidence-gap values ──
print("\nTOP-60 EVIDENCE-GAP PROXY VALUES:")
ev_ranked = sorted(evidence_scores.items(), key=lambda x: -x[1])
for i, (pid, score) in enumerate(ev_ranked[:60]):
    marker = " ← 50th" if i == 49 else ""
    print(f"  {i+1:3d}. {pid:<25s} gap={score:.4f}{marker}")

# ── Tie analysis at boundaries ──
print("\nTIE ANALYSIS:")
for k in [50, 100, 200]:
    kth_val = ev_ranked[k-1][1]
    n_exact_ties = sum(1 for _, v in ev_ranked if abs(v - kth_val) < 1e-9)
    n_above = sum(1 for _, v in ev_ranked if v > kth_val + 1e-9)
    n_at = sum(1 for _, v in ev_ranked if abs(v - kth_val) < 1e-9)
    print(f"  Top-{k}: boundary value={kth_val:.4f}, strictly above={n_above}, at boundary={n_at}")
    print(f"    → if {n_above} < {k} and {n_at} > 1, result is TIE-BREAKING SENSITIVE")

# ── Compute overlaps ──
print("\nOVERLAP COMPUTATION:")
p_ranked = sorted(passport_scores.keys(), key=lambda x: -passport_scores[x])
e_ranked = sorted(evidence_scores.keys(), key=lambda x: -evidence_scores[x])

for k in [50, 100, 200]:
    top_p = set(p_ranked[:k])
    top_e = set(e_ranked[:k])
    overlap = len(top_p & top_e)
    pct = overlap / k * 100
    print(f"  Top-{k}: overlap={overlap}/{k} ({pct:.1f}%)")

# ── What if we rank passport differently for tie-breaking? ──
print("\nSENSITIVITY: passport ranked by score then alphabetical (reverse):")
p_ranked_rev = sorted(passport_scores.keys(), key=lambda x: (-passport_scores[x], x), reverse=False)
p_ranked_rev2 = sorted(passport_scores.keys(), key=lambda x: (-passport_scores[x], x), reverse=False)

# Try reverse tie-breaking for passport
p_ranked_alt = sorted(passport_scores.keys(), key=lambda x: (-passport_scores[x], -hash(x)))
for k in [50, 100, 200]:
    top_p = set(p_ranked_alt[:k])
    top_e = set(e_ranked[:k])
    overlap = len(top_p & top_e)
    pct = overlap / k * 100
    print(f"  Top-{k}: overlap={overlap}/{k} ({pct:.1f}%)")
