# Replication Package

**Evaluating Sparse and Dense AI Similarity Methods for Vocabulary Governance in Emerging-Domain Taxonomies: A Cross-Family Robustness Approach**

Nikita N. Kadochnikov  
Target journal: *Applied Soft Computing*

---

## Contents

```
replication_package/
├── README.md
├── LICENSE                        CC BY 4.0
├── requirements.txt               Python dependencies
├── data/
│   ├── tables/                    Aggregated tables (artifact 1)
│   │   ├── table_short_field_stats.csv
│   │   ├── evidence_by_freq_class.csv
│   │   ├── robustness_ai_component.csv
│   │   ├── robustness_use_case.csv
│   │   ├── robustness_opD.csv
│   │   ├── robustness_opE.csv
│   │   ├── clusters_ai_component.csv
│   │   ├── clusters_use_case.csv
│   │   └── stats.json             Full computed statistics
│   ├── similarity/                Pairwise similarity outputs (artifacts 2–3)
│   │   ├── pairs_{field}_{A,B,C,D,E}.csv
│   │   ├── heuristic_validation_ai_component.csv
│   │   └── heuristic_validation_use_case.csv
│   ├── annotations/               Annotation dataset (artifact 4)
│   │   ├── wave1_annotator_1.csv
│   │   ├── wave1_annotator_2.csv
│   │   ├── wave1_adjudicated.csv
│   │   ├── wave2_annotator_1.csv
│   │   ├── wave2_annotator_2.csv
│   │   └── wave2_adjudicated.csv
│   ├── movielens/                 Cross-domain replication (artifact 5)
│   │   ├── tags.csv               MovieLens Latest Small (CC BY 4.0)
│   │   └── movielens_robustness.csv
│   └── llm_validation_results.csv LLM zero-shot baseline (artifact 7)
├── scripts/                       Reproducibility code (artifact 6)
│   └── generate_figures.py
└── figures/                       Pre-generated figures (300 dpi)
    ├── fig1_pipeline.png
    ├── fig2_label_network.png
    ├── fig3_kg_edges.png
    ├── fig4_blurring_typology.png
    ├── fig5_fragmentation_regimes.png
    ├── fig6_cross_family_overlap.png
    ├── fig7_movielens_replication.png
    ├── fig_s1_mca.png
    ├── fig_s4_tsne.png
    └── fig_s5_rank_frequency.png
```

## Artifacts

The package provides seven artifact groups as described in the manuscript's Data Availability section:

| # | Artifact | Directory | Description |
|---|----------|-----------|-------------|
| 1 | Aggregated tables | `data/tables/` | All tables reported in the manuscript and supplementary materials in machine-readable CSV/JSON format |
| 2 | Normalized value vocabularies | `data/similarity/clusters_*.csv` | Deduplicated value lists for `ai_component` and `use_case` with frequency counts and frequency-class assignments (head/mid/tail) |
| 3 | Pairwise similarity outputs | `data/similarity/pairs_*.csv` | Top-50 neighbor pairs per operationalization (Ops A–C), top-100 for Ops D–E, for both fields, including cosine similarity scores and surface-consistency classifications |
| 4 | Annotation dataset | `data/annotations/` | Full annotation data for 196 pairs across two waves: pair identifiers, annotator labels (four-level scale), confidence ratings, adjudicated decisions, and stratum assignments |
| 5 | Cross-domain replication | `data/movielens/` | MovieLens tag vocabulary, pairwise similarity outputs, and within-family vs. cross-family overlap diagnostics. Source: MovieLens Latest Small (GroupLens, CC BY 4.0) |
| 6 | Reproducibility code | `scripts/` | Python script reproducing all figures from raw data or shared artifacts, with fixed random seeds (`seed = 42`) |
| 7 | LLM validation baseline | `data/llm_validation_results.csv` | Claude Opus 4.6 zero-shot synonym judgments on a stratified sample (n = 67 pairs across `cross_family_stable` and `negative_control` strata); used as an independent comparison anchor for the dense/sparse similarity methods |

## Data files

### `data/tables/`

| File | Manuscript reference |
|------|---------------------|
| `table_short_field_stats.csv` | Table 1 — Field-level statistics (N, missing share, unique values, frequency-class shares) |
| `evidence_by_freq_class.csv` | Supplementary — Evidence-quality interaction by frequency class |
| `robustness_ai_component.csv` | Table 5 — Within- vs. cross-family overlap at multiple k (ai_component) |
| `robustness_use_case.csv` | Table 5 — Within- vs. cross-family overlap at multiple k (use_case) |
| `robustness_opD.csv` | Robustness data including Op D (mpnet) |
| `robustness_opE.csv` | Robustness data including Op E (E5-large-v2) |
| `clusters_ai_component.csv` | Cluster assignments with frequency class (ai_component) |
| `clusters_use_case.csv` | Cluster assignments with frequency class (use_case) |
| `stats.json` | Full computed statistics (missingness, frequency classes, robustness, annotation metrics) |

### `data/similarity/`

| File | Description |
|------|-------------|
| `pairs_{field}_{op}.csv` | Top-50 most similar pairs for field × operationalization (top-100 for Ops D–E). Columns: `field`, `op`, `similarity`, `label_a`, `label_b`, `freq_a`, `freq_b` |
| `heuristic_validation_{field}.csv` | Surface-form heuristic validation: `label_a`, `label_b`, `sim`, `heuristic_class`, `op`, `field` |

### `data/annotations/`

Two-wave human annotation study (n = 196 pairs total, Cohen's κ = 0.844).

| File | Description |
|------|-------------|
| `wave1_annotator_1.csv` | Wave 1 — Annotator 1 labels |
| `wave1_annotator_2.csv` | Wave 1 — Annotator 2 labels |
| `wave1_adjudicated.csv` | Wave 1 — Adjudicated decisions (pair_id, field, value_a, value_b, stratum, ann1, ann2, adjudicated, is_synonym) |
| `wave2_annotator_1.csv` | Wave 2 — Annotator 1 labels |
| `wave2_annotator_2.csv` | Wave 2 — Annotator 2 labels |
| `wave2_adjudicated.csv` | Wave 2 — Adjudicated decisions |

### `data/movielens/`

| File | Description |
|------|-------------|
| `tags.csv` | MovieLens Latest Small tag assignments (GroupLens Research; see `LICENSE-MOVIELENS.txt`) |
| `movielens_robustness.csv` | Within- vs. cross-family overlap diagnostics for MovieLens tags (Ops A–E, N = 699 multi-word tags) |
| `LICENSE-MOVIELENS.txt` | Original GroupLens license (research use; redistribution under same terms; citation required) |

### `data/llm_validation_results.csv`

Stratified-sample LLM zero-shot baseline (n = 67 pairs sampled from the human-annotated set across two strata: `cross_family_stable` and `negative_control`). Used as an independent comparison anchor for the dense/sparse similarity methods reported in the manuscript.

| Column | Description |
|--------|-------------|
| `pair_id` | Pair identifier (consistent with `data/annotations/`) |
| `field` | `ai_component` or `use_case` |
| `value_a`, `value_b` | Vocabulary entries being compared |
| `stratum` | Sampling stratum (`cross_family_stable`, `negative_control`) |
| `human_is_synonym` | Adjudicated human label (binary) |
| `llm_answer` | Raw LLM response (`yes`/`no`) |
| `llm_is_synonym` | Binary mapping (`yes`→1, `no`→0) |

**LLM details:** Claude Opus 4.6 via Cursor IDE (Anthropic). Prompt: zero-shot binary synonym judgment on `value_a` vs. `value_b` within `field`. The LLM here is used as an experimental subject (independent baseline) and is methodologically distinct from the writing-assistance role described in the manuscript's "Declaration of generative AI" statement.

## Reproducing figures

### Prerequisites

```bash
pip install -r requirements.txt
```

### Without raw corpus (default)

Generates fig1 (schematic, no data) and fig7 (MovieLens replication from `data/movielens/tags.csv`). Pre-generated PNGs for all other figures are in `figures/`.

```bash
python scripts/generate_figures.py
```

### With raw corpus (full reproduction)

The underlying project-card corpus is subject to access restrictions. Researchers may contact the corresponding author (redice.surgut@gmail.com) for a data-use agreement.

```bash
python scripts/generate_figures.py \
    --corpus /path/to/project_cards.json \
    --passport /path/to/passport_fields.csv
```

The corpus and passport files are available from:
- **Zenodo deposit:** Kadochnikov NN (2026) *Project card schema and completeness diagnostics for AI–blockchain registries* [Data set]. DOI: [10.5281/zenodo.18900950](https://doi.org/10.5281/zenodo.18900950)

## Random seeds

All stochastic computations use `seed = 42` for reproducibility:
- `numpy.random.seed(42)`
- `random_state=42` for t-SNE, MCA, Louvain community detection, spring layout

## Citation

If you use this replication package, please cite the manuscript:

> Kadochnikov NN (2026) Evaluating Sparse and Dense AI Similarity Methods for Vocabulary Governance in Emerging-Domain Taxonomies: A Cross-Family Robustness Approach. *Applied Soft Computing*.

## License

This replication package is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), except for MovieLens data (`data/movielens/tags.csv`) which is redistributed under its original GroupLens license (research use only; see `data/movielens/LICENSE-MOVIELENS.txt`). Required citation for MovieLens data: Harper FM, Konstan JA (2015) The MovieLens Datasets: History and Context. ACM TiiS 5(4):19. https://doi.org/10.1145/2827872

