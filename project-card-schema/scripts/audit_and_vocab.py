#!/usr/bin/env python3
"""
Link-reachability audit and vocabulary coverage analysis for the
AI–Blockchain Project-Card corpus.

Reproduces the diagnostics reported in:
  G_data_paper.en.commonmark.md, Section 4 (Technical Validation)

Usage:
    python audit_and_vocab.py --projects-dir ../../projects \
                              --sample-size 150 --seed 42 --timeout 8

Outputs (stdout):
    - Vocabulary coverage for the `chain` field
    - Link-reachability audit results (HTTP HEAD/GET)

Requirements:
    Python 3.9+, requests
"""

import argparse
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("ERROR: 'requests' package is required. Install with: pip install requests")


# ---------------------------------------------------------------------------
# Canonical vocabulary for the `chain` field (Table 2a)
# ---------------------------------------------------------------------------
CANONICAL_CHAINS = {
    "Ethereum", "Solana", "Base", "BNB Chain", "Arbitrum",
    "Polygon", "Avalanche", "Sui", "Aptos", "Near",
    "Cosmos", "TON", "Fantom", "Optimism", "zkSync", "Bittensor", "other",
}

CHAIN_SYNONYMS = {
    "BNB Smart Chain": "BNB Chain",
    "Arbitrum One": "Arbitrum",
    "NEAR": "Near",
    "near": "Near",
}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
def extract_chain_value(text: str) -> str | None:
    """Extract the chain field value from a project-card markdown file."""
    patterns = [
        r"\|\s*(?:Основная сеть|chain)\s*\|\s*(.+?)\s*\|",
        r"\*\*(?:Основная сеть|chain)\*\*\s*[:：]\s*(.+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().strip("|").strip()
            if val and val != "—" and val != "-":
                return val
    return None


def extract_tier1_urls(text: str) -> list[str]:
    """Extract all Tier-1 source URLs from Evidence tables."""
    urls = []
    tier1_pattern = re.compile(
        r"\|\s*.*?\s*\|\s*(https?://[^\s|]+)\s*\|\s*(?:Tier[- ]?1|1)\s*\|",
        re.IGNORECASE,
    )
    for m in tier1_pattern.finditer(text):
        url = m.group(1).strip()
        if url:
            urls.append(url)
    return urls


# ---------------------------------------------------------------------------
# Vocabulary coverage analysis
# ---------------------------------------------------------------------------
def analyze_vocabulary(projects_dir: Path) -> None:
    """Compute vocabulary coverage for the chain field."""
    print("=" * 60)
    print("VOCABULARY COVERAGE ANALYSIS (chain field)")
    print("=" * 60)

    chain_values: list[str] = []

    for fpath in sorted(projects_dir.glob("*.md")):
        text = fpath.read_text(encoding="utf-8", errors="replace")
        val = extract_chain_value(text)
        if val:
            chain_values.append(val)

    total = len(chain_values)
    if total == 0:
        print("WARNING: No chain values found. Check --projects-dir path.")
        return

    canonical_count = 0
    synonym_count = 0
    novel_count = 0
    synonym_details: Counter = Counter()
    novel_details: Counter = Counter()

    for v in chain_values:
        if v in CANONICAL_CHAINS:
            canonical_count += 1
        elif v in CHAIN_SYNONYMS:
            synonym_count += 1
            synonym_details[f"'{v}' -> '{CHAIN_SYNONYMS[v]}'"] += 1
        else:
            novel_count += 1
            novel_details[v] += 1

    print(f"\nTotal chain values: {total}")
    print(f"Canonical (in-vocabulary): {canonical_count} ({canonical_count/total*100:.1f}%)")
    print(f"Synonyms (mappable):       {synonym_count} ({synonym_count/total*100:.1f}%)")
    for desc, n in synonym_details.most_common():
        print(f"  SYNONYM: {desc} (n={n})")
    print(f"Truly novel (OOV):         {novel_count} ({novel_count/total*100:.1f}%)")
    if novel_details:
        for val, n in novel_details.most_common(10):
            print(f"  OOV: '{val}' (n={n})")
        if len(novel_details) > 10:
            print(f"  ... and {len(novel_details) - 10} more unique OOV values")

    effective = canonical_count + synonym_count
    print(f"\nEffective coverage (canonical + synonym): {effective}/{total} ({effective/total*100:.1f}%)")


# ---------------------------------------------------------------------------
# Link-reachability audit
# ---------------------------------------------------------------------------
def audit_links(projects_dir: Path, sample_size: int, seed: int, timeout: int) -> None:
    """Sample Tier-1 URLs and test HTTP reachability."""
    print("\n" + "=" * 60)
    print("LINK-REACHABILITY AUDIT (Tier-1 URLs)")
    print("=" * 60)

    all_urls: set[str] = set()

    for fpath in sorted(projects_dir.glob("*.md")):
        text = fpath.read_text(encoding="utf-8", errors="replace")
        urls = extract_tier1_urls(text)
        all_urls.update(urls)

    print(f"\nTotal unique Tier-1 URLs extracted: {len(all_urls)}")

    url_list = sorted(all_urls)
    random.seed(seed)
    sample = random.sample(url_list, min(sample_size, len(url_list)))
    actual_sample = len(sample)

    print(f"Sampling {actual_sample} unique Tier-1 URLs for reachability test (seed={seed})...\n")

    reachable = 0  # 2xx, 3xx, 403
    http_404 = 0
    other_error = 0
    timeouts = 0
    domain_stats: Counter = Counter()
    domain_reachable: Counter = Counter()

    headers = {"User-Agent": "DecAIHub-Audit/1.0 (research; link-reachability check)"}

    for i, url in enumerate(sample, 1):
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        try:
            resp = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
            if resp.status_code == 405:
                resp = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True, stream=True)

            domain_stats[domain] += 1
            if resp.status_code in range(200, 400) or resp.status_code == 403:
                reachable += 1
                domain_reachable[domain] += 1
            elif resp.status_code == 404:
                http_404 += 1
            else:
                other_error += 1
        except requests.exceptions.Timeout:
            timeouts += 1
            domain_stats[domain] += 1
        except requests.exceptions.RequestException:
            other_error += 1
            domain_stats[domain] += 1

        if i % 25 == 0:
            print(f"  Checked {i}/{actual_sample}...")

    print(f"\n--- RESULTS ({actual_sample} URLs) ---")
    print(f"Reachable (2xx/3xx/403): {reachable}/{actual_sample} ({reachable/actual_sample*100:.1f}%)")
    print(f"HTTP 404 (link rot):     {http_404}/{actual_sample} ({http_404/actual_sample*100:.1f}%)")
    print(f"Other HTTP errors:       {other_error}/{actual_sample} ({other_error/actual_sample*100:.1f}%)")
    print(f"Timeouts:                {timeouts}/{actual_sample} ({timeouts/actual_sample*100:.1f}%)")

    print("\n--- DOMAIN BREAKDOWN (top domains by sample count) ---")
    for domain, count in domain_stats.most_common(15):
        reached = domain_reachable.get(domain, 0)
        print(f"  {domain}: {reached}/{count} reachable")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Link-reachability audit and vocabulary coverage for AI-Blockchain corpus"
    )
    parser.add_argument(
        "--projects-dir", type=Path,
        default=Path(__file__).resolve().parent.parent.parent.parent / "projects",
        help="Path to docs/projects/ directory containing project-card .md files",
    )
    parser.add_argument("--sample-size", type=int, default=150,
                        help="Number of Tier-1 URLs to sample for reachability test")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducible sampling")
    parser.add_argument("--timeout", type=int, default=8,
                        help="HTTP request timeout in seconds")
    parser.add_argument("--skip-audit", action="store_true",
                        help="Skip link-reachability audit (run vocab analysis only)")

    args = parser.parse_args()

    if not args.projects_dir.is_dir():
        sys.exit(f"ERROR: Projects directory not found: {args.projects_dir}")

    analyze_vocabulary(args.projects_dir)

    if not args.skip_audit:
        audit_links(args.projects_dir, args.sample_size, args.seed, args.timeout)

    print("\nDone.")


if __name__ == "__main__":
    main()
