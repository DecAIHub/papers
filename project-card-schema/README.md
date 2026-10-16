# ABPC — AI–Blockchain Project-Card Dataset: replication package

Replication code for:

> Kadochnikov, N. N. (2026). *Descriptor: AI–Blockchain Project-Card Dataset (ABPC).* IEEE Data Descriptions, 1–13. https://doi.org/10.1109/IEEEDATA.2026.3740408.

Dataset: Zenodo, concept DOI **10.5281/zenodo.18900949** (v1.1.0 = 10.5281/zenodo.22800707; v1.0.0 = 10.5281/zenodo.18900950), CC BY 4.0.

This package accompanies dataset v1.1.0. The package released with v1.0.0 is preserved in the repository history: [commit ed69f9f](https://github.com/DecAIHub/papers/tree/ed69f9f000669a7a701d86ec0f1dfe9cac2b6a4e/project-card-schema).

## Layout

| Path | Purpose |
|---|---|
| `schema/project_card.schema.json` | JSON Schema (draft 2020-12), version 1.1.0 |
| `scripts/extract_cards.py` | Parse the curated project cards (markdown) into an intermediate JSON |
| `scripts/vocab.py` | Controlled vocabularies of Category, chain, type, token_type; derivation of `ai_component_status` |
| `scripts/build_mapping_tables.py` | Write the per-value mapping tables (`mapping_*.csv`) |
| `scripts/wayback_lookup.py` | Internet Archive capture closest to 2026-03-05 for every evidence URL |
| `scripts/build_deposit.py` | Assemble `project_cards.json`, `cards/`, derive `claim_field`, attach archived copies |
| `scripts/validate.py` | Validate every record against the schema (exit code 1 on any violation) |
| `scripts/package_deposit.py` | README (with known issues and change log), mapping table, `cards.zip` |
| `scripts/compute_stats.py` | All statistics, tables and figures of the descriptor from `project_cards.json` |
| `scripts/case_study.py` | Reproducible downstream example (seed 42) |
| `scripts/irr_passport_agreement.py` | Agreement between the independent coder and the curator on the passport fields |
| `scripts/claim_support_audit.py` | Claim-support audit: summary of the coder's verdicts on 150 evidence entries |
| `scripts/persistence_audit_summary.py` | Persistence audit T1: summary of the per-URL log |
| `irr/sample.json` | Sample definition (seed 20260824): 50 cards (passport coding) and 150 evidence entries (claim-support audit) |
| `irr/coder_tool.html` | Coding tool shown to the coder (value definitions, links, evidence entries; card excerpts omitted) |
| `irr/irr_results_task1.json`, `irr/irr_results_task2.json` | Anonymized coder responses (passport fields; claim support) |
| `irr/mapping_sample50_to_table7.csv` | Curator-approved mapping of the sampled cards' descriptors onto the coder's value lists |
| `irr/source_status_at_coding_2026-09-05.csv` | State of each sampled card's sources at coding time (live-same / partial / live-changed) |
| `irr/pilot_2026-02/` | Claim-intensity pilot (February 2026): protocol given to the coder (`README_TASK.md`), the coder's sheet (`coding_sheet.csv`: tiers of the cited artifacts and 13 flags for 50 cards), the curator's reference coding (`ground_truth.csv`) and the computation script (`compute_irr.py`) |
| `audit/link_audit_t1.py` | Persistence audit probe (HEAD, 8 s timeout, GET on 405; retry pass) |
| `audit/t1_probe_2026-09-05.csv`, `audit/t1_retry_2026-09-05.csv` | Per-URL log of the 2026-09-05 run (10,219 URLs) and of the retry pass |

## Reproduce from the deposit (no access to the source cards needed)

```bash
pip install -r requirements.txt
python scripts/validate.py project_cards.json schema/project_card.schema.json
python scripts/compute_stats.py project_cards.json out/stats
python scripts/case_study.py project_cards.json out/case_study.json
python scripts/irr_passport_agreement.py irr/irr_results_task1.json project_cards.json out/irr.json --sample-map irr/mapping_sample50_to_table7.csv --strata irr/source_status_at_coding_2026-09-05.csv
python scripts/claim_support_audit.py irr/sample.json irr/irr_results_task2.json out/claim_support.json --probe audit/t1_probe_2026-09-05.csv
python scripts/persistence_audit_summary.py project_cards.json audit/t1_probe_2026-09-05.csv audit/t1_retry_2026-09-05.csv out/t1_audit.json
python irr/pilot_2026-02/compute_irr.py irr/pilot_2026-02/coding_sheet.csv
```

`compute_stats.py` writes `stats.json` (every corpus statistic reported in the article) and the four figures; the
remaining scripts reproduce the inter-rater, claim-support and persistence figures (`compute_irr.py` writes
`irr_report.md` next to itself).

## Rebuild the deposit from the source cards (curator only; cards are not redistributed)

```bash
python scripts/extract_cards.py <cards_dir> build/cards_raw.json
python scripts/build_mapping_tables.py build/cards_raw.json build/mapping
python scripts/wayback_lookup.py build/cards_raw.json build/archive_map.json --workers 4
python scripts/build_deposit.py build/cards_raw.json deposit --archive build/archive_map.json
python scripts/validate.py deposit/project_cards.json deposit/project_card.schema.json
python scripts/package_deposit.py deposit build/mapping
```

The pipeline is deterministic; re-running it on the February 2026 cards reproduces the deposit.

## Language

The source cards are written in Russian; everything released here is English. The parsers (`extract_cards.py`,
`link_audit_t1.py`) contain the Russian headings and keys of the card template, `build_deposit.py` the Russian stems
matched in the curator's source notes, and `vocab.py` the table that renders the 98 exported values carrying Russian
annotations in English. In the pilot materials the protocol is an English rendering of the Russian original given to the
coder and the coder's six notes are translated; in the audit logs, operating-system error messages are rendered in
English.

## Requirements

Python 3.11 or newer (run with 3.13); package versions pinned in `requirements.txt`.

## License

MIT (code). Dataset: CC BY 4.0.
