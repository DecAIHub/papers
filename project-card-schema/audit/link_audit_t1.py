#!/usr/bin/env python3
"""
Link-reachability re-audit (T1) of the ABPC evidence layer.

Same probe protocol as the T0 audit reported in the manuscript (2026-03-05):
  HEAD request, 8 s timeout, redirects followed, GET fallback on HTTP 405,
  User-Agent "DecAIHub-Audit/1.0 (research; link-reachability check)",
  classes: reachable (2xx/3xx/403) | 404 | other error | timeout.

Differences from T0 (all additive):
  * the whole population is probed (every evidence URL of deposit v1.0.0 plus
    the links_* URLs of the project cards), not a 150-URL sample;
  * a per-URL log is written (status, final URL, domain change, elapsed),
    which makes the *next* re-audit (T2) a paired comparison;
  * a retry pass (--retry) re-probes only failures several hours later, to
    separate transient from persistent failures.

Execution model: one sequential lane per registrable domain (politeness delay
inside the lane; github.com 1.5 s, others 0.4 s), lanes run concurrently
(--workers). The run of 2026-09-05 (10,219 URLs) took 61 min with 16 workers.
The output CSV is never overwritten silently (--force) — a stopped run whose
Python process is still alive would otherwise corrupt the file.

Usage:
    python link_audit_t1.py --deposit project_cards.json [--cards <cards_dir>] --workers 16
                                                  # full run -> t1_probe_<date>.csv + t1_summary_<date>.json
    python link_audit_t1.py --deposit project_cards.json --limit 10 --tag dry   # dry run on a random 10 URLs (+6 github)
    python link_audit_t1.py --retry t1_probe_2026-09-05.csv   # re-probe failures only
The 2026-09-05 run used deposit v1.0.0 and the curator's card files (links_* tables); without --cards only the
evidence URLs of the deposit are probed.

Requirements: Python 3.9+, requests
"""
import argparse
import csv
import json
import random
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, date
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    sys.exit("ERROR: 'requests' package is required. Install with: pip install requests")

DEPOSIT = None   # set from --deposit
PROJECTS = None  # set from --cards (optional)
HERE = Path(__file__).parent

# T0 protocol constants (do not change: comparability)
TIMEOUT = 8
HEADERS = {"User-Agent": "DecAIHub-Audit/1.0 (research; link-reachability check)"}

# T0 reference (manuscript, 2026-03-05): 150-URL sample of 3,674 unique Tier-1 URLs
T0 = {"date": "2026-03-05", "population": 3674, "n": 150,
      "reachable": 134, "http_404": 7, "other_error": 7, "timeout": 2}

LINK_TYPE_EN = {
    "CoinMarketCap (профиль, справочно)": "CoinMarketCap (profile, reference)",
    "CoinGecko (профиль, справочно)": "CoinGecko (profile, reference)",
}

WORKERS = 8
SAME_DOMAIN_DELAY = 0.4  # seconds between requests to the same host (politeness)
MULTI = "|"  # separator inside multi-value CSV fields (kinds/tiers/claim_fields/cards);
             # not ";" — Excel in many locales (ru, de, ...) treats ";" as the column delimiter
SLOW_HOSTS = {"github.com": 1.5, "raw.githubusercontent.com": 1.5, "gitbook.io": 1.0}
# HTTP 429 (rate limiting) is an artefact of probing volume, not of link decay:
# back off and re-probe up to RATE_LIMIT_RETRIES times before recording the 429.
RATE_LIMIT_RETRIES = 1   # GitHub answers 429 to any non-browser client on /commits/ pages
RATE_LIMIT_SLEEP = 10    # regardless of back-off (verified 2026-09-04) -> one retry is enough
                         # seconds (Retry-After header honoured when present)


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------
def host_of(url: str) -> str:
    return (urlparse(url).netloc or "").lower()


def reg_domain(host: str) -> str:
    """Naive registrable domain: strip leading 'www.', keep last two labels."""
    h = host.split(":")[0]
    if h.startswith("www."):
        h = h[4:]
    parts = h.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else h


def load_population(only_tier1=False, only_evidence=False):
    """url -> {"kinds": set, "tiers": set, "fields": set, "cards": set}"""
    pop = defaultdict(lambda: {"kinds": set(), "tiers": set(), "fields": set(), "cards": set()})

    dep = json.loads(DEPOSIT.read_text(encoding="utf-8"))
    recs = dep if isinstance(dep, list) else dep.get("cards") or dep.get("projects")
    for r in recs:
        pid = r.get("project_id", "").split("-", 1)[0]  # card number only (matches md file prefix)
        for e in r.get("evidence", []):
            url = (e.get("source_url") or "").strip()
            tier = e.get("tier") or ""
            if not url:
                continue
            if only_tier1 and tier != "Tier-1":
                continue
            p = pop[url]
            p["kinds"].add("evidence")
            p["tiers"].add(tier)
            p["fields"].add(e.get("claim_field") or "")
            p["cards"].add(pid)

    if PROJECTS is not None and not only_evidence and not only_tier1:
        link_re = re.compile(r"###\s*Ссылки \(links_\*\)\s*\n\n\|.*?\n\|[-| ]+\n((?:\|.*\n)*)")
        for fp in sorted(PROJECTS.glob("*.ru.commonmark.md")):
            num = fp.name.split("_", 1)[0]
            m = link_re.search(fp.read_text(encoding="utf-8", errors="replace"))
            if not m:
                continue
            for row in m.group(1).strip().split("\n"):
                cells = [c.strip() for c in row.split("|")[1:-1]]
                if len(cells) >= 2 and cells[1].startswith("http"):
                    ltype = LINK_TYPE_EN.get(cells[0], cells[0])
                    p = pop[cells[1]]
                    p["kinds"].add(f"link:{ltype}")
                    p["cards"].add(num)
    return pop


# ---------------------------------------------------------------------------
# Probe (T0 protocol)
# ---------------------------------------------------------------------------
_domain_locks = defaultdict(threading.Lock)
_domain_last = {}


def classify(status, exc):
    """T0 4-class scheme."""
    if exc == "timeout":
        return "timeout"
    if exc:
        return "other_error"
    if status is None:
        return "other_error"
    if 200 <= status < 400 or status == 403:
        return "reachable"
    if status == 404:
        return "http_404"
    return "other_error"


def _request(url):
    resp = requests.head(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
    if resp.status_code == 405:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True, stream=True)
        resp.close()
    return resp


def _norm_path(u: str) -> str:
    p = urlparse(u)
    return (p.path.rstrip("/") or "/") + (("?" + p.query) if p.query else "")


def probe(url: str) -> dict:
    host = host_of(url)
    delay = SLOW_HOSTS.get(reg_domain(host), SAME_DOMAIN_DELAY)
    lock = _domain_locks[reg_domain(host)]
    rate_limited = 0
    with lock:
        last = _domain_last.get(host)
        if last is not None:
            wait = delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        t0 = time.monotonic()
        status, final_url, exc, detail = None, "", "", ""
        try:
            resp = _request(url)
            while resp.status_code == 429 and rate_limited < RATE_LIMIT_RETRIES:
                rate_limited += 1
                ra = resp.headers.get("Retry-After")
                time.sleep(min(int(ra), 60) if ra and ra.isdigit() else RATE_LIMIT_SLEEP)
                resp = _request(url)
            status, final_url = resp.status_code, resp.url
            if status == 429:
                detail = f"429 after {rate_limited} back-off retries"
        except requests.exceptions.Timeout:
            exc, detail = "timeout", "timeout"
        except requests.exceptions.SSLError as ex:
            exc, detail = "ssl_error", str(ex)[:160]
        except requests.exceptions.ConnectionError as ex:
            exc, detail = "connection_error", str(ex)[:160]
        except requests.exceptions.RequestException as ex:
            exc, detail = type(ex).__name__, str(ex)[:160]
        elapsed = int((time.monotonic() - t0) * 1000)
        _domain_last[host] = time.monotonic()

    fhost = host_of(final_url) if final_url else ""
    # soft-404 hint: same site, non-trivial original path, final path is site root
    to_root = int(bool(fhost) and reg_domain(fhost) == reg_domain(host)
                  and _norm_path(url) != "/" and _norm_path(final_url) == "/")
    return {
        "url": url,
        "status": status if status is not None else "",
        "t0_class": classify(status, exc),
        "exc": exc,
        "final_url": final_url,
        "final_host": fhost,
        "domain_changed": int(bool(fhost) and reg_domain(fhost) != reg_domain(host)),
        "redirected_to_root": to_root,
        "rate_limit_retries": rate_limited,
        "elapsed_ms": elapsed,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "detail": detail,
    }


FIELDS = ["url", "status", "t0_class", "exc", "final_url", "final_host", "domain_changed",
          "redirected_to_root", "rate_limit_retries", "elapsed_ms", "checked_at", "detail",
          "kinds", "tiers", "claim_fields", "cards"]


def run_probe(urls, pop, out_csv: Path):
    """One sequential lane per registrable domain (politeness delay inside the
    lane), lanes run concurrently. Largest domains start first so the longest
    lane (github.com, ~1.1k URLs) bounds the total run time."""
    lanes = defaultdict(list)
    for u in urls:
        lanes[reg_domain(host_of(u))].append(u)
    order = sorted(lanes, key=lambda d: -len(lanes[d]))
    results, done = [], 0
    io_lock = threading.Lock()
    total = len(urls)

    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()

        def lane(domain):
            nonlocal done
            for u in lanes[domain]:
                r = probe(u)
                meta = pop.get(u, {"kinds": set(), "tiers": set(), "fields": set(), "cards": set()})
                r["kinds"] = MULTI.join(sorted(meta["kinds"]))
                r["tiers"] = MULTI.join(sorted(t for t in meta["tiers"] if t))
                r["claim_fields"] = MULTI.join(sorted(f for f in meta["fields"] if f))
                r["cards"] = MULTI.join(sorted(meta["cards"]))
                with io_lock:
                    w.writerow(r)
                    fh.flush()
                    results.append(r)
                    done += 1
                    if done % 250 == 0:
                        print(f"  {done}/{total} probed", flush=True)

        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = [ex.submit(lane, d) for d in order]
            for f in as_completed(futs):
                f.result()  # re-raise lane exceptions
    return results


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - half) / den, (centre + half) / den)


def pct(k, n):
    return round(100.0 * k / n, 1) if n else None


def class_counts(rows):
    c = Counter(r["t0_class"] for r in rows)
    n = len(rows)
    return {"n": n, **{k: c.get(k, 0) for k in ("reachable", "http_404", "other_error", "timeout")},
            "reachable_pct": pct(c.get("reachable", 0), n),
            "domain_changed": sum(int(r["domain_changed"]) for r in rows),
            "redirected_to_root": sum(int(r["redirected_to_root"]) for r in rows),
            "http_429_residual": sum(str(r["status"]) == "429" for r in rows)}


def summarize(rows, tag):
    t1 = [r for r in rows if "Tier-1" in r["tiers"].split(MULTI)]
    by_tier = {t: class_counts([r for r in rows if t in r["tiers"].split(MULTI)])
               for t in ("Tier-1", "Tier-2", "Tier-3")}
    by_kind, small = {}, []
    for k in sorted({k for r in rows for k in r["kinds"].split(MULTI) if k}):
        rr = [r for r in rows if k in r["kinds"].split(MULTI)]
        if len(rr) >= 20 or k == "evidence":
            by_kind[k] = class_counts(rr)
        else:
            small.extend(rr)
    if small:
        by_kind["link:other (types with n<20)"] = class_counts(list({r["url"]: r for r in small}.values()))
    dom = Counter(host_of(r["url"]) for r in t1)
    top_domains = {}
    for d, cnt in dom.most_common(15):
        rr = [r for r in t1 if host_of(r["url"]) == d]
        top_domains[d] = {"n": cnt, "reachable": sum(r["t0_class"] == "reachable" for r in rr)}
    t0_lo, t0_hi = wilson(T0["reachable"], T0["n"])
    return {
        "tag": tag,
        "run_date_local": date.today().isoformat(),
        "protocol": "HEAD, 8 s timeout, redirects followed, GET on 405; classes 2xx/3xx/403 | 404 | other | timeout",
        "population_note": "all evidence URLs of deposit v1.0.0 (unique) + links_* URLs of project cards",
        "all": class_counts(rows),
        "tier1": class_counts(t1),
        "by_tier": by_tier,
        "by_kind": by_kind,
        "tier1_top_domains": top_domains,
        "t0_reference": {**T0, "reachable_pct": pct(T0["reachable"], T0["n"]),
                         "wilson95": [round(t0_lo * 100, 1), round(t0_hi * 100, 1)],
                         "note": "T0 per-URL results were not persisted; T0 sample cannot be "
                                 "reproduced URL-for-URL (seed-42 draw over the deposit set does "
                                 "not match the published domain breakdown). T1 probes the full "
                                 "population, so comparison is population(T1) vs sample(T0)."},
    }


# ---------------------------------------------------------------------------
# Retry pass
# ---------------------------------------------------------------------------
def run_retry(src_csv: Path, tag):
    rows = list(csv.DictReader(src_csv.open(encoding="utf-8")))
    fails = [r for r in rows if r["t0_class"] != "reachable"]
    print(f"retrying {len(fails)} non-reachable URLs of {len(rows)}")
    pop = {r["url"]: {"kinds": set(r["kinds"].split(MULTI)), "tiers": set(r["tiers"].split(MULTI)),
                      "fields": set(r["claim_fields"].split(MULTI)), "cards": set(r["cards"].split(MULTI))}
           for r in fails}
    out_csv = HERE / f"t1_retry_{tag}.csv"
    res = run_probe([r["url"] for r in fails], pop, out_csv)
    first = {r["url"]: r["t0_class"] for r in fails}
    trans = Counter((first[r["url"]], r["t0_class"]) for r in res)
    recovered = sum(v for (a, b), v in trans.items() if b == "reachable")
    summ = {"tag": tag, "retried": len(res), "recovered_reachable": recovered,
            "persistent_failures": len(res) - recovered,
            "transitions": {f"{a}->{b}": v for (a, b), v in sorted(trans.items())},
            "note": "recovered = transient failure at first probe; headline T1 numbers stay as first probe"}
    (HERE / f"t1_retry_{tag}.json").write_text(json.dumps(summ, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summ, indent=2))


# ---------------------------------------------------------------------------
def main():
    global WORKERS
    global DEPOSIT, PROJECTS
    ap = argparse.ArgumentParser(description="Link-reachability re-audit (T1)")
    ap.add_argument("--deposit", type=Path, help="project_cards.json whose evidence URLs form the population")
    ap.add_argument("--cards", type=Path, help="directory of project-card markdown files (adds links_* URLs)")
    ap.add_argument("--limit", type=int, default=0, help="probe a random subset of N URLs (dry run)")
    ap.add_argument("--tag", default=None, help="file tag (default: today's date)")
    ap.add_argument("--only-tier1", action="store_true")
    ap.add_argument("--retry", type=Path, help="re-probe non-reachable rows of a previous CSV")
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--force", action="store_true", help="overwrite an existing output CSV")
    a = ap.parse_args()
    tag = a.tag or date.today().isoformat()
    WORKERS = a.workers

    if a.retry:
        run_retry(a.retry, tag)
        return
    if not a.deposit:
        ap.error("--deposit is required unless --retry is given")
    DEPOSIT, PROJECTS = a.deposit, a.cards

    pop = load_population(only_tier1=a.only_tier1)
    urls = sorted(pop)
    n_t1 = sum("Tier-1" in p["tiers"] for p in pop.values())
    n_ev = sum("evidence" in p["kinds"] for p in pop.values())
    print(f"population: {len(urls)} unique URLs (evidence {n_ev}, of which Tier-1 {n_t1}; "
          f"links_* only {len(urls) - n_ev})")
    if a.limit:
        random.seed(20260905)
        gh = [u for u in urls if reg_domain(host_of(u)) == "github.com"]
        urls = random.sample(urls, min(a.limit, len(urls))) + random.sample(gh, min(6, len(gh)))
        print(f"dry run: {len(urls)} URLs (incl. 6 github.com for rate-limit check)")

    # Probe order: shuffled (fixed seed) so that concurrent workers hit different
    # hosts; a sorted list would queue all workers behind one per-domain lock.
    random.Random(20260905).shuffle(urls)
    out_csv = HERE / f"t1_probe_{tag}.csv"
    if out_csv.exists() and not a.force:
        sys.exit(f"ERROR: {out_csv.name} exists (another run may be writing to it); "
                 f"stop it and use --force to overwrite")
    t_start = time.monotonic()
    rows = run_probe(urls, pop, out_csv)
    summ = summarize(rows, tag)
    summ["elapsed_s"] = int(time.monotonic() - t_start)
    (HERE / f"t1_summary_{tag}.json").write_text(json.dumps(summ, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"all": summ["all"], "tier1": summ["tier1"], "elapsed_s": summ["elapsed_s"]}, indent=2))
    print(f"-> {out_csv.name}, t1_summary_{tag}.json")


if __name__ == "__main__":
    main()
