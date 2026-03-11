# Paper: Manipulation-Resistant Verification under Heterogeneous Evidence

Replication package for:

> Kadochnikov, N.N. (2026). *Manipulation-Resistant Verification under Heterogeneous Evidence: Adversarial Framework with Protocol Validation and Boundary Diagnostics.* Computers & Security (submitted).

## Contents

```
├── scripts/
│   ├── generate_figures.py        ← main-text figures (Fig. 1–5)
│   └── compute_review_fixes.py    ← supplementary analyses, Fig. S2–S3
├── figures/                        ← all generated figures (300 dpi PNG)
├── data/                           ← annotation matrices (review-stage / on request)
├── requirements.txt
└── LICENSE                         ← CC BY 4.0
```

## Quick Start

```bash
pip install -r requirements.txt
cd scripts
python generate_figures.py
python compute_review_fixes.py
```

## Data Availability

The analyses in this paper use an earlier snapshot of the underlying registry. A later public release of the related AI-Blockchain Project-Card Dataset is available on Zenodo (DOI: 10.5281/zenodo.18900950). Annotation matrices (k=3 × n=60 × 4 flags, baseline + intervention) and the algorithmic re-classification rule set can be shared for review or upon reasonable request, subject to applicable platform terms.




