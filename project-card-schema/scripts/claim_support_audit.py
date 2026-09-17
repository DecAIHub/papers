"""
Claim-support audit (September 2026): does the cited artifact support the recorded claim?

Usage: python claim_support_audit.py <sample.json> <irr_results_task2.json> <out.json> [--probe <t1_probe.csv>]

sample.json (seed 20260824) defines the 150 evidence entries (claim_support.entries: card number, URL, claim_field, tier); the
coder's answer for entry i is stored under the id "<project_id>#e<i+1>" in the coding-tool export (supports / partial /
no, or dead = artifact not available to the coder). With --probe, 'no' answers whose URL returned HTTP 404 in the T1
persistence audit are counted separately. Confidence intervals are Wilson 95%.
"""
import csv
import io
import json
import math
import sys
from collections import Counter


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - hw), 1), round(100 * (c + hw), 1)]


def main():
    entries = json.load(io.open(sys.argv[1], encoding="utf-8"))["claim_support"]["entries"]
    answers = json.load(io.open(sys.argv[2], encoding="utf-8"))["task2"]
    probe = {}
    if "--probe" in sys.argv:
        probe = {r["url"]: r["t0_class"] for r in csv.DictReader(io.open(sys.argv[sys.argv.index("--probe") + 1], encoding="utf-8"))}
    joined = []
    for key, a in answers.items():
        i = int(key.split("#e")[1]) - 1
        e = entries[i]
        assert e["num"] == key.split("-")[0], key
        joined.append({"id": key, "tier": e["tier"], "claim_field": e["claim_field"], "url": e["url"],
                       "verdict": "dead" if a["dead"] else a["support"], "seconds": a["seconds"]})
    avail = [j for j in joined if j["verdict"] != "dead"]
    full = [j for j in avail if j["verdict"] == "supports"]
    out = {"date": "September 2026", "n": len(joined), "by_tier": dict(Counter(j["tier"] for j in joined)),
           "verdicts": dict(Counter(j["verdict"] for j in joined)),
           "available": len(avail), "fully_supports": len(full), "fully_supports_pct": round(100 * len(full) / len(avail), 1),
           "fully_supports_ci": wilson(len(full), len(avail)),
           "partial": sum(1 for j in avail if j["verdict"] == "partial"), "no": sum(1 for j in avail if j["verdict"] == "no"),
           "by_tier_full_over_available": {t: [sum(1 for j in full if j["tier"] == t), sum(1 for j in avail if j["tier"] == t)]
                                           for t in ["Tier-1", "Tier-2", "Tier-3"]},
           "by_field_full_over_available": {f: [sum(1 for j in full if j["claim_field"] == f), sum(1 for j in avail if j["claim_field"] == f)]
                                            for f in sorted({j["claim_field"] for j in joined})},
           "coder_hours": round(sum(j["seconds"] for j in joined) / 3600, 1),
           "non_supported": [{"id": j["id"], "tier": j["tier"], "claim_field": j["claim_field"], "verdict": j["verdict"],
                              "t1_status": probe.get(j["url"])} for j in avail if j["verdict"] != "supports"]}
    if probe:
        out["no_with_http_404_at_t1"] = sum(1 for j in avail if j["verdict"] == "no" and probe.get(j["url"]) == "http_404")
    json.dump(out, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
