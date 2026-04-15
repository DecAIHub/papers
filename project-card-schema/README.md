# Project-Card Schema and Completeness Diagnostics

Replication package for:

> Kadochnikov, N. N. (2026). A Project-Card Schema and Completeness Diagnostics for AI–Blockchain Registries. *Scientific Data* (submitted).

## Dataset

The dataset (845 project cards + JSON Schema) is deposited at Zenodo:
https://doi.org/10.5281/zenodo.18900950

## Contents

| File | Description |
|------|-------------|
| `scripts/audit_and_vocab.py` | Link-reachability audit and vocabulary-coverage analysis (deterministic with `--seed 42`) |
| `scripts/extract_zenodo.py` | Extraction pipeline for project-card records |
| `scripts/verify_tables.py` | Verification of all tables reported in the paper |
| `scripts/verify_stats.py` | Verification of descriptive statistics |
| `scripts/regenerate_figures.py` | Regeneration of Figures 2–4 |
| `figures/` | Publication-quality figures (300 dpi PNG) |

## Requirements

- Python 3.9+
- Dependencies: `pandas`, `numpy`, `matplotlib`, `requests`

## Reproduction

```bash
pip install pandas numpy matplotlib requests
python scripts/audit_and_vocab.py --projects-dir <path-to-project-cards>
python scripts/regenerate_figures.py
```

## License

MIT
