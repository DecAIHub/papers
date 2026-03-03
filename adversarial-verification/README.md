# Paper C: Manipulation-Resistant Verification under Heterogeneous Evidence

Replication package for:

> Kadochnikov, N.N. (2026). *Manipulation-Resistant Verification under Heterogeneous Evidence: Adversarial Framework with Protocol Validation and Boundary Diagnostics.* Blockchain: Research and Applications.

## Contents

```
├── scripts/
│   ├── generate_figures.py        ← main-text figures (Fig. 1–5)
│   └── compute_review_fixes.py    ← supplementary analyses, Fig. S2–S3
├── figures/                        ← all generated figures (300 dpi PNG)
├── data/                           ← annotation matrices (deposited upon acceptance)
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

Annotation matrices (k=3 × n=60 × 4 flags, baseline + intervention) and the algorithmic re-classification rule set will be deposited on Zenodo upon acceptance.
