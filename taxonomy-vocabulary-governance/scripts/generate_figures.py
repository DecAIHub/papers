"""
Replication package — Generate all figures for Article A (Taxonomy).

Usage:
    python scripts/generate_figures.py                        # pre-computed artifacts only (fig1, fig7)
    python scripts/generate_figures.py --corpus path/to/project_cards.json --passport path/to/passport_fields.csv

When --corpus and --passport are supplied, all 10 figures (7 main + 3 supplementary) are
generated from raw data. Without them, fig1 (schematic) is always produced, and fig7
(MovieLens replication) is produced from data/movielens/tags.csv.
Pre-generated PNGs for all figures are included in figures/ for reference.
"""

import argparse
import json
import re
import os
import warnings
import itertools
import textwrap
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

warnings.filterwarnings("ignore")
np.random.seed(42)

PKG_ROOT = Path(__file__).resolve().parent.parent
DATA = PKG_ROOT / "data"
FIGURES = PKG_ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

DPI = 300
FONT_SIZE = 9
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.titlesize": FONT_SIZE + 1,
    "axes.labelsize": FONT_SIZE,
    "xtick.labelsize": FONT_SIZE - 1,
    "ytick.labelsize": FONT_SIZE - 1,
    "legend.fontsize": FONT_SIZE - 1,
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "font.family": "serif",
})


# ---- Data loading ----

def load_corpus(corpus_path, passport_path):
    with open(corpus_path, encoding="utf-8") as f:
        cards = json.load(f)

    pf = pd.read_csv(passport_path)
    pf["slug"] = pf["file"].apply(
        lambda fp: re.sub(r"\.ru\.commonmark\.md$", "",
                          os.path.basename(fp)).replace("_", "-"))

    slug_to_info = {}
    for _, row in pf.iterrows():
        slug_to_info[row["slug"]] = {
            "category_labels": row["category_labels"] if pd.notna(row["category_labels"]) else "",
            "token_type": row["token_type"] if pd.notna(row["token_type"]) else "",
            "ai_component": row["ai_component"] if pd.notna(row["ai_component"]) else "",
            "use_case": row["use_case"] if pd.notna(row["use_case"]) else "",
            "chain": row["chain"] if pd.notna(row["chain"]) else "",
            "type": row["type"] if pd.notna(row["type"]) else "",
        }

    rows = []
    for c in cards:
        pid = c["project_id"]
        info = slug_to_info.get(pid, {})
        evs = c.get("evidence", [])
        total = len(evs)
        t1 = sum(1 for e in evs if e.get("tier") == "Tier-1")
        gap = 1 - (t1 / total) if total > 0 else 1.0
        rows.append({"slug": pid, "gap": gap, **info})

    proj = pd.DataFrame(rows)
    proj["labels_list"] = proj["category_labels"].apply(
        lambda x: [l.strip() for l in x.split(";") if l.strip()])
    return proj


# ---- Fig 1: Pipeline diagram (no data required) ----

def fig1_pipeline():
    fig, ax = plt.subplots(figsize=(10, 2.8))
    ax.set_xlim(-0.1, 10.2)
    ax.set_ylim(0, 3)
    ax.axis("off")

    boxes = [
        (0.2, 0.8, 1.8, 1.4, "Corpus\nN = 845\nproject cards\n6 fields", "#E8F4FD"),
        (2.4, 0.8, 2.2, 1.4,
         "Structural\nAnalysis (3.2)\n-----------\nCo-occurrence\nKG scaffold\nBlurring typology", "#FFF3E0"),
        (5.0, 0.8, 2.2, 1.4,
         "Semantic\nMapping (3.3)\n-----------\nFragmentation\nCross-family\nstability", "#E8F5E9"),
        (7.6, 0.8, 2.2, 1.4,
         "Validation (3.4)\n-----------\nHuman annotation\nCross-domain\n(MovieLens)", "#FFEBEE"),
    ]
    for x, y, w, h, txt, color in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor="#555", linewidth=1.2)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center",
                fontsize=9.0, family="serif")

    for x1, x2 in [(2.0, 2.4), (4.6, 5.0), (7.2, 7.6)]:
        ax.annotate("", xy=(x2, 1.5), xytext=(x1, 1.5),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))

    ax.text(5.1, 0.25,
            "RQ1: Structure  ->  RQ2: Semantics  ->  RQ3: Validation",
            ha="center", fontsize=10.2, fontstyle="italic", color="#333")

    fig.savefig(FIGURES / "fig1_pipeline.png", pad_inches=0.05)
    plt.close(fig)
    print("  OK: fig1_pipeline.png")


# ---- Fig 2: Label co-occurrence network ----

def fig2_label_network(proj):
    all_labels = []
    for ll in proj["labels_list"]:
        all_labels.extend(ll)
    label_counts = Counter(all_labels)
    top_labels = [l for l, _ in label_counts.most_common(15) if label_counts[l] >= 7]

    G = nx.Graph()
    for lbl in top_labels:
        G.add_node(lbl, count=label_counts[lbl])

    for _, row in proj.iterrows():
        ll = [l for l in row["labels_list"] if l in top_labels]
        for a, b in itertools.combinations(ll, 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)

    fig, ax = plt.subplots(figsize=(8, 7))
    pos = nx.spring_layout(G, k=2.5, seed=42, weight="weight")
    node_sizes = [G.nodes[n]["count"] * 4 for n in G.nodes()]

    communities = nx.community.louvain_communities(G, seed=42, resolution=1.0)
    node_colors = {}
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
               "#8c564b", "#e377c2", "#7f7f7f"]
    for i, comm in enumerate(communities):
        for node in comm:
            node_colors[node] = palette[i % len(palette)]
    colors = [node_colors.get(n, "#999") for n in G.nodes()]

    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [0.5 + 3.5 * w / max_w for w in edge_weights]

    nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths, alpha=0.4, edge_color="#888")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, node_color=colors,
                           alpha=0.8, edgecolors="#333", linewidths=0.8)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_family="serif")

    Q = nx.community.modularity(G, communities)
    ax.set_title(f"Label Co-occurrence Network (top-{len(top_labels)} labels, "
                 f"Louvain Q = {Q:.2f})", fontsize=10)
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(FIGURES / "fig2_label_network.png")
    plt.close(fig)
    print(f"  OK: fig2_label_network.png (Q={Q:.2f})")


# ---- Fig 3: Stable KG edges ----

def fig3_kg_edges(proj):
    edges = []
    for _, row in proj.iterrows():
        tt = row["token_type"]
        if not tt:
            continue
        for lbl in row["labels_list"]:
            edges.append((lbl, tt))

    edge_counts = Counter(edges)
    stable = {k: v for k, v in edge_counts.items() if v >= 10}

    if not stable:
        print("  SKIP: fig3_kg_edges.png (no stable edges)")
        return

    labels_in = set()
    tts_in = set()
    for (lbl, tt), cnt in stable.items():
        labels_in.add(lbl)
        tts_in.add(tt)

    G = nx.Graph()
    for lbl in labels_in:
        G.add_node(lbl, bipartite=0)
    for tt in tts_in:
        G.add_node(tt, bipartite=1)
    for (lbl, tt), cnt in stable.items():
        G.add_edge(lbl, tt, weight=cnt)

    n_labels = len(labels_in)
    n_tts = len(tts_in)
    fig_h = max(4, max(n_labels * 1.2, n_tts * 0.8) + 1.5)
    fig, ax = plt.subplots(figsize=(8, fig_h))

    pos = {}
    sorted_labels = sorted(labels_in)
    sorted_tts = sorted(tts_in, key=lambda x: -stable.get(
        (sorted_labels[0], x), 0) if sorted_labels else 0)
    for i, lbl in enumerate(sorted_labels):
        pos[lbl] = (0, -i * 1.2)
    for i, tt in enumerate(sorted_tts):
        pos[tt] = (4, -i * 0.8)

    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [0.8 + 4 * w / max_w for w in edge_weights]
    edge_alphas = [0.3 + 0.6 * w / max_w for w in edge_weights]

    for (u, v), w, a in zip(G.edges(), edge_widths, edge_alphas):
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                color="#2196F3", linewidth=w, alpha=a)

    for lbl in sorted_labels:
        ax.plot(pos[lbl][0], pos[lbl][1], "o", markersize=12,
                color="#FF7043", markeredgecolor="#333", markeredgewidth=0.8)
        ax.text(pos[lbl][0] - 0.15, pos[lbl][1], lbl,
                ha="right", va="center", fontsize=8, fontweight="bold")

    for tt in sorted_tts:
        ax.plot(pos[tt][0], pos[tt][1], "s", markersize=10,
                color="#66BB6A", markeredgecolor="#333", markeredgewidth=0.8)
        wrapped = "\n".join(textwrap.wrap(tt, width=38))
        ax.text(pos[tt][0] + 0.15, pos[tt][1], wrapped,
                ha="left", va="center", fontsize=8.4)

    for (u, v) in G.edges():
        mx = (pos[u][0] + pos[v][0]) / 2
        my = (pos[u][1] + pos[v][1]) / 2
        ax.text(mx, my + 0.12, str(G[u][v]["weight"]),
                ha="center", fontsize=6, color="#555")

    ax.set_title(f"Stable Category-token_type Edges (count >= 10; "
                 f"{len(stable)} edges)", fontsize=10)
    ax.axis("off")
    all_x = [p[0] for p in pos.values()]
    ax.set_xlim(min(all_x) - 1.8, max(all_x) + 3.2)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig3_kg_edges.png", pad_inches=0.05)
    plt.close(fig)
    print(f"  OK: fig3_kg_edges.png ({len(stable)} edges)")


# ---- Fig 4: Two-dimensional ambiguity typology ----

def fig4_blurring_typology(proj):
    expl = []
    for _, row in proj.iterrows():
        for lbl in row["labels_list"]:
            expl.append({"label": lbl, "n_labels": len(row["labels_list"])})
    expl_df = pd.DataFrame(expl)

    label_stats = expl_df.groupby("label").agg(
        count=("label", "size"),
        mixed_share=("n_labels", lambda x: (x > 1).mean()),
    )
    label_stats = label_stats[label_stats["count"] >= 20]

    entropy_data = []
    for lbl in label_stats.index:
        co_labels = []
        for _, row in proj.iterrows():
            if lbl in row["labels_list"]:
                for other in row["labels_list"]:
                    if other != lbl:
                        co_labels.append(other)
        if not co_labels:
            entropy_data.append(0)
            continue
        co_counts = Counter(co_labels)
        total = sum(co_counts.values())
        probs = [c / total for c in co_counts.values()]
        H = -sum(p * np.log2(p) for p in probs if p > 0)
        H_max = np.log2(len(co_counts)) if len(co_counts) > 1 else 1
        entropy_data.append(H / H_max if H_max > 0 else 0)

    label_stats["entropy_norm"] = entropy_data

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.axvline(0.80, color="#ccc", ls="--", lw=0.8)
    ax.axhline(0.60, color="#ccc", ls="--", lw=0.8)

    ax.fill_between([0.80, 1.02], 0, 0.60, alpha=0.06, color="#FF9800")
    ax.fill_between([0.80, 1.02], 0.60, 1.02, alpha=0.06, color="#4CAF50")
    ax.fill_between([0, 0.80], 0, 0.60, alpha=0.06, color="#9E9E9E")
    ax.fill_between([0, 0.80], 0.60, 1.02, alpha=0.06, color="#2196F3")

    ax.text(0.91, 0.05, "Concentrated", ha="center", fontsize=7.5,
            color="#E65100", fontstyle="italic")
    ax.text(0.91, 0.95, "Diffuse", ha="center", fontsize=7.5,
            color="#1B5E20", fontstyle="italic")
    ax.text(0.91, 0.55, "Scale-driven", ha="center", fontsize=7.5,
            color="#333", fontstyle="italic")
    ax.text(0.40, 0.95, "Residual-\ndiffuse", ha="center", fontsize=7.5,
            color="#0D47A1", fontstyle="italic")

    sizes = label_stats["count"].values
    size_scale = 30 + (sizes / sizes.max()) * 250

    ax.scatter(label_stats["mixed_share"], label_stats["entropy_norm"],
               s=size_scale, c="#2196F3", alpha=0.7, edgecolors="#1565C0",
               linewidths=1, zorder=5)

    for lbl, row in label_stats.iterrows():
        dx, dy = 0.01, 0.02
        if lbl == "Meme":
            dx = -0.02
            dy = -0.03
        elif lbl == "AI/Other":
            dy = -0.03
        ax.annotate(lbl, (row["mixed_share"] + dx, row["entropy_norm"] + dy),
                    fontsize=7, zorder=6)

    ax.set_xlabel("Mixed Share (fraction with 2+ labels)")
    ax.set_ylabel("Normalized Co-label Entropy")
    ax.set_title("Two-Dimensional Ambiguity Typology (labels with N >= 20)")
    ax.set_xlim(0.45, 1.02)
    ax.set_ylim(0.35, 0.90)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig4_blurring_typology.png")
    plt.close(fig)
    print("  OK: fig4_blurring_typology.png")


# ---- Fig 5: Fragmentation regimes ----

def fig5_fragmentation(proj):
    fields_data = {}
    for field in ["type", "chain", "token_type", "ai_component", "use_case"]:
        vals = proj[field][proj[field] != ""].tolist()
        if not vals:
            continue
        counts = Counter(vals)
        total = sum(counts.values())
        shares = [c / total for c in counts.values()]
        hhi = sum(s ** 2 for s in shares)
        n_unique = len(counts)
        singletons = sum(1 for c in counts.values() if c == 1)
        singleton_tail = singletons / n_unique if n_unique > 0 else 0
        fields_data[field] = {"HHI": hhi, "singleton_tail": singleton_tail}

    fig, ax = plt.subplots(figsize=(7, 5))
    colors_map = {
        "type": "#4CAF50", "chain": "#FF9800", "token_type": "#FF9800",
        "ai_component": "#F44336", "use_case": "#F44336",
    }
    markers_map = {
        "type": "D", "chain": "s", "token_type": "s",
        "ai_component": "o", "use_case": "o",
    }

    ax.axvspan(0.3, 0.7, alpha=0.05, color="#4CAF50")
    ax.axvspan(0.05, 0.3, alpha=0.05, color="#FF9800")
    ax.axvspan(0, 0.05, alpha=0.05, color="#F44336")

    ax.text(0.50, 0.02, "Regime A\n(controlled)", ha="center",
            fontsize=7.5, color="#2E7D32", fontstyle="italic")
    ax.text(0.15, 0.02, "Regime B\n(head-dominated)", ha="center",
            fontsize=7.5, color="#E65100", fontstyle="italic")
    ax.text(0.02, 0.50, "Regime C\n(near-\nuncontrolled)", ha="center",
            fontsize=7.5, color="#C62828", fontstyle="italic")

    for field, data in fields_data.items():
        ax.scatter(data["HHI"], data["singleton_tail"],
                   s=120, c=colors_map[field], marker=markers_map[field],
                   edgecolors="#333", linewidths=0.8, zorder=5, alpha=0.8)
        dx, dy = 0.01, 0.02
        if field == "ai_component":
            dy = -0.04
        ax.annotate(field, (data["HHI"] + dx, data["singleton_tail"] + dy),
                    fontsize=8, fontweight="bold")

    ax.set_xlabel("HHI (Herfindahl-Hirschman Index)")
    ax.set_ylabel("Singleton Tail Share")
    ax.set_title("Three-Regime Fragmentation Typology")
    ax.set_xlim(-0.02, 0.62)
    ax.set_ylim(-0.05, 1.05)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig5_fragmentation_regimes.png")
    plt.close(fig)
    print("  OK: fig5_fragmentation_regimes.png")


# ---- Fig 6: Within vs cross-family overlap curves ----

def fig6_overlap_curves(proj):
    fields = {"ai_component": proj[proj["ai_component"] != ""]["ai_component"].tolist(),
              "use_case": proj[proj["use_case"] != ""]["use_case"].tolist()}

    k_values = [10, 15, 20, 25, 30, 40, 50, 75, 100]

    def top_k_pairs(sim_matrix, values, k):
        n = len(values)
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((sim_matrix[i, j], values[i], values[j]))
        pairs.sort(reverse=True)
        return set((min(a, b), max(a, b)) for _, a, b in pairs[:k])

    fig, axes = plt.subplots(2, 1, figsize=(6, 9))

    for ax_idx, (field, values) in enumerate(fields.items()):
        unique_vals = list(set(values))
        if len(unique_vals) < 20:
            continue

        tfidf_char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                     max_features=5000, sublinear_tf=True)
        tfidf_word = TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                     max_features=5000, sublinear_tf=True)

        X_char = tfidf_char.fit_transform(unique_vals)
        X_word = tfidf_word.fit_transform(unique_vals)
        sim_char = cosine_similarity(X_char).astype(np.float32)
        sim_word = cosine_similarity(X_word).astype(np.float32)

        try:
            from sentence_transformers import SentenceTransformer
            sbert_mini = SentenceTransformer("all-MiniLM-L6-v2")
            emb_mini = sbert_mini.encode(unique_vals, show_progress_bar=False, batch_size=128)
            sim_minilm = cosine_similarity(emb_mini).astype(np.float32)

            sbert_mpnet = SentenceTransformer("all-mpnet-base-v2")
            emb_mpnet = sbert_mpnet.encode(unique_vals, show_progress_bar=False, batch_size=128)
            sim_mpnet = cosine_similarity(emb_mpnet).astype(np.float32)

            e5 = SentenceTransformer("intfloat/e5-large-v2")
            e5_texts = ["query: " + v for v in unique_vals]
            emb_e5 = e5.encode(e5_texts, show_progress_bar=False, batch_size=64)
            sim_e5 = cosine_similarity(emb_e5).astype(np.float32)

            has_dense = True
        except Exception:
            has_dense = False

        ops = {"A (TF-IDF char)": sim_char, "B (TF-IDF word)": sim_word}
        if has_dense:
            ops["C (MiniLM)"] = sim_minilm
            ops["D (mpnet)"] = sim_mpnet
            ops["E (E5-large)"] = sim_e5

        def get_family(name):
            if "TF-IDF" in name:
                return "sparse"
            return "dense"

        op_names = list(ops.keys())
        within_pairs = []
        cross_pairs = []
        for i in range(len(op_names)):
            for j in range(i + 1, len(op_names)):
                if get_family(op_names[i]) == get_family(op_names[j]):
                    within_pairs.append((op_names[i], op_names[j]))
                else:
                    cross_pairs.append((op_names[i], op_names[j]))

        all_overlaps = {}
        for name_i, name_j in within_pairs + cross_pairs:
            overlaps = []
            for k in k_values:
                if k > len(unique_vals) * (len(unique_vals) - 1) // 2:
                    break
                s1 = top_k_pairs(ops[name_i], unique_vals, k)
                s2 = top_k_pairs(ops[name_j], unique_vals, k)
                ov = len(s1 & s2) / k if k > 0 else 0
                overlaps.append(ov)
            all_overlaps[(name_i, name_j)] = overlaps

        within_sparse_color = "#2196F3"
        within_dense_color = "#4CAF50"
        cross_color = "#FF7043"

        ax = axes[ax_idx]
        for name_i, name_j in within_pairs:
            overlaps = all_overlaps[(name_i, name_j)]
            is_sparse = "TF-IDF" in name_i
            color = within_sparse_color if is_sparse else within_dense_color
            short = f"{name_i.split('(')[1].split(')')[0]}×{name_j.split('(')[1].split(')')[0]}"
            prefix = "W-sparse" if is_sparse else "W-dense"
            ax.plot(k_values[:len(overlaps)], overlaps, "o-", lw=2,
                    markersize=4, label=f"{prefix}: {short}", color=color,
                    alpha=0.9 if is_sparse else 0.7)

        for name_i, name_j in cross_pairs:
            overlaps = all_overlaps[(name_i, name_j)]
            short = f"{name_i.split('(')[1].split(')')[0]}×{name_j.split('(')[1].split(')')[0]}"
            ax.plot(k_values[:len(overlaps)], overlaps, "s--", lw=1.2,
                    markersize=3, label=f"Cross: {short}", color=cross_color, alpha=0.5)

        within_s_vals = [all_overlaps[p] for p in within_pairs if "TF-IDF" in p[0]]
        within_d_vals = [all_overlaps[p] for p in within_pairs if "TF-IDF" not in p[0]]
        cross_vals = [all_overlaps[p] for p in cross_pairs]

        def mean_at_k(lists, idx):
            vals = [l[idx] for l in lists if idx < len(l)]
            return np.mean(vals) if vals else 0

        n_k = min(len(v) for v in all_overlaps.values())
        print(f"    {field}: within-sparse mean = "
              f"{np.mean([mean_at_k(within_s_vals, i) for i in range(n_k)]):.3f}, "
              f"within-dense mean = "
              f"{np.mean([mean_at_k(within_d_vals, i) for i in range(n_k)]):.3f}, "
              f"cross mean = "
              f"{np.mean([mean_at_k(cross_vals, i) for i in range(n_k)]):.3f}")

        ax.set_xlabel("k (top-k pairs)")
        ax.set_ylabel("Overlap@k")
        ax.set_title(f"{field}")
        ax.set_ylim(0, 0.95)
        ax.legend(fontsize=5.5, loc="lower right", ncol=2)

    fig.suptitle("Within- vs Cross-Family Overlap Curves (5 operationalizations)", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig6_cross_family_overlap.png")
    plt.close(fig)
    print("  OK: fig6_cross_family_overlap.png")


# ---- Fig 7: MovieLens replication (uses data/movielens/tags.csv) ----

def fig7_movielens():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  SKIP: fig7 (no sentence_transformers)")
        return

    tags_path = DATA / "movielens" / "tags.csv"
    if tags_path.exists():
        tags_df = pd.read_csv(tags_path)
        raw_tags = tags_df["tag"].dropna().tolist()
        unique_tags = sorted(set(
            t.strip().lower() for t in raw_tags if len(str(t).split()) >= 2
        ))
    else:
        print("  SKIP: fig7 (data/movielens/tags.csv not found)")
        return

    def top_k_pairs(sim, vals, k):
        n = len(vals)
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((sim[i, j], vals[i], vals[j]))
        pairs.sort(reverse=True)
        return set((min(a, b), max(a, b)) for _, a, b in pairs[:k])

    tfidf_char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                 max_features=5000, sublinear_tf=True)
    tfidf_word = TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                 max_features=5000, sublinear_tf=True)
    X_char = tfidf_char.fit_transform(unique_tags)
    X_word = tfidf_word.fit_transform(unique_tags)
    sim_char = cosine_similarity(X_char).astype(np.float32)
    sim_word = cosine_similarity(X_word).astype(np.float32)

    sbert_mini = SentenceTransformer("all-MiniLM-L6-v2")
    emb_mini = sbert_mini.encode(unique_tags, show_progress_bar=False, batch_size=128)
    sim_minilm = cosine_similarity(emb_mini).astype(np.float32)

    sbert_mpnet = SentenceTransformer("all-mpnet-base-v2")
    emb_mpnet = sbert_mpnet.encode(unique_tags, show_progress_bar=False, batch_size=128)
    sim_mpnet = cosine_similarity(emb_mpnet).astype(np.float32)

    e5 = SentenceTransformer("intfloat/e5-large-v2")
    e5_texts = ["query: " + t for t in unique_tags]
    emb_e5 = e5.encode(e5_texts, show_progress_bar=False, batch_size=64)
    sim_e5 = cosine_similarity(emb_e5).astype(np.float32)

    ops = {
        "A (TF-IDF char)": sim_char,
        "B (TF-IDF word)": sim_word,
        "C (MiniLM)": sim_minilm,
        "D (mpnet)": sim_mpnet,
        "E (E5-large)": sim_e5,
    }

    def get_family(name):
        if "TF-IDF" in name:
            return "sparse"
        return "dense"

    k_values = [10, 15, 20, 25, 30, 40, 50]
    op_names = list(ops.keys())

    within_overlaps = {}
    cross_overlaps = {}
    for i in range(len(op_names)):
        for j in range(i + 1, len(op_names)):
            overlaps = []
            for k in k_values:
                s1 = top_k_pairs(ops[op_names[i]], unique_tags, k)
                s2 = top_k_pairs(ops[op_names[j]], unique_tags, k)
                ov = len(s1 & s2) / k if k > 0 else 0
                overlaps.append(ov)
            pair_key = f"{op_names[i].split('(')[1].split(')')[0]}×{op_names[j].split('(')[1].split(')')[0]}"
            if get_family(op_names[i]) == get_family(op_names[j]):
                within_overlaps[pair_key] = overlaps
            else:
                cross_overlaps[pair_key] = overlaps

    within_mean = [np.mean([v[ki] for v in within_overlaps.values()])
                   for ki in range(len(k_values))]
    cross_mean = [np.mean([v[ki] for v in cross_overlaps.values()])
                  for ki in range(len(k_values))]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for label, overlaps in within_overlaps.items():
        ax.plot(k_values, overlaps, "o-", lw=1, markersize=3,
                color="#2196F3", alpha=0.3)
    for label, overlaps in cross_overlaps.items():
        ax.plot(k_values, overlaps, "s--", lw=0.8, markersize=2,
                color="#FF7043", alpha=0.2)

    ax.plot(k_values, within_mean, "o-", lw=2.5, color="#1565C0",
            label=f"Within-family mean (n={len(within_overlaps)})", markersize=5)
    ax.plot(k_values, cross_mean, "s--", lw=2.5, color="#BF360C",
            label=f"Cross-family mean (n={len(cross_overlaps)})", markersize=5)

    if len(k_values) >= 4:
        k_gap = k_values[3]
        y_top = within_mean[3]
        y_bot = cross_mean[3]
        y_mid = (y_top + y_bot) / 2
        delta = y_top - y_bot
        ax.annotate("", xy=(k_gap, y_top), xytext=(k_gap, y_bot),
                    arrowprops=dict(arrowstyle="<->", color="#333", lw=1.5))
        ax.text(k_gap + 1.5, y_mid, f"$\\Delta$ = {delta:.2f}",
                fontsize=9, fontweight="bold", color="#333", va="center")

    print(f"  MovieLens: within-family mean = {np.mean(within_mean):.3f}, "
          f"cross-family mean = {np.mean(cross_mean):.3f}, "
          f"Delta@k=25 = {within_mean[3] - cross_mean[3]:.3f}")

    ax.set_xlabel("k (top-k pairs)")
    ax.set_ylabel("Overlap@k")
    ax.set_title(f"MovieLens Cross-Domain Replication (N = {len(unique_tags)} tags, 5 ops)")
    ax.legend(loc="upper right", fontsize=7)
    ax.set_ylim(0, 0.85)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig7_movielens_replication.png")
    plt.close(fig)
    print("  OK: fig7_movielens_replication.png")


# ---- Fig S1: MCA biplot ----

def fig_s1_mca(proj):
    try:
        import prince
    except ImportError:
        print("  SKIP: fig_s1_mca.png (pip install prince)")
        return

    df = proj[["category_labels", "token_type", "chain"]].copy()
    df = df[(df["token_type"] != "") & (df["chain"] != "")]
    if len(df) < 30:
        print("  SKIP: fig_s1_mca.png (insufficient data)")
        return

    top_cats = proj["labels_list"].explode().value_counts().head(8).index.tolist()
    df["cat_group"] = df["category_labels"].apply(
        lambda x: next((l for l in x.split(";") if l.strip() in top_cats),
                        "Other") if pd.notna(x) else "Other")

    tt_counts = df["token_type"].value_counts()
    top_tt = tt_counts.head(6).index.tolist()
    df["tt_group"] = df["token_type"].apply(lambda x: x if x in top_tt else "Other")

    chain_counts = df["chain"].value_counts()
    top_chains = chain_counts.head(5).index.tolist()
    df["chain_group"] = df["chain"].apply(lambda x: x if x in top_chains else "Other")

    mca_input = df[["cat_group", "tt_group", "chain_group"]].astype(str)
    mca = prince.MCA(n_components=2, random_state=42)
    mca = mca.fit(mca_input)
    coords = mca.row_coordinates(mca_input)

    fig, ax = plt.subplots(figsize=(8, 6))
    cats_unique = mca_input["cat_group"].unique()
    cmap = plt.cm.get_cmap("tab10", len(cats_unique))
    for i, cat in enumerate(cats_unique):
        mask = mca_input["cat_group"] == cat
        ax.scatter(coords.loc[mask, 0], coords.loc[mask, 1],
                   s=25, alpha=0.5, label=cat, color=cmap(i))

    col_coords = mca.column_coordinates(mca_input)
    for idx, row in col_coords.iterrows():
        label = str(idx)
        ax.annotate(label, (row[0], row[1]), fontsize=6, alpha=0.8,
                    fontweight="bold", color="#333")

    inertia = mca.eigenvalues_
    total_inertia = sum(inertia)
    pct1 = inertia[0] / total_inertia * 100 if total_inertia > 0 else 0
    pct2 = inertia[1] / total_inertia * 100 if total_inertia > 0 else 0

    ax.set_xlabel(f"Dimension 1 ({pct1:.1f}%)")
    ax.set_ylabel(f"Dimension 2 ({pct2:.1f}%)")
    ax.set_title("MCA Biplot: token_type x Category x chain")
    ax.legend(fontsize=6, loc="best", ncol=2)
    ax.axhline(0, color="#ccc", lw=0.5)
    ax.axvline(0, color="#ccc", lw=0.5)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig_s1_mca.png", pad_inches=0.05)
    plt.close(fig)
    print("  OK: fig_s1_mca.png")


# ---- Fig S4: t-SNE label maps ----

def fig_s4_tsne(proj):
    from sklearn.manifold import TSNE
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  SKIP: fig_s4_tsne.png (no sentence_transformers)")
        return

    fig, axes = plt.subplots(2, 1, figsize=(6, 10))
    sbert = SentenceTransformer("all-MiniLM-L6-v2")

    for ax_idx, field in enumerate(["ai_component", "use_case"]):
        vals = proj[proj[field] != ""][field].tolist()
        unique_vals = list(set(vals))
        if len(unique_vals) < 20:
            continue

        freq = Counter(vals)
        def freq_class(v):
            c = freq[v]
            if c >= 10:
                return "head"
            elif c >= 3:
                return "mid"
            return "tail"

        emb = sbert.encode(unique_vals, show_progress_bar=False, batch_size=128)
        perp = min(30, len(unique_vals) - 1)
        tsne = TSNE(n_components=2, perplexity=perp, random_state=42,
                     init="pca", learning_rate="auto")
        coords = tsne.fit_transform(emb)

        classes = [freq_class(v) for v in unique_vals]
        color_map = {"head": "#D32F2F", "mid": "#FF9800", "tail": "#90CAF9"}
        sizes_map = [60 if c == "head" else 30 if c == "mid" else 8 for c in classes]

        ax = axes[ax_idx]
        for cls in ["tail", "mid", "head"]:
            mask = [c == cls for c in classes]
            xs = [coords[i, 0] for i, m in enumerate(mask) if m]
            ys = [coords[i, 1] for i, m in enumerate(mask) if m]
            sz = [sizes_map[i] for i, m in enumerate(mask) if m]
            ax.scatter(xs, ys, s=sz, c=color_map[cls], alpha=0.6,
                       label=f"{cls} (n={sum(mask)})", edgecolors="none")

        ax.set_title(field, fontsize=10)
        ax.set_xlabel("t-SNE 1")
        ax.set_ylabel("t-SNE 2")
        ax.legend(fontsize=7, loc="best")

    fig.suptitle("t-SNE Label Maps (SBERT MiniLM embeddings)", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_s4_tsne.png", pad_inches=0.05)
    plt.close(fig)
    print("  OK: fig_s4_tsne.png")


# ---- Fig S5: Rank-frequency curves ----

def fig_s5_rank_frequency(proj):
    fields = ["type", "chain", "token_type", "ai_component", "use_case"]
    colors = ["#4CAF50", "#FF9800", "#FF9800", "#F44336", "#F44336"]
    markers = ["D", "s", "^", "o", "v"]

    fig, ax = plt.subplots(figsize=(7, 5))

    for field, color, marker in zip(fields, colors, markers):
        vals = proj[proj[field] != ""][field].tolist()
        if not vals:
            continue
        freq = sorted(Counter(vals).values(), reverse=True)
        ranks = list(range(1, len(freq) + 1))
        ax.plot(ranks, freq, marker=marker, markersize=3, lw=1.2,
                color=color, alpha=0.8, label=field)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Rank (log)")
    ax.set_ylabel("Frequency (log)")
    ax.set_title("Rank-Frequency Curves (all fields)")
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig_s5_rank_frequency.png", pad_inches=0.05)
    plt.close(fig)
    print("  OK: fig_s5_rank_frequency.png")


# ---- Main ----

def main():
    parser = argparse.ArgumentParser(
        description="Generate figures for Article A (Taxonomy Vocabulary Governance)")
    parser.add_argument("--corpus", type=str, default=None,
                        help="Path to project_cards.json (proprietary; required for figs 2-6, S1, S4, S5)")
    parser.add_argument("--passport", type=str, default=None,
                        help="Path to passport_fields.csv (required alongside --corpus)")
    args = parser.parse_args()

    has_corpus = args.corpus and args.passport

    print("Generating figures...")
    print("  (figures/ already contains pre-generated PNGs for reference)\n")

    print("Main figures:")
    fig1_pipeline()

    if has_corpus:
        print(f"\nLoading corpus from {args.corpus}...")
        proj = load_corpus(args.corpus, args.passport)
        print(f"  N = {len(proj)}")

        fig2_label_network(proj)
        fig3_kg_edges(proj)
        fig4_blurring_typology(proj)
        fig5_fragmentation(proj)
        fig6_overlap_curves(proj)
    else:
        print("\n  [Corpus not provided] Skipping figs 2-6.")
        print("  Use --corpus and --passport to regenerate from raw data.")
        print("  Pre-generated figures are available in figures/.\n")

    fig7_movielens()

    if has_corpus:
        print("\nSupplementary figures:")
        fig_s1_mca(proj)
        fig_s4_tsne(proj)
        fig_s5_rank_frequency(proj)
    else:
        print("  [Corpus not provided] Skipping supplementary figs S1, S4, S5.")

    n_figs = len(list(FIGURES.glob("*.png")))
    print(f"\nDone. {n_figs} figures in {FIGURES}")


if __name__ == "__main__":
    main()
