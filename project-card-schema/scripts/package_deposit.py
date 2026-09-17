"""
Assemble the deposit: cards.zip, mapping_tables.csv and README.md
(the README carries the known issues and the change log).

Usage: python package_deposit.py <deposit_dir> <mapping_dir> [--build-dir build]
Final deposit = project_cards.json, cards.zip, project_card.schema.json, mapping_tables.csv, README.md.
CSV files are UTF-8 with BOM, comma-separated (RFC 4180).
"""
import csv
import json
import shutil
import sys
import zipfile
from pathlib import Path

dep = Path(sys.argv[1])
mapping_src = Path(sys.argv[2])
build_dir = Path(sys.argv[sys.argv.index("--build-dir") + 1]) if "--build-dir" in sys.argv else Path("build")
report = json.load(open(dep / "build_report.json", encoding="utf-8"))
N = report["records"]
# persistence audit T1 (persistence_audit_summary.py on the per-URL log released in the code repository)
t1_path = build_dir / "t1_audit.json"
T1 = json.load(open(t1_path, encoding="utf-8")) if t1_path.exists() else None
persistence = (f"\n- Source persistence, two audits: T0 = 2026-03-05 (verification date) — 89.3% of a 150-URL Tier-1 sample reachable; "
               f"T1 = {T1['date']} — {T1['Tier-1']['reachable_pct']}% of the {T1['Tier-1']['n']:,} Tier-1 URLs reachable, "
               f"{T1['deposit_tier1']['cards_with_unreachable_tier1']} cards with at least one unreachable Tier-1 URL (per-URL log and "
               f"script in the code repository, `audit/`); use `archive_url` for the state of a source at snapshot time") if T1 else ""

# one mapping table for all fields -----------------------------------------------------------------------------
rows = []
for name, field in [("mapping_Category.csv", "Category"), ("mapping_chain.csv", "chain"), ("mapping_type.csv", "type"),
                    ("mapping_token_type.csv", "token_type")]:
    with open(mapping_src / name, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = r.get("raw_value", r.get("raw_label"))
            rows.append([field, raw, r["n"], r["canonical"], r.get("mechanisms", "")])
with open(dep / "mapping_tables.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["field", "raw_value", "n_records", "canonical", "token_mechanisms"])
    w.writerows(rows)
if (dep / "mapping").exists():
    shutil.rmtree(dep / "mapping")

# cards.zip; the unpacked cards/ folder (written by build_deposit.py) is not part of the deposit ----------------
if (dep / "cards").exists():
    with zipfile.ZipFile(dep / "cards.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted((dep / "cards").glob("*.json")):
            z.write(f, f"cards/{f.name}")
    shutil.rmtree(dep / "cards")


(dep / "README.md").write_text(
f"""# AI–Blockchain Project-Card Dataset (ABPC) — v1.1.0

A curated snapshot (February 2026) of **{N} projects positioned as AI-related on blockchain infrastructure**: a passport
(canonical and raw metadata), links, and an evidence table linking claims to source artifacts by provenance tier.
Version 1.1.0 corrects the representation of the same snapshot released as 1.0.0.

## Contents

| File | Description |
|---|---|
| `project_cards.json` | All {N} records in a single JSON array |
| `cards.zip` | The same records as individual JSON files |
| `project_card.schema.json` | JSON Schema (draft 2020-12) with field descriptions; all records validate |
| `mapping_tables.csv` | Mapping from the curator's values to canonical values (Category, chain, type, token_type) |

CSV files: UTF-8 with BOM, comma-separated.

## Key statistics
- N = {N} records (27 stub records, `stub: true`)
- {report['evidence_entries']:,} evidence entries (Tier-1 {report['evidence_by_tier']['Tier-1']:,} / Tier-2 {report['evidence_by_tier']['Tier-2']} / Tier-3 {report['evidence_by_tier']['Tier-3']}); {report['unique_tier1_urls']:,} unique Tier-1 URLs; {report['evidence_gaps']} negative-evidence rows
- Null share: token_type {100*report['null_token_type']/N:.1f}%, ai_component {100*report['null_ai_component']/N:.1f}%, use_case {100*report['null_use_case']/N:.1f}%
- Dates: cards verified 3–11 February 2026 (`card_verified_date`); URL check 2026-03-05 (`verified_date`); Internet Archive copies closest to that date (`archive_url`){persistence}

## Known issues
- Duplicate listings: 404-effect-ai / 481-effect-ai-sol; 739-aimedis / 379-aimedis-new (merge for entity-level analyses).
- Claim-support audit residuals: 34-iotex and 723-murall (Tier-1, Category — cited page does not support the claim); 05-filecoin (Tier-1, ai_component — partially supported).
- `claim_field` is derived from the curator's source note by a keyword rule; treat it as an index, not a curated link.

## Changes since 1.0.0
Same snapshot; representation corrected, no value re-curated. Canonical + `*_raw` layer for Category, chain, type and token_type;
`ai_component` and `use_case` released as free text with `ai_component_status` (all records now validate); link fields restored; one evidence row per (URL, field) with `archive_url`; `evidence_gaps` added; header fields
`name`, `ticker`, `token_contract`, `stub`, `card_verified_date` and `launch_date` added; `Category` and `links.website` nullable;
residual Russian annotations in 98 free-text values rendered in English (table `ENGLISH_RENDERINGS` in `vocab.py`).

## License and citation
CC BY 4.0. Kadochnikov, N. N. (2026). Descriptor: AI–Blockchain Project-Card Dataset (ABPC). *IEEE Data Descriptions* (in revision).
Concept DOI 10.5281/zenodo.18900949. Code: https://github.com/DecAIHub/papers/tree/main/project-card-schema (MIT).
Contact: redice.surgut@gmail.com — ORCID 0009-0004-5996-7934
""", encoding="utf-8")

# the build report is a build artifact, not part of the deposit
build_dir.mkdir(exist_ok=True)
shutil.move(str(dep / "build_report.json"), str(build_dir / "build_report.json"))
for stale in ("known_issues.md", "CHANGELOG.md"):
    if (dep / stale).exists():
        (dep / stale).unlink()
print("deposit:", sorted(p.name for p in dep.iterdir()))
