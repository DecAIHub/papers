# Project-Card Schema and Completeness Diagnostics

Replication package for:

> Kadochnikov, N. N. (2026). *A Project-Card Schema and Completeness Diagnostics for AI–Blockchain Registries.*

## Dataset

The dataset — 845 AI–blockchain project cards, the JSON Schema, and the data dictionary — is deposited at Zenodo under a CC-BY 4.0 license:

**https://doi.org/10.5281/zenodo.18900950**

The analysis and verification scripts in this repository operate on `project_cards.json` from that deposit (see [Data location](#data-location)).

## Repository contents

### Scripts that run on the published dataset (`project_cards.json`)

| Script | Purpose |
|--------|---------|
| `scripts/verify_stats.py` | Reproduce the descriptive statistics reported in the paper |
| `scripts/verify_tables.py` | Reproduce Tables 5 and 7 |
| `scripts/verify_table5_detail.py` | Detailed Table 5 overlap computation, incl. tie-break sensitivity |
| `scripts/tier_count.py` | Evidence tier distribution (Tier-1/2/3) and unique Tier-1 URL count |
| `scripts/check_urls.py` | Evidence-URL formatting / hygiene checks |
| `scripts/check_synthetic.py` | Verify absence of synthetic fallback Tier-1 evidence; tier distribution |
| `scripts/regenerate_figures.py` | Regenerate Figures 3 and 4 from the dataset |
| `scripts/fix_cyrillic.py` | Dataset-preparation step: normalize residual non-English category values |

### Scripts that document the upstream extraction

These read the curated source registry (project-card markdown). The raw source is **not redistributed** here; the curated output is the published Zenodo dataset. They are included for transparency of the processing pipeline.

| Script | Purpose |
|--------|---------|
| `scripts/extract_zenodo.py` | Extraction pipeline: project-card markdown → `project_cards.json` + per-card JSON + schema |
| `scripts/audit_and_vocab.py` | Link-reachability audit (sampled HTTP checks) and chain-vocabulary coverage (`--projects-dir`, deterministic with `--seed 42`) |

### Other contents

| Path | Description |
|------|-------------|
| `figures/` | Publication-quality figures (PNG) |
| `requirements.txt` | Python dependencies (minimum compatible versions) |
| `LICENSE` | MIT |

## Processing & analysis pipeline

1. **Extraction** (`extract_zenodo.py`) — parse the curated project-card registry into a schema-conforming corpus: `project_cards.json`, one JSON per card, and the JSON Schema.
2. **Normalization** (`fix_cyrillic.py`) — normalize residual non-English values in the controlled passport fields.
3. **Tier accounting** (`tier_count.py`) — tally the Tier-1/2/3 evidence distribution and unique Tier-1 URLs.
4. **Quality control** (`check_urls.py`, `check_synthetic.py`) — evidence-URL formatting hygiene and confirmation that no synthetic fallback Tier-1 entries remain.
5. **Link & vocabulary audit** (`audit_and_vocab.py`) — sampled HTTP reachability of Tier-1 sources and chain-vocabulary coverage.
6. **Verification** (`verify_stats.py`, `verify_tables.py`, `verify_table5_detail.py`) — recompute the statistics and tables reported in the manuscript.
7. **Figures** (`regenerate_figures.py`) — regenerate Figures 3 and 4.

## Requirements

- Python 3.9 or newer
- `numpy`, `matplotlib`, `requests` (see `requirements.txt`)

```bash
pip install -r requirements.txt
```

## Data location

The repository does not bundle the dataset. Each dataset-consuming script locates `project_cards.json` in this order:

1. first command-line argument — `python scripts/tier_count.py /path/to/project_cards.json`
2. the `PROJECT_CARDS` environment variable
3. `project_cards.json` in the current working directory (default)

(`fix_cyrillic.py` takes the dataset *directory* — via `argv[1]` or `DATA_DIR` — since it also rewrites the per-card files.)

## Reproduction

```bash
pip install -r requirements.txt

# Download project_cards.json from the Zenodo deposit (DOI 10.5281/zenodo.18900950),
# then point the scripts at it:
export PROJECT_CARDS=/path/to/project_cards.json     # Windows: set PROJECT_CARDS=...

python scripts/verify_stats.py
python scripts/verify_tables.py
python scripts/tier_count.py
python scripts/check_urls.py
python scripts/check_synthetic.py
python scripts/regenerate_figures.py
```

## Reproducibility scope

All diagnostics, verification, and figure scripts reproduce directly from the published `project_cards.json`. The extraction and chain-vocabulary scripts (`extract_zenodo.py`, `audit_and_vocab.py`) document the upstream step from the curated source registry, whose raw markdown is not redistributed; the curated result is the Zenodo dataset itself.

## License

MIT — see `LICENSE`.
