"""
Recompute all evidence-dependent statistics and regenerate Figures 3 & 4
from the current Zenodo extract (project_cards.json).
"""

import json, os, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: matplotlib/numpy not installed. Run: pip install matplotlib numpy")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZENODO = os.path.join(BASE, "zenodo")
ASSETS = os.path.join(BASE, "assets")

with open(os.path.join(ZENODO, "project_cards.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)

SEGMENTS_MAIN = ["Infra", "AI/Other", "AI/Agents", "DeFi", "Meme",
                 "AI/Compute", "Consumer", "AI/Data", "Gaming", "(no category)"]

nullable_fields = ["token_type", "ai_component", "use_case"]

# ── Compute per-segment statistics ──

segment_data = defaultdict(list)
all_segments = defaultdict(list)

for c in cards:
    cat = c["passport"].get("Category") or ""
    labels = [x.strip() for x in cat.split("|")] if cat else ["(no category)"]
    labels = [x for x in labels if x] or ["(no category)"]

    total = len(c["evidence"])
    t1 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-1")
    t2 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-2")
    t3 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-3")
    share_t1 = t1 / total if total > 0 else 0
    share_t2 = t2 / total if total > 0 else 0
    share_t3 = t3 / total if total > 0 else 0

    missing = sum(1 for f in nullable_fields if not c["passport"].get(f))
    passport_comp = 1 - missing / len(nullable_fields)

    entry = {
        "pid": c["project_id"],
        "total": total, "t1": t1, "t2": t2, "t3": t3,
        "share_t1": share_t1, "share_t2": share_t2, "share_t3": share_t3,
        "passport_comp": passport_comp, "missing": missing,
    }

    for label in labels:
        segment_data[label].append(entry)
        all_segments[label].append(entry)

# ── TABLE 7 output ──
print("=" * 80)
print("TABLE 7 — UPDATED VALUES")
print("=" * 80)
print(f"{'Label':<15} {'N':>4} {'MeanT1share':>12} {'EGP':>8} {'T1pres%':>8} {'MeanT1cnt':>10}")
for seg in SEGMENTS_MAIN:
    data = segment_data.get(seg, [])
    n = len(data)
    if n == 0:
        continue
    ms = sum(d["share_t1"] for d in data) / n
    gap = 1 - ms
    present = sum(1 for d in data if d["t1"] > 0) / n * 100
    mc = sum(d["t1"] for d in data) / n
    print(f"{seg:<15} {n:>4} {ms:>12.3f} {gap:>8.3f} {present:>8.1f} {mc:>10.1f}")

# ── TABLE 8 — all segments with N >= 10 ──
print()
print("=" * 80)
print("TABLE 8 — EVIDENCE-GAP HOTSPOTS (N >= 10)")
print("=" * 80)

all_seg_stats = []
for seg, data in all_segments.items():
    if len(data) < 10:
        continue
    n = len(data)
    ms = sum(d["share_t1"] for d in data) / n
    gap = 1 - ms

    pids_in_seg = set(d["pid"] for d in data)
    cards_in_seg = [c for c in cards if c["project_id"] in pids_in_seg]
    miss_tt = sum(1 for c in cards_in_seg if not c["passport"].get("token_type")) / len(cards_in_seg) * 100
    miss_ai = sum(1 for c in cards_in_seg if not c["passport"].get("ai_component")) / len(cards_in_seg) * 100
    miss_uc = sum(1 for c in cards_in_seg if not c["passport"].get("use_case")) / len(cards_in_seg) * 100

    all_seg_stats.append((seg, n, gap, miss_tt, miss_ai, miss_uc))

all_seg_stats.sort(key=lambda x: -x[2])
print(f"{'Label':<15} {'N':>4} {'EGP':>8} {'tt%':>8} {'ai%':>8} {'uc%':>8}")
for seg, n, gap, tt, ai, uc in all_seg_stats:
    print(f"{seg:<15} {n:>4} {gap:>8.3f} {tt:>8.1f} {ai:>8.1f} {uc:>8.1f}")

# ── TABLE 5 — Overlap ──
print()
print("=" * 80)
print("TABLE 5 — OVERLAP")
print("=" * 80)

passport_incomp = {}
evidence_incomp = {}
for c in cards:
    pid = c["project_id"]
    missing = sum(1 for f in nullable_fields if not c["passport"].get(f))
    passport_incomp[pid] = missing / len(nullable_fields)
    total = len(c["evidence"])
    t1 = sum(1 for e in c["evidence"] if e["tier"] == "Tier-1")
    evidence_incomp[pid] = 1 - (t1 / total if total > 0 else 0)

p_ranked = sorted(passport_incomp.keys(), key=lambda x: -passport_incomp[x])
e_ranked = sorted(evidence_incomp.keys(), key=lambda x: -evidence_incomp[x])

for k in [50, 100, 200]:
    top_p = set(p_ranked[:k])
    top_e = set(e_ranked[:k])
    overlap = len(top_p & top_e)
    pct = overlap / k * 100
    print(f"  Top-{k}: {overlap}/{k} ({pct:.1f}%)")

both_100 = set(p_ranked[:100]) & set(e_ranked[:100])
n_both = len(both_100)
mean_gap_both = sum(evidence_incomp[pid] for pid in both_100) / n_both if n_both else 0
cats_of_both = defaultdict(int)
for pid in both_100:
    c = next(c for c in cards if c["project_id"] == pid)
    cat = c["passport"].get("Category") or "(no category)"
    for lbl in ([x.strip() for x in cat.split("|")] if cat != "(no category)" else ["(no category)"]):
        cats_of_both[lbl] += 1
print(f"\n  Cards in both top-100: n={n_both}")
print(f"  Mean evidence-gap proxy: {mean_gap_both:.3f}")
print(f"  Category breakdown:")
for lbl, cnt in sorted(cats_of_both.items(), key=lambda x: -x[1]):
    print(f"    {lbl}: {cnt}/{n_both}")

all_missing_tt = all(not next(c for c in cards if c["project_id"] == pid)["passport"].get("token_type") for pid in both_100)
all_missing_ai = all(not next(c for c in cards if c["project_id"] == pid)["passport"].get("ai_component") for pid in both_100)
print(f"  All have missing token_type: {all_missing_tt}")
print(f"  All have missing ai_component: {all_missing_ai}")

# ── Corpus-level average evidence-gap proxy ──
all_gaps = [evidence_incomp[pid] for pid in evidence_incomp]
corpus_avg_gap = sum(all_gaps) / len(all_gaps)
print(f"\n  Corpus average evidence-gap proxy: {corpus_avg_gap:.3f}")
print(f"  Ratio (both_100 / corpus): {mean_gap_both / corpus_avg_gap:.1f}x")

# ── INLINE PROSE values ──
print()
print("=" * 80)
print("INLINE PROSE VALUES")
print("=" * 80)
for seg in ["Meme", "(no category)", "AI/Compute", "AI/Data"]:
    data = segment_data[seg]
    n = len(data)
    ms = sum(d["share_t1"] for d in data) / n
    mc = sum(d["t1"] for d in data) / n
    print(f"  {seg}: share={ms:.3f}, count={mc:.1f}")

# Min share among AI/Compute and AI/Data
ac_share = sum(d["share_t1"] for d in segment_data["AI/Compute"]) / len(segment_data["AI/Compute"])
ad_share = sum(d["share_t1"] for d in segment_data["AI/Data"]) / len(segment_data["AI/Data"])
ac_count = sum(d["t1"] for d in segment_data["AI/Compute"]) / len(segment_data["AI/Compute"])
ad_count = sum(d["t1"] for d in segment_data["AI/Data"]) / len(segment_data["AI/Data"])
print(f"\n  AI/Compute + AI/Data: min share={min(ac_share, ad_share):.3f}, min count={min(ac_count, ad_count):.1f}")

# Infra and AI/Compute gap
infra_gap = 1 - sum(d["share_t1"] for d in segment_data["Infra"]) / len(segment_data["Infra"])
ac_gap = 1 - ac_share
print(f"  Infra gap={infra_gap:.3f}, AI/Compute gap={ac_gap:.3f}")
print(f"  Max of (Infra, AI/Compute) gap: {max(infra_gap, ac_gap):.3f}")

# ── FIGURE 3 — Stacked bar: Tier composition ──

fig3_labels = SEGMENTS_MAIN
fig3_t1 = []
fig3_t2 = []
fig3_t3 = []

for seg in fig3_labels:
    data = segment_data.get(seg, [])
    n = len(data)
    if n == 0:
        fig3_t1.append(0); fig3_t2.append(0); fig3_t3.append(0)
        continue
    fig3_t1.append(sum(d["share_t1"] for d in data) / n)
    fig3_t2.append(sum(d["share_t2"] for d in data) / n)
    fig3_t3.append(sum(d["share_t3"] for d in data) / n)

x = np.arange(len(fig3_labels))
width = 0.6

fig, ax = plt.subplots(figsize=(12, 5))
bars1 = ax.bar(x, fig3_t1, width, label="Tier-1", color="#2ec4b6")
bars2 = ax.bar(x, fig3_t2, width, bottom=fig3_t1, label="Tier-2", color="#e88d67")
bars3 = ax.bar(x, fig3_t3, width,
               bottom=[a + b for a, b in zip(fig3_t1, fig3_t2)],
               label="Tier-3", color="#dda0dd")

ax.set_ylabel("Proportion", fontsize=12)
ax.set_title("Figure 3. Tier composition by segment", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(fig3_labels, rotation=30, ha="right", fontsize=10)
ax.set_ylim(0, 1.05)
ax.legend(loc="upper left", fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
fig3_path = os.path.join(ASSETS, "fig3_tier_composition.png")
plt.savefig(fig3_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"\nSaved: {fig3_path}")

# ── FIGURE 4 — Grouped bar: Passport vs Evidence completeness ──

fig4_labels = SEGMENTS_MAIN
fig4_display = [s if s != "(no category)" else "(no cat.)" for s in fig4_labels]
fig4_passport = []
fig4_evidence = []

for seg in fig4_labels:
    data = segment_data.get(seg, [])
    n = len(data)
    if n == 0:
        fig4_passport.append(0); fig4_evidence.append(0)
        continue
    fig4_passport.append(sum(d["passport_comp"] for d in data) / n)
    fig4_evidence.append(sum(d["share_t1"] for d in data) / n)

x = np.arange(len(fig4_labels))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 6))
bars_p = ax.bar(x - width/2, fig4_passport, width, label="Passport completeness", color="#1f77b4")
bars_e = ax.bar(x + width/2, fig4_evidence, width, label="Evidence completeness (Tier-1 share)", color="#ff7f0e")

for bar in bars_p:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.01, f"{h:.3f}",
            ha="center", va="bottom", fontsize=8)
for bar in bars_e:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.01, f"{h:.3f}",
            ha="center", va="bottom", fontsize=8)

ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.7, linewidth=1)
ax.text(len(fig4_labels) - 0.3, 0.51, "50%", color="gray", fontsize=9, ha="left")

ax.set_ylabel("Score (0.0 to 1.0)", fontsize=12)
ax.set_title("Passport Completeness vs. Evidence Completeness by Category",
             fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(fig4_display, rotation=0, ha="center", fontsize=10)
ax.set_ylim(0, 1.05)
ax.legend(loc="upper right", fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
fig4_path = os.path.join(ASSETS, "fig4_completeness_by_segment.png")
plt.savefig(fig4_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"Saved: {fig4_path}")
