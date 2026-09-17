"""
Build the ABPC v1.1.0 deposit from the parsed cards (extract_cards.py output).

Usage: python build_deposit.py <cards_raw.json> <out_dir> [--archive archive_map.json]

Writes  <out_dir>/project_cards.json, <out_dir>/cards/<project_id>.json,
        <out_dir>/project_card.schema.json (copied from ../schema),
        <out_dir>/build_report.json (counts used by the descriptor).
"""
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import vocab

SCHEMA_VERSION = "1.1.0"
URL_CHECK_DATE = "2026-03-05"
HERE = Path(__file__).resolve().parent

# claim_field derivation rule, unchanged from v1.0.0 (extract_zenodo.py) for continuity.
CLAIM_KEYWORDS = {
    "ai_component": ["ai", "ии", "модел", "inference", "train", "llm", "ml ", "machine learn", "нейро", "neural",
                     "nlp", "gpt", "семантич", "semantic", "intelligen", "copilot", "analytics", "аналитик",
                     "compute", "вычисл"],
    "use_case": ["use case", "use-case", "сценарий", "применен", "portfolio", "trading", "marketplace", "gaming",
                 "content creat", "security audit", "identity", "prediction", "labeling"],
    "token_type": ["токен", "token", "staking", "governance", "utility", "reward", "payment", "erc-20", "bep-20",
                   "spl", "supply", "mint"],
    "chain": ["контракт", "contract", "mainnet", "chain", "сеть", "explorer", "etherscan", "basescan", "solscan",
              "bscscan", "polygonscan", "onchain", "on-chain", "on\u2011chain", "развёрнут"],
    "type": ["evm", "non-evm", "appchain", "l1", "l2", "rollup", "sidechain", "infrastructure"],
}


def infer_claim_field(note):
    low = (note or "").lower()
    scores = {f: sum(1 for kw in kws if kw in low) for f, kws in CLAIM_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Category"


def txt(v):
    """Exported text: template hyphens normalised, residual Russian annotations rendered in English (vocab.py)."""
    return vocab.render_english(v)


def links_clean(v):
    """Link values are URLs or {type, url} entries; only the free-text `type` needs rendering."""
    if isinstance(v, list):
        return [{**x, "type": txt(x["type"])} if isinstance(x, dict) else x for x in v] or None
    return v or None


def build_record(c, archive):
    p = c["passport"]
    cats, cats_raw = vocab.map_category(p.get("Category"))
    tt_class, mechs = vocab.map_token_type(p.get("token_type"))
    passport = {
        "Category": " | ".join(cats) if cats else None,
        "Category_raw": txt(" | ".join(cats_raw)) if cats_raw else None,
        "chain": vocab.map_chain(p.get("chain")),
        "chain_raw": txt(p.get("chain")),
        "type": vocab.map_type(p.get("type")),
        "type_raw": txt(p.get("type")),
        "token_type": tt_class,
        "token_type_raw": txt(p.get("token_type")),
        "token_mechanisms": mechs,
        "ai_component": txt(p.get("ai_component")),
        "ai_component_status": vocab.ai_component_status(p.get("ai_component")),
        "use_case": txt(p.get("use_case")),
        "launch_date": c.get("launch_date"),
        "launch_date_raw": txt(p.get("launch_date")),
    }
    L = c["links"]
    links = {
        "website": L.get("website"),
        "documentation": L.get("documentation"),
        "whitepaper": L.get("whitepaper"),
        "repository": L.get("repository"),
        "releases": L.get("releases"),
        "roadmap": L.get("roadmap"),
        "security_advisories": L.get("security_advisories"),
        "app": L.get("app"),
        "bug_bounty": L.get("bug_bounty"),
        "coingecko": L.get("coingecko"),
        "coinmarketcap": L.get("coinmarketcap"),
        "explorer": links_clean(L.get("explorer")),
        "audit": links_clean(L.get("audit")),
        "social": links_clean(L.get("social")),
        "other": links_clean(L.get("other")),
    }
    # one row per (source URL, associated field); the curator's source notes stay in the cards and are used only to
    # derive claim_field
    evidence, seen = [], set()
    for e in c["evidence"]:
        cf = infer_claim_field(e.get("claim_note"))
        if (e["source_url"], cf) in seen:
            continue
        seen.add((e["source_url"], cf))
        a = archive.get(e["source_url"]) if archive else None
        if a and a.get("error"):
            a = None
        evidence.append({
            "claim_field": cf,
            "source_url": e["source_url"],
            "tier": e["tier"],
            "verified_date": URL_CHECK_DATE,
            "archive_url": a["archive_url"] if a else None,
            "archive_timestamp": a["timestamp"] if a else None,
        })
    gaps = [{"tier": g["tier"], "kind": g["kind"]} for g in c["evidence_gaps"]]
    return {
        "project_id": c["project_id"],
        "schema_version": SCHEMA_VERSION,
        "name": txt(p.get("name")),
        "ticker": txt(p.get("ticker")),
        "token_contract": vocab.render_english(p.get("token_contract"), strip_backticks=True),
        "stub": cats is None,
        "card_verified_date": p.get("last_verified"),
        "passport": passport,
        "links": links,
        "evidence": evidence,
        "evidence_gaps": gaps,
    }


def main():
    cards = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2])
    archive = {}
    if "--archive" in sys.argv:
        ap = Path(sys.argv[sys.argv.index("--archive") + 1])
        if ap.exists():
            archive = json.load(open(ap, encoding="utf-8"))
    records = [build_record(c, archive) for c in cards]
    out.mkdir(parents=True, exist_ok=True)
    (out / "project_cards.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    cdir = out / "cards"
    if cdir.exists():
        shutil.rmtree(cdir)
    cdir.mkdir()
    for r in records:
        (cdir / f"{r['project_id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(HERE.parent / "schema" / "project_card.schema.json", out / "project_card.schema.json")

    # ---- report ---------------------------------------------------------------
    rep = {"records": len(records), "stubs": sum(r["stub"] for r in records)}
    ev = [e for r in records for e in r["evidence"]]
    rep["evidence_entries"] = len(ev)
    rep["evidence_by_tier"] = dict(Counter(e["tier"] for e in ev))
    rep["unique_tier1_urls"] = len({e["source_url"] for e in ev if e["tier"] == "Tier-1"})
    rep["unique_urls"] = len({e["source_url"] for e in ev})
    rep["evidence_with_archive"] = sum(1 for e in ev if e["archive_url"])
    rep["evidence_gaps"] = sum(len(r["evidence_gaps"] or []) for r in records)
    rep["evidence_gaps_by_kind"] = dict(Counter(g["kind"] for r in records for g in (r["evidence_gaps"] or [])))
    rep["claim_field_distribution"] = dict(Counter(e["claim_field"] for e in ev))
    for f in ["Category", "chain", "type", "token_type", "ai_component", "use_case", "launch_date"]:
        rep[f"null_{f}"] = sum(1 for r in records if r["passport"][f] is None)
    rep["unknown_token_type"] = sum(1 for r in records if r["passport"]["token_type"] == "unknown")
    rep["dist_token_type"] = dict(Counter(r["passport"]["token_type"] for r in records if r["passport"]["token_type"]).most_common())
    rep["dist_ai_component_status"] = dict(Counter(r["passport"]["ai_component_status"] for r in records if r["passport"]["ai_component_status"]).most_common())
    rep["unknown_use_case"] = sum(1 for r in records if vocab.use_case_is_unknown(r["passport"]["use_case"]))
    rep["dist_chain"] = dict(Counter(r["passport"]["chain"] for r in records if r["passport"]["chain"]).most_common())
    rep["dist_type"] = dict(Counter(r["passport"]["type"] for r in records if r["passport"]["type"]).most_common())
    cat = Counter()
    for r in records:
        if r["passport"]["Category"]:
            for lab in r["passport"]["Category"].split(" | "):
                cat[lab] += 1
    rep["dist_Category"] = dict(cat.most_common())
    rep["links_nonnull"] = {k: sum(1 for r in records if r["links"][k]) for k in records[0]["links"]}
    rep["cards_with_tier1"] = sum(1 for r in records if any(e["tier"] == "Tier-1" for e in r["evidence"]))
    (out / "build_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if not k.startswith("dist_")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
