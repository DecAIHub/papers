"""
Compute all review-fix items:
1. Leave-one-annotator-out pairwise EA + kappa for OC_3
2. Post-hoc power analysis for OC_3
3. A4 (strategic decluttering) simulation
4. Generate Figure S2 (confusion matrices) and Figure S3 (FP/FN taxonomy)
"""
import json
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Raw per-annotator JSON files (annotator{1,2,3}_{baseline,intervention}.json)
# are not redistributed in the public replication package (see Data Availability
# in the paper). If you have obtained them (e.g., for peer review), drop them
# into scripts/iaa_pilot/results/ or point DECAIHUB_IAA_DIR to their location.
IAA_DIR = os.environ.get(
    "DECAIHUB_IAA_DIR",
    os.path.join(SCRIPT_DIR, "iaa_pilot", "results"),
)
OUT = os.path.join(SCRIPT_DIR, "..", "figures")
OUT = os.path.normpath(OUT)
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

PAL = {
    "blue": "#2C73D2", "red": "#D63031", "green": "#00B894",
    "orange": "#E17055", "purple": "#6C5CE7", "gray": "#636E72",
    "light": "#DFE6E9", "yellow": "#FDCB6E", "teal": "#00CEC9",
    "dark": "#2D3436",
}


def load_annotations():
    import sys
    data = {}
    for phase in ["baseline", "intervention"]:
        data[phase] = {}
        for a_idx in [1, 2, 3]:
            fname = os.path.join(IAA_DIR, f"annotator{a_idx}_{phase}.json")
            if not os.path.exists(fname):
                sys.stderr.write(
                    f"Raw annotator file not found: {fname}\n\n"
                    "The per-annotator JSON files are not redistributed in the public\n"
                    "replication package (see Data Availability in the paper). If you\n"
                    "have obtained them (peer review / reasonable request), drop them\n"
                    "into scripts/iaa_pilot/results/ or point the env var\n"
                    "DECAIHUB_IAA_DIR to their directory and rerun.\n"
                )
                sys.exit(2)
            with open(fname, "r", encoding="utf-8") as f:
                records = json.load(f)
            data[phase][a_idx] = {r["project_id"]: r for r in records}
    return data


def cohens_kappa_2x2(a, b):
    n = len(a)
    if n == 0:
        return 0.0
    tp = sum(1 for i in range(n) if a[i] == 1 and b[i] == 1)
    tn = sum(1 for i in range(n) if a[i] == 0 and b[i] == 0)
    fp = sum(1 for i in range(n) if a[i] == 0 and b[i] == 1)
    fn = sum(1 for i in range(n) if a[i] == 1 and b[i] == 0)
    po = (tp + tn) / n
    pe = ((tp + fn) * (tp + fp) + (fp + tn) * (fn + tn)) / (n * n)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def exact_agreement(a, b):
    n = len(a)
    if n == 0:
        return 0.0
    return sum(1 for i in range(n) if a[i] == b[i]) / n


# ================================================================
# 1. Leave-one-annotator-out analysis for OC_3
# ================================================================
def leave_one_out():
    data = load_annotations()
    flag = "OC_3"
    pairs = [(1, 2), (1, 3), (2, 3)]
    pair_labels = ["A1-A2 (excl. A3)", "A1-A3 (excl. A2)", "A2-A3 (excl. A1)"]

    print("\n=== Leave-One-Annotator-Out: OC_3 ===")
    print(f"{'Pair':<22} {'Phase':<14} {'EA':>8} {'kappa':>8} {'n1':>5} {'n0':>5}")
    print("-" * 70)

    results = {}
    for (a1, a2), label in zip(pairs, pair_labels):
        for phase in ["baseline", "intervention"]:
            pids = sorted(set(data[phase][a1].keys()) & set(data[phase][a2].keys()))
            vals_a = [data[phase][a1][pid][flag] for pid in pids]
            vals_b = [data[phase][a2][pid][flag] for pid in pids]
            ea = exact_agreement(vals_a, vals_b)
            kappa = cohens_kappa_2x2(vals_a, vals_b)
            n1_a = sum(vals_a)
            n1_b = sum(vals_b)
            print(f"{label:<22} {phase:<14} {ea:>7.1%} {kappa:>8.3f}   {n1_a:>2}/{n1_b:>2}")
            results[(label, phase)] = {"ea": ea, "kappa": kappa, "n1_a": n1_a, "n1_b": n1_b}

    print("\n=== Leave-One-Out Delta (Intervention - Baseline) ===")
    print(f"{'Pair':<22} {'dEA':>8} {'dKappa':>8}")
    print("-" * 40)
    for (a1, a2), label in zip(pairs, pair_labels):
        b = results[(label, "baseline")]
        i = results[(label, "intervention")]
        d_ea = i["ea"] - b["ea"]
        d_k = i["kappa"] - b["kappa"]
        print(f"{label:<22} {d_ea:>+7.1%} {d_k:>+8.3f}")

    return results


# ================================================================
# 2. Post-hoc power analysis
# ================================================================
def power_analysis():
    from scipy.stats import norm

    p1 = 0.433  # baseline EA for OC_3 (3-annotator)
    p2 = 0.650  # intervention EA for OC_3
    n = 60
    alpha = 0.05

    h = 2 * math.asin(math.sqrt(p2)) - 2 * math.asin(math.sqrt(p1))

    z_alpha = norm.ppf(1 - alpha / 2)
    power = norm.cdf(abs(h) * math.sqrt(n) - z_alpha)

    print("\n=== Post-Hoc Power Analysis (OC_3) ===")
    print(f"Baseline EA:     {p1:.1%}")
    print(f"Intervention EA: {p2:.1%}")
    print(f"n (profiles):    {n}")
    print(f"Cohen's h:       {h:.3f}")
    print(f"alpha:           {alpha}")
    print(f"Post-hoc power:  {power:.1%}")
    print(f"Conclusion:      n=60 provides {power:.0%} power to detect h={h:.2f}")

    for target_ea in [0.55, 0.60, 0.65, 0.70]:
        h_t = 2 * math.asin(math.sqrt(target_ea)) - 2 * math.asin(math.sqrt(p1))
        pwr = norm.cdf(abs(h_t) * math.sqrt(n) - z_alpha)
        print(f"  If target EA = {target_ea:.0%}: h = {h_t:.3f}, power = {pwr:.1%}")

    return {"h": h, "power": power, "n": n, "alpha": alpha}


# ================================================================
# 3. A4 (strategic decluttering) simulation
# ================================================================
def run_a4_simulation():
    np.random.seed(321)

    segments = {
        "Meme":         {"N": 103, "mu": 0.718, "lam": 0.730},
        "Metaverse":    {"N":  13, "mu": 0.462, "lam": 0.600},
        "Consumer":     {"N":  52, "mu": 0.462, "lam": 0.596},
        "DeFi":         {"N": 112, "mu": 0.455, "lam": 0.590},
        "AI/Other":     {"N": 247, "mu": 0.587, "lam": 0.560},
        "AI/Agents":    {"N": 220, "mu": 0.450, "lam": 0.557},
        "Gaming":       {"N":  35, "mu": 0.514, "lam": 0.552},
        "AI/Analytics": {"N":  22, "mu": 0.318, "lam": 0.545},
        "Infra":        {"N": 384, "mu": 0.438, "lam": 0.532},
        "AI/Data":      {"N":  44, "mu": 0.409, "lam": 0.513},
        "AI/Inference": {"N":  25, "mu": 0.440, "lam": 0.480},
        "AI/Compute":   {"N":  55, "mu": 0.436, "lam": 0.478},
        "DePIN":        {"N":  17, "mu": 0.294, "lam": 0.441},
    }

    FLAGS_PER_PROFILE = 5
    N_TRIALS = 500
    N_BOOTSTRAP = 2000
    PI_LEVELS = [0.1, 0.3, 0.5]

    results = {}

    for pi in PI_LEVELS:
        detected_mu = 0
        detected_lam = 0
        detected_union = 0
        total_tests = 0

        for seg_name, seg in segments.items():
            N = seg["N"]
            base_mu = seg["mu"]
            base_lam = seg["lam"]

            base_mixed = np.random.binomial(1, base_mu, (N_BOOTSTRAP, N))
            bootstrap_mu_se = np.std([m.mean() for m in base_mixed])

            n_flags = N * FLAGS_PER_PROFILE
            base_unresolved = int(round(n_flags * base_lam))
            flag_resolved = np.zeros(n_flags, dtype=int)
            flag_resolved[:n_flags - base_unresolved] = 1
            bootstrap_lams = []
            for _ in range(N_BOOTSTRAP):
                idx = np.random.choice(N, N, replace=True)
                sel_flags = []
                for i in idx:
                    sel_flags.extend(
                        flag_resolved[i * FLAGS_PER_PROFILE:(i + 1) * FLAGS_PER_PROFILE]
                    )
                sel_flags = np.array(sel_flags)
                bootstrap_lams.append(1 - sel_flags.mean())
            bootstrap_lam_se = np.std(bootstrap_lams)

            for trial in range(N_TRIALS):
                mixed = np.random.binomial(1, base_mu, N)
                flags = np.zeros((N, FLAGS_PER_PROFILE), dtype=int)
                for i in range(N):
                    n_resolved = int(round(FLAGS_PER_PROFILE * (1 - base_lam)))
                    flags[i, :n_resolved] = 1

                n_contaminate = max(1, int(round(pi * N)))
                contam_idx = np.random.choice(N, n_contaminate, replace=False)

                for ci in contam_idx:
                    mixed[ci] = 0
                    unresolved = np.where(flags[ci] == 0)[0]
                    if len(unresolved) > 0:
                        flags[ci, unresolved[0]] = 1

                new_mu = mixed.mean()
                new_lam = 1 - flags.mean()

                detect_mu = abs(new_mu - base_mu) > 1.96 * bootstrap_mu_se
                detect_lam = abs(new_lam - base_lam) > 1.96 * bootstrap_lam_se

                detected_mu += int(detect_mu)
                detected_lam += int(detect_lam)
                detected_union += int(detect_mu or detect_lam)
                total_tests += 1

        power_mu = detected_mu / total_tests
        power_lam = detected_lam / total_tests
        power_union = detected_union / total_tests
        results[pi] = (power_mu, power_lam, power_union)

    print("\n=== A4 Strategic Decluttering Simulation ===")
    print("  " + "-" * 60)
    print(f"  {'Scenario':<25} {'pi':>5} {'P(mu)':>8} {'P(lam)':>8} {'P(union)':>8}")
    print("  " + "-" * 60)
    for pi in PI_LEVELS:
        pm, pl, pu = results[pi]
        print(f"  {'A4 (strat. declutter)':<25} {pi:>5.1f} {pm:>8.3f} {pl:>8.3f} {pu:>8.3f}")
    print("  " + "-" * 60)

    return results


# ================================================================
# 4. Figure S2: Confusion matrices for OC_3 (intervention)
# ================================================================
def fig_s2_confusion():
    data = load_annotations()
    phase = "intervention"
    flag = "OC_3"
    pairs = [(1, 2, "A1 vs A2"), (1, 3, "A1 vs A3"), (2, 3, "A2 vs A3")]

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

    for ax, (a1, a2, title) in zip(axes, pairs):
        pids = sorted(set(data[phase][a1].keys()) & set(data[phase][a2].keys()))
        vals_a = [data[phase][a1][pid][flag] for pid in pids]
        vals_b = [data[phase][a2][pid][flag] for pid in pids]

        tp = sum(1 for i in range(len(pids)) if vals_a[i] == 1 and vals_b[i] == 1)
        tn = sum(1 for i in range(len(pids)) if vals_a[i] == 0 and vals_b[i] == 0)
        fp = sum(1 for i in range(len(pids)) if vals_a[i] == 0 and vals_b[i] == 1)
        fn = sum(1 for i in range(len(pids)) if vals_a[i] == 1 and vals_b[i] == 0)

        cm = np.array([[tn, fp], [fn, tp]])
        kappa = cohens_kappa_2x2(vals_a, vals_b)
        ea = exact_agreement(vals_a, vals_b)

        im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=max(60, cm.max()))
        for i in range(2):
            for j in range(2):
                color = "white" if cm[i, j] > 25 else PAL["dark"]
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        fontsize=22, fontweight="bold", color=color)

        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        a2_label = f"A{a2}"
        a1_label = f"A{a1}"
        ax.set_xticklabels(["0", "1"])
        ax.set_yticklabels(["0", "1"])
        ax.set_xlabel(a2_label, fontsize=16)
        ax.set_ylabel(a1_label, fontsize=16)
        ax.set_title(f"{title}\n$\\kappa$={kappa:.3f}, EA={ea:.1%}", fontsize=15)

    fig.suptitle("OC_3 Pairwise Confusion Matrices (Intervention Phase)", fontsize=18, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_s2_iaa_confusion.png"))
    plt.close(fig)
    print("  OK fig_s2_iaa_confusion.png")


# ================================================================
# 5. Figure S3: FP/FN boundary mechanism taxonomy
# ================================================================
def fig_s3_taxonomy():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(-0.5, 14)
    ax.set_ylim(-0.5, 7.5)
    ax.axis("off")

    root = FancyBboxPatch((4.5, 6.2), 5, 1.0, boxstyle="round,pad=0.1",
                           facecolor=PAL["dark"], edgecolor="white", lw=1.5)
    ax.add_patch(root)
    ax.text(7, 6.7, "Boundary Mechanisms", ha="center", va="center",
            fontsize=17, fontweight="bold", color="white")

    fp_box = FancyBboxPatch((0.3, 4.2), 5.0, 0.8, boxstyle="round,pad=0.1",
                             facecolor=PAL["red"], edgecolor="white", lw=1.5, alpha=0.85)
    ax.add_patch(fp_box)
    ax.text(2.8, 4.6, "False-Positive Mechanisms", ha="center", va="center",
            fontsize=16, fontweight="bold", color="white")

    fn_box = FancyBboxPatch((8.2, 4.2), 5.0, 0.8, boxstyle="round,pad=0.1",
                             facecolor=PAL["blue"], edgecolor="white", lw=1.5, alpha=0.85)
    ax.add_patch(fn_box)
    ax.text(10.7, 4.6, "False-Negative Mechanisms", ha="center", va="center",
            fontsize=16, fontweight="bold", color="white")

    ax.plot([7, 2.8], [6.08, 5.14], color=PAL["red"], lw=1.8, alpha=0.45,
            solid_capstyle="round", zorder=0)
    ax.plot([7, 10.7], [6.08, 5.14], color=PAL["blue"], lw=1.8, alpha=0.45,
            solid_capstyle="round", zorder=0)

    fp_items = [
        "FP1: Weak-evidence inflation\n(Tier-2/3 qty mimics coverage)",
        "FP2: Narrow-source masking\n(low gap via 1-2 artifact types)",
        "FP3: Category-norm effects\n(relative completeness masks weakness)",
        "FP4: Template anchoring\n(pre-fill biases assessment)",
    ]
    fn_items = [
        "FN1: Critical-field missingness\n(token_type 43.5%, AI 22.4%)",
        "FN2: Platform availability bias\n(non-EVM fewer standard sources)",
        "FN3: Documentation heterogeneity\n(sector norms vs. corpus thresholds)",
        "FN4: Emerging-project penalty\n(young projects few artifacts)",
    ]

    ax.plot([2.8, 2.8], [4.0, 0.1], color=PAL["red"], lw=0.8, alpha=0.3, zorder=0)
    ax.plot([10.7, 10.7], [4.0, 0.1], color=PAL["blue"], lw=0.8, alpha=0.3, zorder=0)

    for i, txt in enumerate(fp_items):
        y = 3.1 - i * 0.9
        bb = FancyBboxPatch((0.1, y - 0.32), 5.4, 0.64, boxstyle="round,pad=0.06",
                             facecolor="#FFEAEA", edgecolor=PAL["red"], lw=0.8,
                             alpha=1.0, zorder=1)
        ax.add_patch(bb)
        ax.text(2.8, y, txt, ha="center", va="center", fontsize=12,
                color=PAL["dark"], zorder=2)

    for i, txt in enumerate(fn_items):
        y = 3.1 - i * 0.9
        bb = FancyBboxPatch((8.0, y - 0.32), 5.4, 0.64, boxstyle="round,pad=0.06",
                             facecolor="#E8F4FD", edgecolor=PAL["blue"], lw=0.8,
                             alpha=1.0, zorder=1)
        ax.add_patch(bb)
        ax.text(10.7, y, txt, ha="center", va="center", fontsize=12,
                color=PAL["dark"], zorder=2)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_s3_fpfn_taxonomy.png"))
    plt.close(fig)
    print("  OK fig_s3_fpfn_taxonomy.png")


# ================================================================
# Main
# ================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("REVIEW FIX COMPUTATIONS")
    print("=" * 70)

    loo_results = leave_one_out()
    power_results = power_analysis()

    print("\nRunning A4 simulation (may take ~30s)...")
    a4_results = run_a4_simulation()

    print("\nGenerating supplementary figures...")
    fig_s2_confusion()
    fig_s3_taxonomy()

    print("\nDone.")
