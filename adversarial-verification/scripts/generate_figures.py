"""
Generate all 5 publication-quality figures for the C_verification article
and run the A2* cross-effect simulation.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "figures"))
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 16,
    "axes.labelsize": 18,
    "axes.titlesize": 19,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

PAL = {
    "blue": "#2C73D2",
    "red": "#D63031",
    "green": "#00B894",
    "orange": "#E17055",
    "purple": "#6C5CE7",
    "gray": "#636E72",
    "light": "#DFE6E9",
    "yellow": "#FDCB6E",
    "teal": "#00CEC9",
    "dark": "#2D3436",
}


# ───────── Figure 1: Verification Pipeline ─────────
def fig1_pipeline():
    fig, ax = plt.subplots(figsize=(14, 3.74))
    ax.set_xlim(-0.3, 14.3)
    ax.set_ylim(-1.75, 2.15)
    ax.axis("off")

    boxes = [
        (1.0, 1, "Adversarial\nThreat Modeling\n(A1\u2013A4)", PAL["red"]),
        (4.0, 1, "Two-Proxy\nDiagnostic\nConstruction\n(\u03bc, \u03bb)", PAL["orange"]),
        (7.0, 1, "Protocol\nDesign\n(Op-Def Template)", PAL["blue"]),
        (10.0, 1, "IAA\nValidation\n(k=3, n=60)", PAL["green"]),
        (13.0, 1, "Boundary\nDiagnostics\n(6 Case Types)", PAL["purple"]),
    ]

    BW, BH = 1.3, 0.95
    for x, y, txt, color in boxes:
        bb = FancyBboxPatch(
            (x - BW, y - BH), BW * 2, BH * 2,
            boxstyle="round,pad=0.12",
            facecolor=color, edgecolor="white", alpha=0.88, linewidth=1.5,
        )
        ax.add_patch(bb)
        ax.text(x, y, txt, ha="center", va="center",
                fontsize=13, color="white", fontweight="bold", linespacing=1.2)

    sec_labels = ["\u00a73.2", "\u00a73.2", "\u00a73.3", "\u00a73.3", "\u00a73.4"]
    for i, (x, y, _, _) in enumerate(boxes):
        ax.text(x, y - BH - 0.2, sec_labels[i], ha="center", va="top",
                fontsize=12, color=PAL["gray"], style="italic")

    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + BW
        x2 = boxes[i + 1][0] - BW
        ax.annotate("", xy=(x2, 1), xytext=(x1, 1),
                     arrowprops=dict(arrowstyle="-|>", color=PAL["dark"],
                                     lw=1.8, connectionstyle="arc3,rad=0"))

    t = np.linspace(0, np.pi, 120)
    arc_top = -0.35
    rx, depth = 6.0, 1.0
    arc_x = 7.0 + rx * np.cos(t)
    arc_y = arc_top - depth * np.sin(t)
    ax.plot(arc_x[:-8], arc_y[:-8], ls="--", color=PAL["gray"], lw=1.4,
            alpha=0.7, zorder=0)
    ax.annotate("", xy=(arc_x[-1], arc_y[-1]),
                xytext=(arc_x[-8], arc_y[-8]),
                arrowprops=dict(arrowstyle="-|>", color=PAL["gray"],
                                lw=1.4, linestyle="--"))
    ax.text(7.0, arc_top - depth - 0.2, "Iterative Refinement",
            ha="center", va="top", fontsize=13, color=PAL["gray"],
            style="italic")

    fig.savefig(os.path.join(OUT, "fig1_pipeline.png"))
    plt.close(fig)
    print("  OK fig1_pipeline.png")


# ───────── Figure 2: Detection Matrix (Adversary × Proxy) ─────────
def fig2_threat_model():
    fig, ax = plt.subplots(figsize=(6.5, 4.2))

    adversaries = ["A1: Selective\nDisclosure", "A2: Ambiguity\nInjection",
                   "A3: Claim\nInflation", "A4: Strategic\nDecluttering"]
    proxies = [r"$\mu$ (Mixed-Tier)", r"$\lambda$ (Cons.-Loss)",
               r"$\mu \vee \lambda$ (Union)"]

    matrix = np.array([
        [0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0],
        [0.6, 0.6, 1.0],
        [0.5, 0.05, 0.53],
    ])

    cmap_custom = plt.cm.colors.LinearSegmentedColormap.from_list(
        "detect", [PAL["light"], PAL["yellow"], PAL["green"]], N=256
    )

    im = ax.imshow(matrix, cmap=cmap_custom, aspect="auto", vmin=0, vmax=1)

    labels = [
        ["Blind", "Detects\n(0.46\u20131.00)", "Detects\n(0.46\u20131.00)"],
        ["Detects\n(0.08\u20130.92)", "Blind", "Detects\n(0.08\u20130.92)"],
        ["Partial\n(0.18\u20130.94)", "Partial\n(0.15\u20130.46)", "Strong\n(0.27\u20130.94)"],
        ["Partial\n(0.16\u20130.79)", "Weak\n(0.00\u20130.08)", "Partial\n(0.16\u20130.79)"],
    ]

    for i in range(4):
        for j in range(3):
            color = "white" if matrix[i, j] >= 0.8 else PAL["dark"]
            ax.text(j, i, labels[i][j], ha="center", va="center",
                    fontsize=12, fontweight="bold", color=color)

    ax.set_xticks(range(3))
    ax.set_xticklabels(proxies, fontsize=14)
    ax.set_yticks(range(4))
    ax.set_yticklabels(adversaries, fontsize=13)
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)

    for edge in ["top", "bottom", "left", "right"]:
        ax.spines[edge].set_visible(False)
    ax.set_xticks(np.arange(3 + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(4 + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_threat_model.png"))
    plt.close(fig)
    print("  OK fig2_threat_model.png")


# ───────── Figure 3: Decision Tree for Boundary Classification ─────────
def fig3_decision_tree():
    fig = plt.figure(figsize=(11.4, 8))
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_xlim(0, 27)
    ax.set_ylim(0, 19)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    DW, DH = 3.8, 1.3
    LW, LH = 4.2, 1.3
    EC = "#94A3B8"

    def dbox(x, y, txt):
        ax.add_patch(FancyBboxPatch(
            (x - DW / 2, y - DH / 2), DW, DH,
            boxstyle="round,pad=0.08", fc="#EFF5FF", ec="#4A90D9", lw=2, zorder=2))
        ax.text(x, y, txt, ha="center", va="center", fontsize=13,
                color="#1E293B", fontweight="semibold", zorder=3, linespacing=1.15)

    def lbox(x, y, l1, l2, col):
        ax.add_patch(FancyBboxPatch(
            (x - LW / 2, y - LH / 2), LW, LH,
            boxstyle="round,pad=0.08", fc=col, ec="white", lw=1.8,
            zorder=2))
        ax.text(x, y + 0.15, l1, ha="center", va="center", fontsize=11,
                color="white", fontweight="bold", zorder=3)
        ax.text(x, y - 0.22, l2, ha="center", va="center", fontsize=11,
                color="white", alpha=0.92, zorder=3)

    def link(x1, y1, x2, y2, lab, side):
        my = (y1 + y2) / 2
        ax.plot([x1, x1, x2, x2], [y1, my, my, y2],
                color=EC, lw=1.5, solid_capstyle="round", zorder=1)
        off = -0.35 if side == "left" else 0.35
        ax.text((x1 + x2) / 2 + off, my + 0.2, lab, fontsize=14,
                color="#64748B", fontweight="bold", ha="center",
                bbox=dict(fc="white", ec="none", pad=1, alpha=0.92), zorder=4)

    Y = [17.5, 14.2, 10.8, 7.4, 3.8]

    dbox(11.5, Y[0], "Gap > 0.25?")

    link(11.5, Y[0] - DH / 2, 5.5, Y[1] + DH / 2, "Yes", "left")
    link(11.5, Y[0] - DH / 2, 17.5, Y[1] + DH / 2, "No", "right")
    dbox(5.5, Y[1], "Token type\nmissing?")
    dbox(17.5, Y[1], "Critical field\nmissing?")

    link(5.5, Y[1] - DH / 2, 2.5, Y[2] + LH / 2, "Yes", "left")
    link(5.5, Y[1] - DH / 2, 8, Y[2] + LH / 2, "No", "right")
    lbox(2.5, Y[2], "D: Indeterminate", "(19.8%)", PAL["red"])
    lbox(8, Y[2], "B: FP — Weak Ev.", "(9.6%)", PAL["orange"])

    link(17.5, Y[1] - DH / 2, 13, Y[2] + LH / 2, "Yes", "left")
    link(17.5, Y[1] - DH / 2, 19.5, Y[2] + DH / 2, "No", "right")
    lbox(13, Y[2], "C: FN — Doc Deficit", "(20.1%)", PAL["teal"])
    dbox(19.5, Y[2], "Tier-1 types\n\u2265 3?")

    link(19.5, Y[2] - DH / 2, 15.5, Y[3] + LH / 2, "No", "left")
    link(19.5, Y[2] - DH / 2, 22, Y[3] + DH / 2, "Yes", "right")
    lbox(15.5, Y[3], "E: FP — Narrow Ev.", "(11.2%)", PAL["purple"])
    dbox(22, Y[3], "Gap > 0.15?")

    link(22, Y[3] - DH / 2, 18.5, Y[4] + LH / 2, "Yes", "left")
    link(22, Y[3] - DH / 2, 24, Y[4] + LH / 2, "No", "right")
    lbox(18.5, Y[4], "F: Conditional", "(15.6%)", PAL["yellow"])
    lbox(24, Y[4], "A: Stable Positive", "(23.7%)", PAL["green"])

    fig.savefig(os.path.join(OUT, "fig3_decision_tree.png"))
    plt.close(fig)
    print("  OK fig3_decision_tree.png")


# ───────── Figure 4: IAA Baseline vs Intervention ─────────
def fig4_iaa():
    # Values must match Table 7 in the manuscript. These per-flag exact-agreement
    # numbers are recomputed from raw annotator JSONs (see _preflight_csi.py check
    # `numeric_integrity_table7`). Do NOT edit without re-running the preflight.
    flags = ["AI_2", "OC_2", "OC_3", "TK_1"]
    kappa_base = [0.856, 0.771, 0.163, 0.712]
    kappa_int = [0.876, 0.675, 0.242, 0.535]
    ea_base = [90.0, 88.3, 38.3, 83.3]
    ea_int = [91.7, 88.3, 60.0, 83.3]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), sharey=False)
    x = np.arange(len(flags))
    w = 0.32

    bars1a = ax1.bar(x - w / 2, kappa_base, w, label="Baseline",
                      color=PAL["gray"], alpha=0.7, edgecolor="white")
    bars1b = ax1.bar(x + w / 2, kappa_int, w, label="Intervention",
                      color=PAL["blue"], alpha=0.85, edgecolor="white")
    ax1.axhline(0.40, ls="--", color=PAL["red"], lw=1, alpha=0.6)
    ax1.text(3.5, 0.42, "\"Fair\" threshold", fontsize=12, color=PAL["red"],
             ha="right", style="italic")
    ax1.set_xticks(x)
    ax1.set_xticklabels(flags)
    ax1.set_ylabel("Fleiss' κ")
    ax1.set_title("(a) Fleiss' κ by flag")
    ax1.set_ylim(0, 1.05)
    ax1.legend(loc="upper left", framealpha=0.8)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    bars2a = ax2.bar(x - w / 2, ea_base, w, label="Baseline",
                      color=PAL["gray"], alpha=0.7, edgecolor="white")
    bars2b = ax2.bar(x + w / 2, ea_int, w, label="Intervention",
                      color=PAL["green"], alpha=0.85, edgecolor="white")
    ax2.set_xticks(x)
    ax2.set_xticklabels(flags)
    ax2.set_ylabel("Exact Agreement (%)")
    ax2.set_title("(b) Exact Agreement by flag")
    ax2.set_ylim(0, 110)
    ax2.legend(loc="upper left", framealpha=0.8)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    ax2.annotate("+21.7 pp\np = 0.028 *",
                 xy=(2 + w / 2, ea_int[2]),
                 xytext=(2.05, 96),
                 fontsize=13, fontweight="bold", color=PAL["red"],
                 arrowprops=dict(arrowstyle="-|>", color=PAL["red"], lw=1.2),
                 ha="center")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4_iaa_results.png"))
    plt.close(fig)
    print("  OK fig4_iaa_results.png")


# ───────── Figure 5: Boundary Case-Type Distribution ─────────
def fig5_boundary():
    labels = [
        "A: Stable\nPositive",
        "B: FP —\nWeak Evidence",
        "C: FN —\nDoc Deficit",
        "D: Indeterminate",
        "E: FP —\nNarrow Evidence",
        "F: Conditional\nStability",
    ]
    counts = [200, 81, 170, 167, 95, 132]
    total = sum(counts)
    pcts = [c / total * 100 for c in counts]
    colors = [PAL["green"], PAL["orange"], PAL["teal"],
              PAL["red"], PAL["purple"], PAL["yellow"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6),
                                    gridspec_kw={"width_ratios": [1.3, 1]})

    bars = ax1.barh(range(len(labels)), counts, color=colors, alpha=0.85,
                     edgecolor="white", height=0.7)
    ax1.set_yticks(range(len(labels)))
    ax1.set_yticklabels(labels, fontsize=14)
    ax1.set_xlabel("Number of profiles")
    ax1.set_title("(a) Case-type distribution (N = 845)")
    ax1.invert_yaxis()
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    for i, (cnt, pct) in enumerate(zip(counts, pcts)):
        ax1.text(cnt + 5, i, f"{cnt} ({pct:.1f}%)", va="center", fontsize=14)

    boundary_total = sum(counts[1:])
    a_pct = counts[0] / total * 100
    bnd_pct = boundary_total / total * 100
    wedge_labels = [f"Stable (A)\n{a_pct:.1f}%", f"Boundary (B-F)\n{bnd_pct:.1f}%"]
    wedge_colors = [PAL["green"], PAL["red"]]
    wedge_sizes = [counts[0], boundary_total]

    wedges, texts, autotexts = ax2.pie(
        wedge_sizes, labels=wedge_labels, colors=wedge_colors,
        autopct="", startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=15, fontweight="bold"),
    )
    ax2.set_title("(b) Boundary vs. stable")

    ax2.text(0, 0, f"{bnd_pct:.1f}%\nboundary",
             ha="center", va="center", fontsize=18, fontweight="bold",
             color=PAL["red"])

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig5_boundary_typology.png"))
    plt.close(fig)
    print("  OK fig5_boundary_typology.png")


# ───────── A2* Cross-Effect Simulation ─────────
def run_crosseffect_simulation():
    """
    Simulate A2* (padding with incidental claim resolution).
    Uses segment-level statistics from Table 4 of the article.
    """
    np.random.seed(42)

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
        "AI/Inference":  {"N":  25, "mu": 0.440, "lam": 0.480},
        "AI/Compute":   {"N":  55, "mu": 0.436, "lam": 0.478},
        "DePIN":        {"N":  17, "mu": 0.294, "lam": 0.441},
    }

    FLAGS_PER_PROFILE = 5
    P_RESOLVE = 0.15
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
                mixed[contam_idx] = 1

                for ci in contam_idx:
                    if np.random.random() < P_RESOLVE:
                        unresolved = np.where(flags[ci] == 0)[0]
                        if len(unresolved) > 0:
                            flags[ci, unresolved[0]] = 1

                new_mu = mixed.mean()
                new_lam = 1 - flags.mean()

                detect_mu = (new_mu - base_mu) > 1.96 * bootstrap_mu_se
                detect_lam = abs(new_lam - base_lam) > 1.96 * bootstrap_lam_se

                detected_mu += int(detect_mu)
                detected_lam += int(detect_lam)
                detected_union += int(detect_mu or detect_lam)
                total_tests += 1

        power_mu = detected_mu / total_tests
        power_lam = detected_lam / total_tests
        power_union = detected_union / total_tests
        results[pi] = (power_mu, power_lam, power_union)

    print("\n  A2* Cross-Effect Simulation Results:")
    print("  " + "-" * 60)
    print(f"  {'Scenario':<25} {'pi':>5} {'P(mu)':>8} {'P(lam)':>8} {'P(union)':>8}")
    print("  " + "-" * 60)
    for pi in PI_LEVELS:
        pm, pl, pu = results[pi]
        print(f"  {'A2* (padding+resolve)':<25} {pi:>5.1f} {pm:>8.3f} {pl:>8.3f} {pu:>8.3f}")
    print("  " + "-" * 60)

    return results


# ───────── A3 Claim-Inflation Simulation ─────────
def run_a3_simulation():
    """
    Simulate A3 (claim inflation): compound adversary that
    (i) inflates mixed-tier indicator (like A2) AND
    (ii) introduces one additional unresolved flag per contaminated profile.
    """
    np.random.seed(123)

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
                    mixed[ci] = 1
                    resolved = np.where(flags[ci] == 1)[0]
                    if len(resolved) > 0:
                        flags[ci, resolved[-1]] = 0

                new_mu = mixed.mean()
                new_lam = 1 - flags.mean()

                detect_mu = (new_mu - base_mu) > 1.96 * bootstrap_mu_se
                detect_lam = (new_lam - base_lam) > 1.96 * bootstrap_lam_se

                detected_mu += int(detect_mu)
                detected_lam += int(detect_lam)
                detected_union += int(detect_mu or detect_lam)
                total_tests += 1

        power_mu = detected_mu / total_tests
        power_lam = detected_lam / total_tests
        power_union = detected_union / total_tests
        results[pi] = (power_mu, power_lam, power_union)

    print("\n  A3 Claim-Inflation Simulation Results:")
    print("  " + "-" * 60)
    print(f"  {'Scenario':<25} {'pi':>5} {'P(mu)':>8} {'P(lam)':>8} {'P(union)':>8}")
    print("  " + "-" * 60)
    for pi in PI_LEVELS:
        pm, pl, pu = results[pi]
        print(f"  {'A3 (claim inflation)':<25} {pi:>5.1f} {pm:>8.3f} {pl:>8.3f} {pu:>8.3f}")
    print("  " + "-" * 60)

    return results


# ───────── Main ─────────
if __name__ == "__main__":
    print("Generating publication figures...")
    fig1_pipeline()
    fig2_threat_model()
    fig3_decision_tree()
    fig4_iaa()
    fig5_boundary()

    print("\nRunning A2* cross-effect simulation...")
    sim_results = run_crosseffect_simulation()

    print("\nRunning A3 claim-inflation simulation...")
    a3_results = run_a3_simulation()

    print("\nDone. All figures saved to:", OUT)
