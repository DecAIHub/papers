"""
Inter-coder reliability of the claim-intensity pilot (February 2026).

Compares the independent coder's sheet with the curator's reference coding for 50 cards: the tier of every cited
artifact (positional, artifact_1..artifact_8) and the 13 binary flags AI_0..AI_4, OC_1..OC_3, TK_0..TK_4.

Usage (from this folder): python compute_irr.py [coding_sheet.csv] [ground_truth.csv]
Writes irr_report.md next to the script and prints the headline figures.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

try:
    from scipy.stats import spearmanr
except ImportError:
    spearmanr = None

HERE = Path(__file__).parent
FLAGS = ["AI_0", "AI_1", "AI_2", "AI_3", "AI_4", "OC_1", "OC_2", "OC_3", "TK_0", "TK_1", "TK_2", "TK_3", "TK_4"]


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return {r["project_id"].strip(): r for r in csv.DictReader(fh) if r.get("project_id", "").strip()}


def kappa(pairs):
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    cats = {v for p in pairs for v in p}
    pe = sum((sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def alpha(pairs):
    vals = [v for p in pairs for v in p]
    n = len(vals)
    c = Counter(vals)
    Do = sum(1 for a, b in pairs if a != b) / len(pairs)
    De = 1 - sum(k * (k - 1) for k in c.values()) / (n * (n - 1))
    return 1.0 if De == 0 else 1 - Do / De


def agreement(pairs):
    return sum(1 for a, b in pairs if a == b) / len(pairs)


def main():
    cs = load(sys.argv[1] if len(sys.argv) > 1 else HERE / "coding_sheet.csv")
    gt = load(sys.argv[2] if len(sys.argv) > 2 else HERE / "ground_truth.csv")
    ids = [pid for pid in gt if pid in cs]

    # ---- tiers (positional) ----------------------------------------------------------------------------------
    tier_pairs = []
    for pid in ids:
        for i in range(1, 9):
            g, c = gt[pid].get(f"artifact_{i}_tier", "").strip(), cs[pid].get(f"artifact_{i}_tier", "").strip()
            if g and c:
                tier_pairs.append((g, c))
    tier_dir = Counter(f"Tier-{a} -> Tier-{b}" for a, b in tier_pairs if a != b)

    # ---- flags -------------------------------------------------------------------------------------------------
    flag_pairs, per_flag, disagreements = [], {f: [] for f in FLAGS}, []
    for pid in ids:
        for f in FLAGS:
            g, c = gt[pid][f].strip(), cs[pid][f].strip()
            if g in ("0", "1") and c in ("0", "1"):
                flag_pairs.append((g, c))
                per_flag[f].append((g, c))
                if g != c:
                    disagreements.append((pid, cs[pid].get("project_name", pid), f, g, c, cs[pid].get("notes", "").strip()))
    fp = sum(1 for a, b in flag_pairs if a == "0" and b == "1")
    fn = sum(1 for a, b in flag_pairs if a == "1" and b == "0")

    # ---- composite score ----------------------------------------------------------------------------------------
    gt_cci = [sum(int(gt[pid][f]) for f in FLAGS) for pid in ids]
    cs_cci = [sum(int(cs[pid][f]) for f in FLAGS) for pid in ids]
    rho = spearmanr(gt_cci, cs_cci).correlation if spearmanr else float("nan")
    mad = sum(abs(a - b) for a, b in zip(gt_cci, cs_cci)) / len(ids)

    L = [f"# Claim-intensity pilot — inter-coder reliability (N = {len(ids)} cards)", "",
         "## 1. Tier classification", "",
         f"- Artifacts compared: {len(tier_pairs)}",
         f"- Raw agreement: {100 * agreement(tier_pairs):.1f}%",
         f"- Cohen's κ: {kappa(tier_pairs):.3f}; Krippendorff's α: {alpha(tier_pairs):.3f}",
         "- Disagreements by direction (curator -> coder): " + (", ".join(f"{k}: {v}" for k, v in tier_dir.most_common()) or "none"),
         "", "## 2. Flags", "",
         "| Flag | N | Agreement | Cohen's κ | Krippendorff's α | Curator %1 | Coder %1 | FP | FN |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for f in FLAGS:
        p = per_flag[f]
        L.append(f"| {f} | {len(p)} | {agreement(p):.3f} | {kappa(p):.3f} | {alpha(p):.3f} | "
                 f"{100 * sum(1 for a, _ in p if a == '1') / len(p):.0f}% | {100 * sum(1 for _, b in p if b == '1') / len(p):.0f}% | "
                 f"{sum(1 for a, b in p if a == '0' and b == '1')} | {sum(1 for a, b in p if a == '1' and b == '0')} |")
    L += ["", f"- Flag pairs: {len(flag_pairs)}; raw agreement {100 * agreement(flag_pairs):.1f}%; "
              f"Cohen's κ {kappa(flag_pairs):.3f}; Krippendorff's α {alpha(flag_pairs):.3f}",
          f"- False positives (coder 1, curator 0): {fp}; false negatives: {fn}",
          "", "## 3. Composite score (sum of the 13 flags)", "",
          f"- Spearman ρ: {rho:.3f}; mean absolute difference: {mad:.2f}",
          "", "## 4. Flag disagreements", "", "| Card | Flag | Curator | Coder | Coder's note |", "|---|---|---|---|---|"]
    L += [f"| {name} ({pid}) | {f} | {g} | {c} | {note} |" for pid, name, f, g, c, note in disagreements]
    L.append(f"\nTotal flag disagreements: {len(disagreements)}")
    (HERE / "irr_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"tiers: n={len(tier_pairs)} agreement={100 * agreement(tier_pairs):.1f}% alpha={alpha(tier_pairs):.3f}")
    print(f"flags: n={len(flag_pairs)} agreement={100 * agreement(flag_pairs):.1f}% alpha={alpha(flag_pairs):.3f} "
          f"kappa={kappa(flag_pairs):.3f} FP={fp} FN={fn} rho={rho:.3f} MAD={mad:.2f}")


if __name__ == "__main__":
    main()
