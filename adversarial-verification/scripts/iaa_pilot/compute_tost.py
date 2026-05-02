"""
TOST equivalence testing for null-effect exploratory IAA flags.

Design: within-subjects paired binary (3-way exact agreement per profile,
before vs. after operational-definition intervention). n = 60 profiles,
k = 3 annotators, 4 flags (OC_3 primary, AI_2/OC_2/TK_1 exploratory).

Method: paired two one-sided tests (Schuirmann, 1987) on proportion
differences using McNemar-style discordant-pair variance. Equivalence
margin Delta is pre-specified; primary Delta_EA = 0.10, sensitivity
Delta_EA = 0.15.

Output: results/tost_equivalence.json with p_equiv, 90% CI, decisions
per flag per Delta.

Usage: python compute_tost.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.environ.get(
    "DECAIHUB_IAA_DIR",
    os.path.join(SCRIPT_DIR, "results"),
)

FLAGS = ["AI_2", "OC_2", "OC_3", "TK_1"]
ANNOTATORS = [1, 2, 3]
PHASES = ["baseline", "intervention"]

PRIMARY_DELTA = 0.10
SENSITIVITY_DELTA = 0.15
ALPHA_ONE_SIDED = 0.05


def load_phase(phase: str) -> Dict[int, Dict[int, Dict[str, int]]]:
    """Return data[project_id][annotator_idx][flag] = 0/1."""
    by_pid: Dict[int, Dict[int, Dict[str, int]]] = {}
    for a_idx in ANNOTATORS:
        fname = os.path.join(RESULTS_DIR, f"annotator{a_idx}_{phase}.json")
        if not os.path.exists(fname):
            sys.stderr.write(
                f"Raw annotator file not found: {fname}\n\n"
                "The per-annotator JSON files (annotator{1,2,3}_{baseline,intervention}.json)\n"
                "are not redistributed in the public replication package (see Data\n"
                "Availability in the paper). If you have obtained them (peer review /\n"
                "reasonable request), drop them into scripts/iaa_pilot/results/ or point\n"
                "the env var DECAIHUB_IAA_DIR to their directory and rerun.\n\n"
                "The expected TOST output is included at results/tost_equivalence.json\n"
                "for reference (reproduced from the raw data with this script).\n"
            )
            sys.exit(2)
        with open(fname, "r", encoding="utf-8") as f:
            records = json.load(f)
        for r in records:
            pid = r["project_id"]
            if pid not in by_pid:
                by_pid[pid] = {}
            by_pid[pid][a_idx] = {flag: int(r[flag]) for flag in FLAGS}
    return by_pid


def profile_agreement(profile: Dict[int, Dict[str, int]], flag: str) -> int:
    """Return 1 if all 3 annotators agree on this flag for this profile, else 0."""
    vals = {profile[a][flag] for a in ANNOTATORS}
    return 1 if len(vals) == 1 else 0


def build_paired_vectors(flag: str) -> Tuple[List[int], List[int]]:
    """Return (baseline_agree[0/1], intervention_agree[0/1]) aligned by project_id."""
    base = load_phase("baseline")
    interv = load_phase("intervention")
    common = sorted(set(base) & set(interv))
    b_vec: List[int] = []
    i_vec: List[int] = []
    for pid in common:
        b_vec.append(profile_agreement(base[pid], flag))
        i_vec.append(profile_agreement(interv[pid], flag))
    return b_vec, i_vec


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_ppf(p: float) -> float:
    """Inverse standard-normal CDF via Beasley-Springer-Moro approximation."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    # Abramowitz-Stegun-style rational approximation (accurate to ~7.5 decimals)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p_low = 0.02425
    p_high = 1.0 - p_low
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
               ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1.0)
    if p > p_high:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1.0)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q / \
           (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1.0)


def paired_tost_binary(baseline: List[int], intervention: List[int],
                       delta: float, alpha: float = ALPHA_ONE_SIDED) -> Dict:
    """Paired TOST for two correlated binary proportions (McNemar variance).

    H01: p_i - p_b <= -delta   (substantial decrease)
    H02: p_i - p_b >= +delta   (substantial increase)
    Reject both at alpha one-sided => equivalence within +/- delta.
    """
    n = len(baseline)
    assert n == len(intervention) and n > 0
    p_b = sum(baseline) / n
    p_i = sum(intervention) / n
    diff = p_i - p_b
    # Discordant pairs
    b = sum(1 for j in range(n) if baseline[j] == 1 and intervention[j] == 0)
    c = sum(1 for j in range(n) if baseline[j] == 0 and intervention[j] == 1)
    # Variance of paired-proportion difference (standard McNemar Wald form)
    # Var(p_i - p_b) = (b + c - (c - b)^2 / n) / n^2
    # Apply continuity guard to avoid division by zero on zero-discordance
    var_diff = (b + c - ((c - b) ** 2) / n) / (n ** 2)
    if var_diff <= 0.0:
        # Fall back to independent-proportion Wald SE (conservative upper bound)
        var_diff = (p_b * (1.0 - p_b) + p_i * (1.0 - p_i)) / n
    se = math.sqrt(var_diff)
    # One-sided z-tests
    z_lower = (diff - (-delta)) / se if se > 0 else float("inf")  # H01: diff > -delta
    z_upper = ((+delta) - diff) / se if se > 0 else float("inf")  # H02: diff < +delta
    p_lower = 1.0 - normal_cdf(z_lower)
    p_upper = 1.0 - normal_cdf(z_upper)
    p_equiv = max(p_lower, p_upper)
    # 1 - 2*alpha two-sided CI (conventional TOST reporting at 90% when alpha=0.05)
    ci_level = 1.0 - 2.0 * alpha
    z_ci = normal_ppf(1.0 - alpha)
    ci_lower = diff - z_ci * se
    ci_upper = diff + z_ci * se
    decision = (
        "equivalent" if p_equiv < alpha
        else "inconclusive"
    )
    return {
        "n": n,
        "p_baseline": round(p_b, 4),
        "p_intervention": round(p_i, 4),
        "delta_ea_pp": round(100.0 * diff, 2),
        "discordant_b": b,
        "discordant_c": c,
        "se": round(se, 4),
        "delta_margin": delta,
        "z_lower_vs_neg_delta": round(z_lower, 3),
        "z_upper_vs_pos_delta": round(z_upper, 3),
        "p_lower": round(p_lower, 4),
        "p_upper": round(p_upper, 4),
        "p_equiv": round(p_equiv, 4),
        "ci_level": round(ci_level, 2),
        "ci_lower_pp": round(100.0 * ci_lower, 2),
        "ci_upper_pp": round(100.0 * ci_upper, 2),
        "decision": decision,
    }


def main() -> None:
    results = {
        "metadata": {
            "design": "within-subjects paired binary 3-way exact agreement",
            "n_profiles": 60,
            "k_annotators": 3,
            "flags": FLAGS,
            "primary_delta_ea": PRIMARY_DELTA,
            "sensitivity_delta_ea": SENSITIVITY_DELTA,
            "alpha_one_sided": ALPHA_ONE_SIDED,
            "test": "Paired TOST (Schuirmann, 1987), McNemar-style SE for "
                    "correlated proportions",
        },
        "per_flag": {},
    }
    print("=" * 70)
    print(f"TOST equivalence (paired, McNemar SE), alpha={ALPHA_ONE_SIDED} one-sided")
    print("=" * 70)
    for flag in FLAGS:
        baseline, intervention = build_paired_vectors(flag)
        flag_out = {
            "ea_baseline": round(sum(baseline) / len(baseline), 4),
            "ea_intervention": round(sum(intervention) / len(intervention), 4),
            f"delta_{str(PRIMARY_DELTA).replace('.', '')}": paired_tost_binary(
                baseline, intervention, PRIMARY_DELTA),
            f"delta_{str(SENSITIVITY_DELTA).replace('.', '')}": paired_tost_binary(
                baseline, intervention, SENSITIVITY_DELTA),
        }
        results["per_flag"][flag] = flag_out
        primary = flag_out[f"delta_{str(PRIMARY_DELTA).replace('.', '')}"]
        sens = flag_out[f"delta_{str(SENSITIVITY_DELTA).replace('.', '')}"]
        print(f"\n{flag}:")
        print(f"  EA baseline    : {flag_out['ea_baseline']:.3f}")
        print(f"  EA intervention: {flag_out['ea_intervention']:.3f}")
        print(f"  Delta EA (pp)  : {primary['delta_ea_pp']:+.2f}")
        print(f"  90% CI         : [{primary['ci_lower_pp']:+.2f}, {primary['ci_upper_pp']:+.2f}] pp")
        print(f"  SE             : {primary['se']:.4f}")
        print(f"  Discordant b/c : {primary['discordant_b']}/{primary['discordant_c']}")
        print(f"  Delta=0.10     : p_equiv={primary['p_equiv']:.4f}  -> {primary['decision']}")
        print(f"  Delta=0.15     : p_equiv={sens['p_equiv']:.4f}  -> {sens['decision']}")
    out_path = os.path.join(RESULTS_DIR, "tost_equivalence.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n" + "=" * 70)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
