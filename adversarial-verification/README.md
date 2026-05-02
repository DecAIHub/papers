# Paper: Manipulation-Resistant Verification in Trust-Critical Digital Registries

Public replication package for:

> Kadochnikov, N.N. (2026). *Manipulation-Resistant Verification in Trust-Critical Digital Registries: Adversarial Framework with Protocol Validation and Boundary Diagnostics.* Manuscript submitted to *Computer Standards & Interfaces*.

## Contents

```text
├── figures/                            ← generated figure files used in the manuscript
├── scripts/
│   ├── generate_figures.py             ← main-text figures (Fig. 1–5)
│   ├── generate_fig_s1.py              ← supplementary figure S1 (corpus tier composition)
│   ├── compute_review_fixes.py         ← supplementary analyses, Fig. S2–S3
│   └── iaa_pilot/
│       ├── compute_tost.py             ← TOST equivalence analysis (§3.3.2)
│       ├── README.md                   ← data-availability notes for IAA / TOST
│       └── results/
│           └── tost_equivalence.json   ← precomputed TOST output
├── requirements.txt
└── LICENSE                             ← CC BY 4.0
```

## Quick Start

Reproduce the five main-text figures out of the box:

```bash
pip install -r requirements.txt
cd scripts
python generate_figures.py
```

Output: `figures/fig1_pipeline.png` … `fig5_boundary_typology.png`.

The remaining scripts require raw inputs that are **not** bundled with this repository (see *Data Availability* below). If those inputs are placed in the default locations, the following will regenerate the supplementary figures and the TOST table:

```bash
python generate_fig_s1.py            # Fig. S1 — needs corpus cache (DECAIHUB_CORPUS_CACHE)
python compute_review_fixes.py       # Fig. S2, S3 — needs raw annotator JSONs (DECAIHUB_IAA_DIR)
python iaa_pilot/compute_tost.py     # TOST equivalence table — needs raw annotator JSONs
```

All three scripts honour environment-variable overrides (`DECAIHUB_CORPUS_CACHE` for the corpus cache, `DECAIHUB_IAA_DIR` for the raw annotator JSONs) and fall back to `scripts/corpus/` and `scripts/iaa_pilot/results/` respectively. If the raw inputs are missing, each script prints a pointer to this README instead of failing silently.

## Data Availability

The analyses in this paper use an earlier snapshot of the underlying registry. A later public release of the related AI-Blockchain Project-Card Dataset is available on Zenodo (DOI: 10.5281/zenodo.18900950). This public GitHub repository contains the figure-generation scripts and generated figure assets only. Review-stage annotation matrices (k = 3 × n = 60 × 4 flags, baseline + intervention), the corpus tier-composition cache used for Fig. S1, and the algorithmic re-classification rule set are not included in the public repository and can be shared for peer review or upon reasonable request, subject to applicable platform terms.







