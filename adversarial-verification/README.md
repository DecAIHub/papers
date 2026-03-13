# Paper: Manipulation-Resistant Verification in Trust-Critical Digital Registries

Public replication package for:

> Kadochnikov, N.N. (2026). *Manipulation-Resistant Verification in Trust-Critical Digital Registries: Adversarial Framework with Protocol Validation and Boundary Diagnostics.* The Journal of Strategic Information Systems

## Contents

```text
├── figures/                        ← generated figure files used in the manuscript
├── scripts/
│   ├── generate_figures.py         ← main-text figures (Fig. 1–5)
│   └── compute_review_fixes.py     ← supplementary analyses, Fig. S2–S3
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

The analyses in this paper use an earlier snapshot of the underlying registry. A later public release of the related AI-Blockchain Project-Card Dataset is available on Zenodo (DOI: 10.5281/zenodo.18900950). This public GitHub repository contains the figure-generation scripts and generated figure assets only. Review-stage annotation matrices (k = 3 × n = 60 × 4 flags, baseline + intervention) and the algorithmic re-classification rule set are not included in the public repository and can be shared for peer review or upon reasonable request, subject to applicable platform terms.







