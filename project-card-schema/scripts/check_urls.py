"""Check evidence-URL formatting quality (hygiene) in the dataset."""

import json, os, sys, re

sys.stdout.reconfigure(encoding="utf-8")

# Path to the Zenodo dataset (project_cards.json), DOI 10.5281/zenodo.18900950.
# Pass it as argv[1], set the PROJECT_CARDS env var, or place project_cards.json
# in the working directory.
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROJECT_CARDS", "project_cards.json")

with open(DATA, "r", encoding="utf-8") as f:
    cards = json.load(f)

backtick = []
mdlink = []
noproto = []
shorturl = []
backslash = []

for c in cards:
    for e in c["evidence"]:
        url = e["source_url"]
        pid = c["project_id"]
        tier = e["tier"]
        if "`" in url:
            backtick.append((pid, tier, url))
        if url.startswith("["):
            mdlink.append((pid, tier, url[:100]))
        if not url.startswith("http") and not url.startswith("["):
            noproto.append((pid, tier, url))
        if len(url) < 10:
            shorturl.append((pid, tier, url))
        if "\\" in url:
            backslash.append((pid, tier, url))

for label, lst in [("Backtick", backtick), ("MD link", mdlink),
                     ("No protocol", noproto), ("Short (<10)", shorturl),
                     ("Backslash", backslash)]:
    print(f"\n{label}: {len(lst)}")
    for pid, tier, url in lst[:8]:
        print(f"  [{tier}] {pid}: {url}")

# Tier-1 entries with problematic URLs
print(f"\n=== Tier-1 with issues ===")
bad_t1 = [x for lst in [backtick, mdlink, noproto, shorturl, backslash] for x in lst if x[1] == "Tier-1"]
print(f"Total Tier-1 with any issue: {len(bad_t1)}")
for pid, tier, url in bad_t1[:15]:
    print(f"  {pid}: {url}")

# Count Tier-1 entries with clean http URLs only
clean_t1 = 0
for c in cards:
    for e in c["evidence"]:
        if e["tier"] == "Tier-1" and e["source_url"].startswith("http") and "`" not in e["source_url"] and "\\" not in e["source_url"]:
            clean_t1 += 1
print(f"\nClean Tier-1 (http, no backtick, no backslash): {clean_t1}")

total_t1 = sum(1 for c in cards for e in c["evidence"] if e["tier"] == "Tier-1")
print(f"Total Tier-1: {total_t1}")
