"""
Summarise the T1 persistence audit (2026-09-05) from its per-URL log and the deposit.

Usage: python persistence_audit_summary.py <project_cards.json> <t1_probe.csv> <t1_retry.csv> <out.json>

The probe log covers every evidence URL of deposit v1.0.0 plus the link-table URLs of the cards (10,219 URLs); its
`tiers` column carries the tier(s) at which a URL is cited. Card-level figures are computed by joining the deposit's
Tier-1 evidence URLs to the log.
"""
import csv
import io
import json
import sys
from collections import Counter

# the log truncates exception text, so match on the prefix of urllib3's NameResolutionError
DNS_MARKERS = ("nameresolution", "getaddrinfo", "name or service not known", "nodename nor servname", "failed to resolve")


def main():
    cards = json.load(io.open(sys.argv[1], encoding="utf-8"))
    probe = list(csv.DictReader(io.open(sys.argv[2], encoding="utf-8")))
    retry = list(csv.DictReader(io.open(sys.argv[3], encoding="utf-8")))
    by_url = {r["url"]: r for r in probe}

    def tier_stats(tier):
        rows = [r for r in probe if tier in (r["tiers"] or "").split("|")]
        ok = sum(1 for r in rows if r["t0_class"] == "reachable")
        return {"n": len(rows), "reachable": ok, "reachable_pct": round(100 * ok / len(rows), 1),
                "by_class": dict(Counter(r["t0_class"] for r in rows))}

    out = {"date": "2026-09-05", "urls": len(probe), "by_class": dict(Counter(r["t0_class"] for r in probe)),
           "reachable_pct": round(100 * sum(1 for r in probe if r["t0_class"] == "reachable") / len(probe), 1)}
    for t in ["Tier-1", "Tier-2", "Tier-3"]:
        out[t] = tier_stats(t)
    tier1_urls = {e["source_url"] for c in cards for e in c["evidence"] if e["tier"] == "Tier-1"}
    logged = [u for u in tier1_urls if u in by_url]
    dns = [u for u in logged if any(m in (by_url[u]["detail"] or "").lower() for m in DNS_MARKERS)]
    out["deposit_tier1"] = {"urls": len(tier1_urls), "in_log": len(logged), "dns_failures": len(dns),
                            "dns_failures_pct": round(100 * len(dns) / len(logged), 1),
                            "cards_with_unreachable_tier1": sum(1 for c in cards if any(
                                e["tier"] == "Tier-1" and e["source_url"] in by_url and by_url[e["source_url"]]["t0_class"] != "reachable"
                                for e in c["evidence"]))}
    out["retry"] = {"retried": len(retry), "recovered": sum(1 for r in retry if r["t0_class"] == "reachable")}
    json.dump(out, open(sys.argv[4], "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
