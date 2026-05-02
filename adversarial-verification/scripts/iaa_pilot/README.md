# IAA Pilot — Equivalence Analysis (TOST)

This directory hosts the pre-specified TOST equivalence analysis
reported in Section 3.3.2 and Table 7b of the manuscript.

## Files

- `compute_tost.py`
  Paired TOST (Schuirmann, 1987) on the three-way exact-agreement
  indicator per profile, McNemar-style variance for correlated
  proportions. Pure Python (stdlib only — no SciPy).

- `results/tost_equivalence.json`
  Reference output for all 4 flags × 2 Δ margins (Δ=0.10 primary,
  Δ=0.15 sensitivity). Produced by `compute_tost.py` from the raw
  per-annotator JSONs (not redistributed — see below). Included so
  reviewers can cross-check numbers against Table 7b without having
  to obtain the raw data.

## Data availability

The per-annotator raw files

```
annotator1_baseline.json
annotator1_intervention.json
annotator2_baseline.json
annotator2_intervention.json
annotator3_baseline.json
annotator3_intervention.json
```

are **not** included in this public replication package. They contain
per-profile labels produced by three external annotators during the
inter-annotator reliability study and are governed by the platform
terms under which the underlying AI-Blockchain corpus was compiled.

They can be shared for peer review or upon reasonable request. Once
you have them, drop the six files into `scripts/iaa_pilot/results/`
alongside `tost_equivalence.json`, or point the env var
`DECAIHUB_IAA_DIR` to the directory that contains them.

## Reproducing Table 7b

From the repository root:

```bash
cd scripts/iaa_pilot
python compute_tost.py
```

Expected console output (four flags, each at Δ=0.10 and Δ=0.15,
matching Table 7b of the manuscript):

- AI_2 — equivalent at Δ=0.10 and Δ=0.15
- OC_2 — equivalent at Δ=0.10 and Δ=0.15
- TK_1 — inconclusive at Δ=0.10, equivalent at Δ=0.15
- OC_3 — inconclusive at both margins (expected; this is the primary
  endpoint, reported for reference only; see Table 7a for its
  null-hypothesis test result: +21.7 pp, p = 0.028)

`compute_tost.py` overwrites `results/tost_equivalence.json` with the
freshly computed numbers. Diff against the shipped reference copy to
confirm bit-for-bit reproducibility.

## Hypotheses tested

For each exploratory flag (AI_2, OC_2, TK_1):

```
H01: Δ_EA ≤ −Δ      (substantial decrease)
H02: Δ_EA ≥ +Δ      (substantial increase)
```

Rejecting **both** at one-sided α = 0.05 establishes equivalence
within ±Δ of the null. OC_3 is reported for reference but is not
expected to satisfy equivalence — its pre-specified primary test is
McNemar's Δ_EA ≠ 0 (see `compute_review_fixes.py` for the primary
analysis).

## References

- Schuirmann, D. J. (1987). A comparison of the two one-sided tests
  procedure and the power approach for assessing the equivalence of
  average bioavailability. *Journal of Pharmacokinetics and
  Biopharmaceutics*, 15(6), 657–680.
  https://doi.org/10.1007/BF01068419
