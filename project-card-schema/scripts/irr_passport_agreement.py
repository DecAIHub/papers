"""
Agreement between the independent coder's passport-field coding (coding tool export, task 1) and the curator's
values in the deposit (v1.1.0), for the 50 sampled cards.

The coder chose from the controlled lists of the first version of the descriptor (Table 7 of v1.0.0): 20 Category
labels, one token model out of 7, one ai_component class out of 10, one use_case class out of 10, plus
"cannot determine" (nd) and "none of the list" (nil, with a free-text suggestion). The curator's free-text
ai_component / use_case descriptors of the sampled cards are mapped onto the same lists by a mapping
table approved by the curator (irr/mapping_sample50_to_table7.csv; __not_assignable__ = descriptor states that no
component / use case was established). Category labels outside the coder's list are mapped by the same table.

Usage: python irr_passport_agreement.py <irr_results_task1.json> <project_cards.json> <out_json>
           --sample-map <mapping_sample50_to_table7.csv> [--strata <verdicts.csv>] [--seed 20260905]
--strata: CSV with columns card (candidate number) and manual_class (live-same | partial | live-changed | dead)
describing the state of a card's sources at coding time; statistics are then also given for the live-same stratum.
"""
import csv
import json
import random
import sys
from collections import Counter

import numpy as np

TT_MECH = {"governance": "governance", "staking": "staking", "payment": "payments", "reward": "rewards", "security": "security"}
CODER_CATEGORY = {"Infra", "AI/Other", "AI/Agents", "DeFi", "Meme", "AI/Compute", "Consumer", "AI/Data", "Gaming", "AI/Inference",
                  "AI/Analytics", "DePIN", "Metaverse", "Social", "NFT", "DAO", "Privacy", "Stablecoin", "Bridge", "Oracle"}
NA = "__not_assignable__"


def alpha_nominal(pairs):
    if not pairs:
        return None
    vals = [v for p in pairs for v in p]
    n = len(vals)
    counts = Counter(vals)
    Do = sum(1 for a, b in pairs if a != b) / len(pairs)
    De = 1 - sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))
    return 1.0 if De == 0 else 1 - Do / De


def alpha_jaccard(pairs):
    def d(a, b):
        a, b = set(a), set(b)
        return 0.0 if not a and not b else 1 - len(a & b) / len(a | b)
    vals = [v for p in pairs for v in p]
    n = len(vals)
    Do = np.mean([d(a, b) for a, b in pairs])
    De = np.mean([d(vals[i], vals[j]) for i in range(n) for j in range(n) if i != j])
    return 1.0 if De == 0 else 1 - Do / De


def kappa(pairs):
    a = [p[0] for p in pairs]; b = [p[1] for p in pairs]
    n = len(pairs)
    po = sum(1 for x, y in pairs if x == y) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def boot(stat, pairs, B, rng):
    vals = []
    for _ in range(B):
        sample = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
        v = stat(sample)
        if v is not None:
            vals.append(v)
    return [round(float(np.percentile(vals, 2.5)), 3), round(float(np.percentile(vals, 97.5)), 3)]


def load_sample_map(path):
    m = {"ai_component": {}, "use_case": {}, "Category": {}}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        m[r["field"]][r["curator_value"]] = r["coder_vocabulary_class"]
    return m


def compute(coder, deposit, smap, seed):
    rng = random.Random(seed)
    B = 2000
    out = {"n_cards": len(coder), "seed": seed, "bootstrap": B}

    # ---- Category ------------------------------------------------------------------------------------------
    pairs, nd = [], 0
    for pid, ans in coder.items():
        f = ans["fields"]["Category"]
        cur = deposit[pid]["passport"]["Category"]
        cur_set = []
        for lab in (cur.split(" | ") if cur else []):
            for t in smap["Category"].get(lab, lab).split(" | "):
                if t in CODER_CATEGORY and t not in cur_set:
                    cur_set.append(t)
        if f["nd"] or f["nil"]:
            nd += 1
            continue
        pairs.append((sorted(f["canon"]), sorted(cur_set)))
    lab_k = {}
    labels = Counter(l for a, b in pairs for l in set(a) | set(b))
    for lab, c in labels.items():
        if c >= 3:
            lab_k[lab] = round(kappa([(lab in a, lab in b) for a, b in pairs]), 3)
    out["Category"] = {"pairs": len(pairs), "coder_nd_or_nil": nd, "exact_set_match": sum(1 for a, b in pairs if a == b),
                       "any_overlap": sum(1 for a, b in pairs if set(a) & set(b)),
                       "mean_jaccard": round(float(np.mean([len(set(a) & set(b)) / len(set(a) | set(b)) for a, b in pairs])), 3),
                       "alpha_jaccard": round(alpha_jaccard(pairs), 3), "alpha_jaccard_ci": boot(alpha_jaccard, pairs, 500, rng),
                       "per_label_kappa": dict(sorted(lab_k.items(), key=lambda kv: -kv[1]))}

    # ---- ai_component -----------------------------------------------------------------------------------------
    bin_pairs, val_pairs, unmapped = [], [], []
    for pid, ans in coder.items():
        f = ans["fields"]["ai_component"]
        p = deposit[pid]["passport"]
        coder_cls = None if (f["nd"] or f["nil"] or not f["canon"]) else f["canon"][0]
        bin_pairs.append((coder_cls is not None, p["ai_component_status"] == "identified"))
        if p["ai_component"] is not None and p["ai_component_status"] == "identified":
            cur_cls = smap["ai_component"].get(p["ai_component"])
            if cur_cls is None:
                unmapped.append(p["ai_component"])
            elif coder_cls is not None and cur_cls != NA:
                val_pairs.append((coder_cls, cur_cls))
    out["ai_component"] = {
        "binary_identifiable_component": {"pairs": len(bin_pairs), "agreement": round(sum(1 for a, b in bin_pairs if a == b) / len(bin_pairs), 3),
                                          "kappa": round(kappa(bin_pairs), 3), "kappa_ci": boot(kappa, bin_pairs, B, rng)},
        "class_among_valued": {"pairs": len(val_pairs), "agreement": round(sum(1 for a, b in val_pairs if a == b) / len(val_pairs), 3) if val_pairs else None,
                               "alpha": round(alpha_nominal(val_pairs), 3) if val_pairs else None,
                               "alpha_ci": boot(alpha_nominal, val_pairs, B, rng) if val_pairs else None,
                               "disagreements": sorted(Counter(f"{a} vs {b}" for a, b in val_pairs if a != b).items(), key=lambda kv: -kv[1])},
        "curator_values_without_mapping": unmapped,
    }

    # ---- use_case -----------------------------------------------------------------------------------------------
    val_pairs, unmapped, nd = [], [], 0
    for pid, ans in coder.items():
        f = ans["fields"]["use_case"]
        cur = deposit[pid]["passport"]["use_case"]
        if f["nd"] or f["nil"] or not f["canon"]:
            nd += 1
            continue
        if cur is None:
            continue
        cur_cls = smap["use_case"].get(cur)
        if cur_cls is None:
            unmapped.append(cur)
        elif cur_cls != NA:
            val_pairs.append((f["canon"][0], cur_cls))
    out["use_case"] = {"coder_nd": nd, "coder_other": sum(1 for a in coder.values() if a["fields"]["use_case"]["canon"] == ["other"]),
                       "class_among_valued": {"pairs": len(val_pairs), "agreement": round(sum(1 for a, b in val_pairs if a == b) / len(val_pairs), 3) if val_pairs else None,
                                              "alpha": round(alpha_nominal(val_pairs), 3) if val_pairs else None,
                                              "alpha_ci": boot(alpha_nominal, val_pairs, B, rng) if val_pairs else None,
                                              "both_other": sum(1 for a, b in val_pairs if a == b == "other")},
                       "curator_values_without_mapping": unmapped}

    # ---- token_type ---------------------------------------------------------------------------------------------
    bin_pairs, mech_ok, mech_n, nd = [], 0, 0, 0
    for pid, ans in coder.items():
        f = ans["fields"]["token_type"]
        p = deposit[pid]["passport"]
        cur_cls, cur_mech = p["token_type"], set(p["token_mechanisms"] or [])
        if f["nd"]:
            nd += 1
            continue
        coder_val = "meme" if f["nil"] and "meme" in (f["sugg"] or "").lower() else (f["canon"][0] if f["canon"] else None)
        if coder_val is None:
            nd += 1
            continue
        coder_has_model = coder_val != "none"
        cur_has_model = cur_cls not in (None, "none", "unknown")
        bin_pairs.append((coder_has_model, cur_has_model))
        if coder_has_model and cur_has_model:
            mech_n += 1
            if (coder_val == "utility" and cur_cls == "utility") or (coder_val == "meme" and cur_cls == "meme") or \
               (coder_val in TT_MECH and TT_MECH[coder_val] in cur_mech):
                mech_ok += 1
    out["token_type"] = {"coder_nd": nd,
                         "binary_has_token_model": {"pairs": len(bin_pairs), "agreement": round(sum(1 for a, b in bin_pairs if a == b) / len(bin_pairs), 3), "kappa": round(kappa(bin_pairs), 3)},
                         "mechanism_level": {"pairs": mech_n, "agreement": round(mech_ok / mech_n, 3) if mech_n else None}}

    # ---- concordance on missing values: where the curator recorded no value, what did the coder find? -----------
    def coder_answer(f, field):
        if f["nd"]:
            return "cannot_determine"
        if field == "token_type" and (f["canon"] == ["none"] or (f["nil"] and "no product utility" in (f["sugg"] or "").lower())):
            return "none"
        return "value_assigned" if (f["canon"] or f["nil"]) else "cannot_determine"

    conc = {}
    sel = {"token_type": lambda p: p["token_type"] in (None, "unknown"),
           "ai_component": lambda p: p["ai_component_status"] in (None, "unknown", "positioning_only", "none"),
           "use_case": lambda p: p["use_case"] is None}
    for field, is_missing in sel.items():
        c = Counter(coder_answer(ans["fields"][field], field) for pid, ans in coder.items() if is_missing(deposit[pid]["passport"]))
        conc[field] = {"curator_missing_or_unknown": sum(c.values()), "coder": dict(c)}
    has_value = {"token_type": lambda p: p["token_type"] not in (None, "unknown"),
                 "ai_component": lambda p: p["ai_component_status"] == "identified",
                 "use_case": lambda p: p["use_case"] is not None}
    conc["coder_cannot_determine_where_curator_has_value"] = {
        field: sum(1 for pid, ans in coder.items() if ans["fields"][field]["nd"] and has_value[field](deposit[pid]["passport"]))
        for field in has_value}
    out["missingness_concordance"] = conc
    return out


def main():
    coder = json.load(open(sys.argv[1], encoding="utf-8"))["task1"]
    deposit = {r["project_id"]: r for r in json.load(open(sys.argv[2], encoding="utf-8"))}
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 20260905
    smap = load_sample_map(sys.argv[sys.argv.index("--sample-map") + 1])
    out = compute(coder, deposit, smap, seed)
    if "--strata" in sys.argv:
        verdicts = {r["card"]: r["manual_class"] for r in csv.DictReader(open(sys.argv[sys.argv.index("--strata") + 1], encoding="utf-8-sig"))}
        out["source_status_at_coding"] = dict(Counter(verdicts.values()))
        live = {pid: ans for pid, ans in coder.items() if verdicts.get(pid.split("-")[0]) == "live-same"}
        out["live_same_stratum"] = compute(live, deposit, smap, seed)
    json.dump(out, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
