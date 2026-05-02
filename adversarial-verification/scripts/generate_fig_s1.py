"""
Regenerate Figure S1: Tier composition by segment + KDE of evidence-gap proxy.

Requires two CSV files from the registry corpus:
  - passport_fields.csv         (columns: file, category_labels, ...)
  - evidence_project_features.csv (columns: file, tier1_count, tier2_count,
                                   tier3_count, tier1_share, ...)

These CSVs are not redistributed in the public replication package (see Data
Availability in the paper). For peer review or reasonable-request access, drop
both CSV files into ./corpus/ next to this script, or point the env var
DECAIHUB_CORPUS_CACHE to their directory.
"""
import csv
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get(
    "DECAIHUB_CORPUS_CACHE",
    os.path.join(SCRIPT_DIR, "corpus"),
)
OUT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "figures"))
os.makedirs(OUT, exist_ok=True)

SEGMENTS_13 = [
    "Infra", "AI/Other", "AI/Agents", "DeFi", "Meme",
    "AI/Compute", "Consumer", "AI/Data", "Gaming",
    "AI/Inference", "AI/Analytics", "DePIN", "Metaverse",
]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

PAL_TIER1 = "#2C8C99"
PAL_TIER2 = "#E8A838"
PAL_TIER3 = "#D63031"
PAL_HIGHLIGHT = {"AI/Other": "#E8A838", "Meme": "#D63031"}

def load_data():
    passport_path = os.path.join(CACHE, "passport_fields.csv")
    evidence_path = os.path.join(CACHE, "evidence_project_features.csv")
    if not (os.path.exists(passport_path) and os.path.exists(evidence_path)):
        sys.stderr.write(
            "Corpus CSV files not found under:\n"
            f"  {CACHE}\n\n"
            "Expected files:\n"
            f"  - {os.path.basename(passport_path)}\n"
            f"  - {os.path.basename(evidence_path)}\n\n"
            "These files are not redistributed in the public replication package\n"
            "(see Data Availability in the paper). If you have access to them,\n"
            "either drop them into ./corpus/ next to this script, or set\n"
            "DECAIHUB_CORPUS_CACHE to their directory and rerun.\n"
        )
        sys.exit(2)

    passport = {}
    with open(passport_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels = [s.strip() for s in row["category_labels"].split(";") if s.strip()]
            passport[row["file"]] = labels

    evidence = {}
    with open(evidence_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            evidence[row["file"]] = {
                "t1": int(row["tier1_count"]),
                "t2": int(row["tier2_count"]),
                "t3": int(row["tier3_count"]),
                "tier1_share": float(row["tier1_share"]),
            }

    seg_data = {s: {"t1": 0, "t2": 0, "t3": 0, "gaps": [], "N": 0} for s in SEGMENTS_13}
    no_cat = {"t1": 0, "t2": 0, "t3": 0, "gaps": [], "N": 0}

    for fid, labels in passport.items():
        ev = evidence.get(fid, {"t1": 0, "t2": 0, "t3": 0, "tier1_share": 0.0})
        gap = 1 - ev["tier1_share"]
        matched = [s for s in labels if s in SEGMENTS_13]
        if not matched:
            no_cat["t1"] += ev["t1"]
            no_cat["t2"] += ev["t2"]
            no_cat["t3"] += ev["t3"]
            no_cat["gaps"].append(gap)
            no_cat["N"] += 1
        else:
            for s in matched:
                seg_data[s]["t1"] += ev["t1"]
                seg_data[s]["t2"] += ev["t2"]
                seg_data[s]["t3"] += ev["t3"]
                seg_data[s]["gaps"].append(gap)
                seg_data[s]["N"] += 1

    return seg_data, no_cat


def fig_s1():
    seg_data, no_cat = load_data()

    ordered = sorted(SEGMENTS_13, key=lambda s: seg_data[s]["N"], reverse=True)

    labels = [f"{s}\n(N={seg_data[s]['N']})" for s in ordered]
    t1_shares, t2_shares, t3_shares = [], [], []
    for s in ordered:
        total = seg_data[s]["t1"] + seg_data[s]["t2"] + seg_data[s]["t3"]
        if total == 0:
            t1_shares.append(0); t2_shares.append(0); t3_shares.append(0)
        else:
            t1_shares.append(seg_data[s]["t1"] / total)
            t2_shares.append(seg_data[s]["t2"] / total)
            t3_shares.append(seg_data[s]["t3"] / total)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 11),
                                    gridspec_kw={"height_ratios": [1.3, 1]})

    x = np.arange(len(ordered))
    ax1.bar(x, t1_shares, color=PAL_TIER1, label="Tier-1", edgecolor="white", lw=0.5)
    ax1.bar(x, t2_shares, bottom=t1_shares, color=PAL_TIER2, label="Tier-2", edgecolor="white", lw=0.5)
    bottoms2 = [a + b for a, b in zip(t1_shares, t2_shares)]
    ax1.bar(x, t3_shares, bottom=bottoms2, color=PAL_TIER3, label="Tier-3", edgecolor="white", lw=0.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Share of artifacts")
    ax1.set_title("Tier composition by segment", fontsize=14, fontweight="bold")
    ax1.set_ylim(0, 1.05)
    ax1.legend(loc="lower left", fontsize=10)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    grid = np.linspace(0, 1.0, 300)
    all_segs = list(seg_data.keys())
    for s in all_segs:
        gaps = np.array(seg_data[s]["gaps"])
        if len(gaps) < 5:
            continue
        try:
            kde = gaussian_kde(gaps, bw_method=0.25)
        except Exception:
            continue
        density = kde(grid)
        if s in PAL_HIGHLIGHT:
            ax2.plot(grid, density, color=PAL_HIGHLIGHT[s], lw=2.0, alpha=0.9, label=s)
        else:
            ax2.plot(grid, density, color="#B0B0B0", lw=0.8, alpha=0.4)

    ax2.set_xlabel("Evidence-gap proxy (1 - Tier-1 share)")
    ax2.set_ylabel("Density")
    ax2.set_title("KDE of evidence-gap proxy", fontsize=14, fontweight="bold")
    ax2.legend(title="Highlighted segments", fontsize=10, title_fontsize=10)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_s1_tier_composition.png"))
    plt.close(fig)
    print("  OK fig_s1_tier_composition.png")


if __name__ == "__main__":
    fig_s1()
