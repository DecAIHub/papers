"""
Look up, for every evidence URL, the Internet Archive capture closest to the
corpus verification date (2026-03-05) using the Wayback availability API.

Usage: python wayback_lookup.py <cards_raw.json | project_cards.json> <out_json> [--workers 4]
Output: {url: {"archive_url": ..., "timestamp": ..., "delta_days": ...} | null}
The script is resumable: existing entries in <out_json> are kept.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

TARGET = "20260305"
API = "https://archive.org/wayback/available?url={url}&timestamp={ts}"


def lookup(url, session, retries=3):
    for attempt in range(retries):
        try:
            r = session.get(API.format(url=quote(url, safe=""), ts=TARGET), timeout=30)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            snap = r.json().get("archived_snapshots", {}).get("closest")
            if not snap or not snap.get("available"):
                return None
            ts = snap["timestamp"]
            d = datetime.strptime(ts[:8], "%Y%m%d") - datetime.strptime(TARGET, "%Y%m%d")
            return {"archive_url": snap["url"], "timestamp": ts, "delta_days": d.days}
        except Exception:
            time.sleep(2 * (attempt + 1))
    return {"error": "lookup_failed"}


def main():
    src = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2])
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    urls = []
    for c in src:
        for e in c["evidence"]:
            u = e["source_url"]
            if u not in urls:
                urls.append(u)
    done = json.load(open(out, encoding="utf-8")) if out.exists() else {}
    todo = [u for u in urls if u not in done or (done[u] and done[u].get("error"))]
    print(f"unique urls: {len(urls)}; to look up: {len(todo)}")
    session = requests.Session()
    session.headers["User-Agent"] = "ABPC-dataset-archive-lookup/1.1"
    n = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(lookup, u, session): u for u in todo}
        for f in as_completed(futs):
            done[futs[f]] = f.result()
            n += 1
            if n % 100 == 0:
                out.write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8")
                print(f"{n}/{len(todo)}", flush=True)
    out.write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for v in done.values() if v and not v.get("error"))
    err = sum(1 for v in done.values() if v and v.get("error"))
    print(f"done: {len(done)}; archived: {ok}; none: {len(done) - ok - err}; errors: {err}")


if __name__ == "__main__":
    main()
