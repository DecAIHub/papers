"""
Recompute every descriptive statistic and figure reported in the descriptor
from the deposited project_cards.json (v1.1.0).

Usage: python compute_stats.py <project_cards.json> <out_dir>
Writes stats.json (all numbers), CSV tables and PNG figures into <out_dir>.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import matplotlib

matplotlib.use("Agg")
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vocab
import matplotlib.pyplot as plt
import numpy as np

FIELDS = ["Category", "chain", "type", "token_type", "ai_component", "use_case"]
NULLABLE = ["token_type", "ai_component", "use_case"]
TIERS = ["Tier-1", "Tier-2", "Tier-3"]


def labels(rec):
    c = rec["passport"]["Category"]
    return c.split(" | ") if c else []


def tier1_share(rec):
    ev = rec["evidence"]
    return sum(1 for e in ev if e["tier"] == "Tier-1") / len(ev)


def tier1_count(rec):
    return sum(1 for e in rec["evidence"] if e["tier"] == "Tier-1")


def field_coverage(rec):
    """Share of non-null passport fields that have >= 1 Tier-1 evidence entry with that claim_field."""
    nonnull = [f for f in FIELDS if rec["passport"][f] is not None]
    if not nonnull:
        return None
    covered = {e["claim_field"] for e in rec["evidence"] if e["tier"] == "Tier-1"}
    return sum(1 for f in nonnull if f in covered) / len(nonnull)


def passport_incompleteness(rec):
    return sum(1 for f in NULLABLE if rec["passport"][f] is None) / len(NULLABLE)


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    N = len(data)
    S = {"N": N}

    # ---- Category distribution (Table 5) -----------------------------------------
    cat = Counter(l for r in data for l in labels(r))
    S["category_distribution"] = [(l, n, pct(n, N)) for l, n in cat.most_common()]
    S["stub_records"] = sum(1 for r in data if r["stub"])
    mult = Counter(len(labels(r)) for r in data)
    S["label_multiplicity"] = dict(sorted(mult.items()))

    # ---- missingness (Table 8) ----------------------------------------------------
    S["missingness"] = {}
    for f in FIELDS:
        nn = sum(1 for r in data if r["passport"][f] is None)
        if f == "ai_component":
            unk = sum(1 for r in data if r["passport"]["ai_component_status"] == "unknown")
        elif f == "use_case":
            unk = sum(1 for r in data if vocab.use_case_is_unknown(r["passport"]["use_case"]))
        else:
            unk = sum(1 for r in data if r["passport"][f] == "unknown")
        S["missingness"][f] = {"null": nn, "null_pct": pct(nn, N), "unknown": unk, "null_or_unknown_pct": pct(nn + unk, N)}
    S["missingness"]["launch_date"] = {"null": sum(1 for r in data if r["passport"]["launch_date"] is None)}
    S["ai_component_positioning_only"] = sum(1 for r in data if r["passport"]["ai_component_status"] == "positioning_only")
    S["ai_component_none"] = sum(1 for r in data if r["passport"]["ai_component_status"] == "none")
    S["ai_component_identified"] = sum(1 for r in data if r["passport"]["ai_component_status"] == "identified")
    S["distinct_ai_component"] = len({r["passport"]["ai_component"] for r in data if r["passport"]["ai_component"]})
    S["distinct_use_case"] = len({r["passport"]["use_case"] for r in data if r["passport"]["use_case"]})
    for f in ["ai_component_status", "token_type", "chain", "type"]:
        S[f"dist_{f}"] = Counter(r["passport"][f] for r in data if r["passport"][f]).most_common()
    mech = Counter(m for r in data for m in (r["passport"]["token_mechanisms"] or []))
    S["token_mechanisms"] = mech.most_common()

    # ---- evidence (Table 9) --------------------------------------------------------
    ev = [e for r in data for e in r["evidence"]]
    S["evidence_total"] = len(ev)
    S["evidence_by_tier"] = {t: sum(1 for e in ev if e["tier"] == t) for t in TIERS}
    S["evidence_mean_per_card"] = round(len(ev) / N, 2)
    S["unique_tier1_urls"] = len({e["source_url"] for e in ev if e["tier"] == "Tier-1"})
    S["unique_urls"] = len({e["source_url"] for e in ev})
    S["cards_with_tier1"] = sum(1 for r in data if tier1_count(r) > 0)
    S["evidence_with_archive"] = sum(1 for e in ev if e.get("archive_url"))
    S["tier1_with_archive"] = sum(1 for e in ev if e["tier"] == "Tier-1" and e.get("archive_url"))
    from datetime import datetime
    ref = datetime(2026, 3, 5)
    deltas = [abs((datetime.strptime(e["archive_timestamp"][:8], "%Y%m%d") - ref).days) for e in ev if e.get("archive_timestamp")]
    S["archive_within_60d"] = sum(1 for d in deltas if d <= 60)
    S["archive_within_180d"] = sum(1 for d in deltas if d <= 180)
    S["archive_median_delta_days"] = float(np.median(deltas)) if deltas else None
    S["cards_all_tier1_archived"] = sum(1 for r in data if all(e.get("archive_url") for e in r["evidence"] if e["tier"] == "Tier-1"))
    gaps = [g for r in data for g in (r["evidence_gaps"] or [])]
    S["evidence_gaps_total"] = len(gaps)
    S["cards_with_gaps"] = sum(1 for r in data if r["evidence_gaps"])
    S["evidence_count_distribution"] = dict(sorted(Counter(len(r["evidence"]) for r in data).items()))

    # ---- evidence coverage per field ----------------------------------------------
    cov = {}
    for f in FIELDS:
        nonnull = sum(1 for r in data if r["passport"][f] is not None)
        with_ev = sum(1 for r in data if r["passport"][f] is not None and any(e["claim_field"] == f for e in r["evidence"]))
        with_t1 = sum(1 for r in data if r["passport"][f] is not None and any(e["claim_field"] == f and e["tier"] == "Tier-1" for e in r["evidence"]))
        cov[f] = {"non_null": nonnull, "with_evidence": with_ev, "with_tier1_evidence": with_t1,
                  "pct_tier1": pct(with_t1, nonnull), "entries": sum(1 for e in ev if e["claim_field"] == f)}
    S["field_evidence_coverage"] = cov
    fc = [field_coverage(r) for r in data]
    fc = [x for x in fc if x is not None]
    S["field_level_coverage_mean"] = round(float(np.mean(fc)), 3)

    # ---- domain x tier ---------------------------------------------------------------
    dom = defaultdict(Counter)
    for e in ev:
        h = urlparse(e["source_url"]).netloc.lower().removeprefix("www.")
        dom[h][e["tier"]] += 1
    S["domains_total"] = len(dom)
    multi = {h: dict(c) for h, c in dom.items() if len(c) > 1}
    S["domains_in_multiple_tiers"] = len(multi)
    S["domain_tier_crosstab"] = sorted(multi.items(), key=lambda kv: -sum(kv[1].values()))
    S["top_tier1_domains"] = Counter({h: c["Tier-1"] for h, c in dom.items() if c["Tier-1"]}).most_common(15)

    # ---- segments ---------------------------------------------------------------------
    seg_members = defaultdict(list)
    for r in data:
        ls = labels(r) or ["(no category)"]
        for l in ls:
            seg_members[l].append(r)
    seg_rows = []
    for l, recs in seg_members.items():
        n = len(recs)
        shares = [tier1_share(r) for r in recs]
        counts = [tier1_count(r) for r in recs]
        fcs = [x for x in (field_coverage(r) for r in recs) if x is not None]
        row = {"label": l, "N": n,
               "miss_token_type": pct(sum(1 for r in recs if r["passport"]["token_type"] is None), n),
               "miss_ai_component": pct(sum(1 for r in recs if r["passport"]["ai_component"] is None), n),
               "miss_use_case": pct(sum(1 for r in recs if r["passport"]["use_case"] is None), n),
               "mean_tier1_share": round(float(np.mean(shares)), 3),
               "primary_source_gap": round(1 - float(np.mean(shares)), 3),
               "tier1_present_pct": pct(sum(1 for c in counts if c > 0), n),
               "mean_tier1_count": round(float(np.mean(counts)), 1),
               "field_coverage": round(float(np.mean(fcs)), 3) if fcs else None,
               "gap_rows_per_card": round(sum(len(r["evidence_gaps"] or []) for r in recs) / n, 2),
               "tier_shares": [round(float(np.mean([sum(1 for e in r["evidence"] if e["tier"] == t) / len(r["evidence"]) for r in recs])), 3) for t in TIERS]}
        seg_rows.append(row)
    seg_rows.sort(key=lambda x: -x["N"])
    S["segments"] = seg_rows
    top = [row for row in seg_rows if row["label"] != "(no category)"][:9] + [row for row in seg_rows if row["label"] == "(no category)"]
    S["segments_top"] = top
    S["hotspots"] = sorted([row for row in seg_rows if row["N"] >= 10], key=lambda x: -x["primary_source_gap"])

    # ---- relation between the two completeness dimensions (replaces the tie-sensitive top-k table)
    from scipy.stats import spearmanr
    pi = np.array([passport_incompleteness(r) for r in data])
    gp = np.array([1 - tier1_share(r) for r in data])
    rho, pval = spearmanr(pi, gp)
    S["completeness_spearman"] = {"rho": round(float(rho), 3), "p": float(pval)}
    worst_p = pi >= 2 / 3           # >= 2 of 3 nullable fields missing
    worst_e = gp >= 0.25            # Tier-1 share <= 0.75
    S["completeness_2x2"] = {"n_worst_passport": int(worst_p.sum()), "n_worst_evidence": int(worst_e.sum()),
                             "n_both": int((worst_p & worst_e).sum()), "n_neither": int((~worst_p & ~worst_e).sum()),
                             "pct_both_of_worst_passport": pct(int((worst_p & worst_e).sum()), int(worst_p.sum()))}
    # legacy top-k overlap with deterministic tie-break (reported with its tie-break sensitivity)
    S["overlap"] = []
    for k in (50, 100, 200):
        res = []
        for tb in ("id", "id_desc"):
            key_a = (lambda r: (-passport_incompleteness(r), -(1 - tier1_share(r)), r["project_id"])) if tb == "id" else (lambda r: (-passport_incompleteness(r), -(1 - tier1_share(r)), "~" + r["project_id"][::-1]))
            key_b = (lambda r: (-(1 - tier1_share(r)), -passport_incompleteness(r), r["project_id"])) if tb == "id" else (lambda r: (-(1 - tier1_share(r)), -passport_incompleteness(r), "~" + r["project_id"][::-1]))
            a = {r["project_id"] for r in sorted(data, key=key_a)[:k]}
            b = {r["project_id"] for r in sorted(data, key=key_b)[:k]}
            res.append(len(a & b))
        S["overlap"].append({"k": k, "overlap_range": [min(res), max(res)]})

    # ---- launch year (temporal patterns) -----------------------------------------------------
    years = Counter(r["passport"]["launch_date"][:4] for r in data if r["passport"]["launch_date"])
    S["launch_year_distribution"] = sorted(years.items())
    S["launch_date_present"] = sum(years.values())
    gap_by_year = {}
    for y in years:
        recs = [r for r in data if (r["passport"]["launch_date"] or "")[:4] == y]
        if len(recs) >= 10:
            gap_by_year[y] = round(1 - float(np.mean([tier1_share(r) for r in recs])), 3)
    S["primary_source_gap_by_launch_year_N10"] = gap_by_year

    # ---- links ----------------------------------------------------------------------------
    S["links_nonnull"] = {k: sum(1 for r in data if r["links"][k]) for k in data[0]["links"]}

    (out / "stats.json").write_text(json.dumps(S, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---- figures (visual style of the first version of the article) -------------------------------
    seg_labels = [row["label"] for row in top]
    short = [l if l != "(no category)" else "(no cat.)" for l in seg_labels]
    M = np.array([[row["miss_token_type"], row["miss_ai_component"], row["miss_use_case"]] for row in top], dtype=float)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    im = ax.imshow(M, cmap="YlOrRd", vmin=0, vmax=max(90, float(M.max())), aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(["token_type", "ai_component", "use_case"], rotation=30, ha="right", fontsize=12)
    ax.set_yticks(range(len(seg_labels))); ax.set_yticklabels(seg_labels, fontsize=12)
    for r in range(M.shape[0]):
        for c in range(M.shape[1]):
            ax.text(c, r, f"{M[r, c]:.0f}%", ha="center", va="center", fontsize=11)
    cb = fig.colorbar(im, ax=ax); cb.set_label("% missing", fontsize=12)
    ax.set_title("Missingness heatmap", fontsize=14, fontweight="bold")
    fig.tight_layout(); fig.savefig(out / "fig1_missingness_heatmap.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    shares = np.array([row["tier_shares"] for row in top])
    x = np.arange(len(seg_labels))
    bottom = np.zeros(len(seg_labels))
    for k, (t, col) in enumerate(zip(TIERS, ["#2ec4b6", "#f4956a", "#d7a9e3"])):
        ax.bar(x, shares[:, k], bottom=bottom, width=0.6, label=t, color=col)
        bottom += shares[:, k]
    ax.set_xticks(x); ax.set_xticklabels(seg_labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Proportion", fontsize=11); ax.set_ylim(0, 1.05); ax.legend(loc="upper left", fontsize=9)
    ax.set_title("Tier composition by segment", fontsize=12, fontweight="bold")
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    fig.tight_layout(); fig.savefig(out / "fig2_tier_composition.png", dpi=150); plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    pc = [1 - float(np.mean([passport_incompleteness(r) for r in seg_members[l]])) for l in seg_labels]
    ts = [row["mean_tier1_share"] for row in top]
    b1 = ax1.bar(x - 0.2, pc, width=0.4, label="Passport completeness", color="#1f77b4")
    b2 = ax1.bar(x + 0.2, ts, width=0.4, label="Primary-source coverage (Tier-1 share)", color="#ff7f0e")
    for bars in (b1, b2):
        for b in bars:
            ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01, f"{b.get_height():.3f}", ha="center", va="bottom", fontsize=7)
    ax1.axhline(0.5, color="grey", ls="--", lw=0.8); ax1.text(len(x) - 0.35, 0.515, "50%", color="grey", fontsize=8, ha="left")
    ax1.set_xticks(x); ax1.set_xticklabels(short, fontsize=9); ax1.set_xlim(-0.6, len(x) + 0.15)
    ax1.set_ylim(0, 1.2); ax1.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); ax1.set_ylabel("Score (0.0 to 1.0)", fontsize=10)
    ax1.legend(loc="upper right", fontsize=9, ncol=2)
    ax1.set_title("Passport completeness vs. primary-source coverage by category", fontsize=12, fontweight="bold")
    for side in ["top", "right"]:
        ax1.spines[side].set_visible(False)
    fig.tight_layout(); fig.savefig(out / "fig3_completeness_vs_tier1.png", dpi=150); plt.close(fig)

    # ER diagram: header box + attribute list per entity, orthogonal connectors with cardinalities
    fig, ax = plt.subplots(figsize=(13, 7.2)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    FS, LH = 8.8, 3.4

    def text_width(txt, size=FS, weight="normal"):
        t = ax.text(0, 0, txt, fontsize=size, fontweight=weight)
        bb = t.get_window_extent(renderer=renderer).transformed(ax.transData.inverted())
        t.remove()
        return bb.width

    def entity(x, y_top, title, lines):
        w = max(max(text_width(l) for l in lines), text_width(title, 11, "bold")) + 3.0
        h_head, h_body = 4.8, LH * len(lines) + 2.0
        ax.add_patch(plt.Rectangle((x, y_top - h_head), w, h_head, fc="#bfe1f6", ec="black", lw=1.2))
        ax.text(x + w / 2, y_top - h_head / 2, title, ha="center", va="center", fontsize=11, fontweight="bold")
        ax.add_patch(plt.Rectangle((x, y_top - h_head - h_body), w, h_body, fc="white", ec="black", lw=1.2))
        for k, line in enumerate(lines):
            ax.text(x + 1.5, y_top - h_head - 1.0 - LH * (k + 0.5), line, ha="left", va="center", fontsize=FS)
        return {"x": x, "y_top": y_top, "w": w, "y_bottom": y_top - h_head - h_body, "cx": x + w / 2, "right": x + w}

    CARD = ["project_id (string) [PK]", "schema_version (string) [required]", "name, ticker (string, nullable)",
            "token_contract (string, nullable)", "stub (boolean) [required]", "card_verified_date (date) [required]"]
    PAS = ["Category (string, multi-label, nullable)", "chain (string) [required]", "type (string) [required]",
           "token_type (enum, nullable)", "token_mechanisms (enum[], nullable)", "ai_component (string, nullable)",
           "ai_component_status (enum, nullable)", "use_case (string, nullable)", "launch_date (date, nullable)",
           "*_raw (string, nullable): curator's wording"]
    LNK = ["website, documentation, whitepaper,", "repository, releases, roadmap,", "security_advisories, app, bug_bounty,",
           "coingecko, coinmarketcap (URL, nullable)", "explorer, audit, social (URL[], nullable)", "other ({type, url}[], nullable)"]
    EV = ["claim_field (enum) [derived]", "source_url (URL) [required]", "tier (enum: Tier-1/2/3) [required]",
          "verified_date (date) [required]", "archive_url (URL, nullable)", "archive_timestamp (string, nullable)"]
    GAP = ["tier (enum: Tier-1/2/3) [required]", "kind (enum: not_found | note) [required]"]
    widths = {k: max(text_width(l) for l in v) + 3.0 for k, v in [("pas", PAS), ("card", CARD), ("lnk", LNK), ("ev", EV), ("gap", GAP)]}
    gap_x = (99 - widths["pas"] - widths["card"] - widths["lnk"]) / 2
    pas = entity(1, 92, "Passport", PAS)
    card = entity(pas["right"] + gap_x, 98, "Project Card", CARD)
    lnk = entity(card["right"] + gap_x, 92, "Links", LNK)
    y_bus = min(pas["y_bottom"], lnk["y_bottom"]) - 5
    y_child = y_bus - 5
    ev = entity(50 - (widths["ev"] + 8 + widths["gap"]) / 2, y_child, "Evidence", EV)
    gap = entity(ev["right"] + 8, y_child, "Evidence gaps", GAP)

    def seg(x0, y0, x1, y1):
        ax.plot([x0, x1], [y0, y1], color="black", lw=1.2, solid_capstyle="butt")

    y_side = 84
    seg(pas["right"], y_side, card["x"], y_side); seg(card["right"], y_side, lnk["x"], y_side)
    for xx, ha in ((pas["right"] + 0.8, "left"), (card["x"] - 0.8, "right"), (card["right"] + 0.8, "left"), (lnk["x"] - 0.8, "right")):
        ax.text(xx, y_side + 1.0, "1", fontsize=10, ha=ha)
    seg(card["cx"], card["y_bottom"], card["cx"], y_bus)
    seg(ev["cx"], y_bus, gap["cx"], y_bus)
    seg(ev["cx"], y_bus, ev["cx"], ev["y_top"]); seg(gap["cx"], y_bus, gap["cx"], gap["y_top"])
    ax.text(card["cx"] + 1.2, card["y_bottom"] - 2.2, "1", fontsize=10)
    ax.text(ev["cx"] + 1.2, ev["y_top"] + 1.2, "N", fontsize=10); ax.text(gap["cx"] + 1.2, gap["y_top"] + 1.2, "N", fontsize=10)
    fig.savefig(out / "fig4_er_diagram.png", dpi=150, bbox_inches="tight", pad_inches=0.15); plt.close(fig)

    # ---- console summary ---------------------------------------------------------------------
    print(json.dumps({k: S[k] for k in ["N", "stub_records", "label_multiplicity", "missingness", "evidence_total", "evidence_by_tier",
                                        "unique_tier1_urls", "unique_urls", "cards_with_tier1", "evidence_with_archive", "tier1_with_archive", "dist_ai_component_status", "distinct_ai_component", "distinct_use_case",
                                        "evidence_gaps_total", "cards_with_gaps", "field_level_coverage_mean", "domains_total",
                                        "domains_in_multiple_tiers", "overlap", "completeness_spearman", "completeness_2x2", "launch_date_present", "primary_source_gap_by_launch_year_N10",
                                        "ai_component_positioning_only", "ai_component_none"]}, indent=1, default=str))
    print("field coverage:", json.dumps(S["field_evidence_coverage"], indent=1))
    print("segments_top:")
    for row in S["segments_top"]:
        print(" ", row)
    print("category distribution:", S["category_distribution"][:14])


if __name__ == "__main__":
    main()
