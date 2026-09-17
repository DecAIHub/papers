"""
Reproducible downstream example on the ABPC deposit (v1.1.0), seed 42.

(1) Cross-chain segmentation: canonical Category labels by infrastructure type.
(2) Evidence-aware screening: how a primary-source threshold changes the corpus.
(3) Multi-label Category classification from the free-text passport fields
    (TF-IDF + one-vs-rest logistic regression, 5-fold CV), evaluated overall and
    by primary-source stratum.

Usage: python case_study.py <project_cards.json> <out_json>
"""
import json
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import chi2_contingency
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import KFold
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

SEED = 42


def tier1_share(r):
    ev = r["evidence"]
    return sum(1 for e in ev if e["tier"] == "Tier-1") / len(ev)


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    out = {}
    core = [r for r in data if not r["stub"]]

    # (1) cross-chain segmentation ---------------------------------------------------------
    types = ["EVM", "non-EVM", "Appchain"]
    lab_counts = Counter(l for r in core for l in (r["passport"]["Category"] or "").split(" | ") if l)
    classes = [c for c, n in lab_counts.most_common() if n >= 10]
    table = defaultdict(Counter)
    for r in core:
        t = r["passport"]["type"]
        if t in types:
            for l in (r["passport"]["Category"] or "").split(" | "):
                if l in classes:
                    table[t][l] += 1
    mat = np.array([[table[t][a] for a in classes] for t in types])
    chi2, p, dof, _ = chi2_contingency(mat)
    out["cross_chain"] = {"types": types, "classes": classes, "counts": mat.tolist(),
                          "row_pct": (100 * mat / mat.sum(axis=1, keepdims=True)).round(1).tolist(),
                          "chi2": round(float(chi2), 1), "dof": int(dof), "p": float(p)}

    # (2) evidence-aware screening ---------------------------------------------------------
    scr = {}
    for thr in (0.5, 0.75, 0.9):
        kept = [r for r in core if tier1_share(r) >= thr]
        cats = Counter(l for r in kept for l in (r["passport"]["Category"] or "").split(" | ") if l)
        scr[str(thr)] = {"kept": len(kept), "kept_pct": round(100 * len(kept) / len(core), 1),
                         "meme_share_pct": round(100 * cats["Meme"] / len(kept), 1) if kept else None,
                         "ai_agents_share_pct": round(100 * cats["AI/Agents"] / len(kept), 1) if kept else None}
    all_cats = Counter(l for r in core for l in (r["passport"]["Category"] or "").split(" | ") if l)
    scr["baseline"] = {"kept": len(core), "meme_share_pct": round(100 * all_cats["Meme"] / len(core), 1),
                       "ai_agents_share_pct": round(100 * all_cats["AI/Agents"] / len(core), 1)}
    out["screening"] = scr

    # (3) multi-label classification ----------------------------------------------------------
    rows = [r for r in core if r["passport"]["Category"]]
    texts = [" ".join(filter(None, [r["passport"]["ai_component"], r["passport"]["use_case"],
                                     r["passport"]["token_type_raw"], r["passport"]["chain_raw"]])) for r in rows]
    labels = [r["passport"]["Category"].split(" | ") for r in rows]
    mlb = MultiLabelBinarizer()
    Y = mlb.fit_transform(labels)
    keep = Y.sum(axis=0) >= 10          # labels with >= 10 positives
    Y = Y[:, keep]
    label_names = [l for l, k in zip(mlb.classes_, keep) if k]
    strata = np.array([tier1_share(r) >= 0.8 for r in rows])
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    pred = np.zeros_like(Y)
    for tr, te in kf.split(texts):
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        Xtr = vec.fit_transform([texts[i] for i in tr])
        Xte = vec.transform([texts[i] for i in te])
        clf = OneVsRestClassifier(LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced", random_state=SEED))
        clf.fit(Xtr, Y[tr])
        pred[te] = clf.predict(Xte)
    res = {"n_cards": len(rows), "labels": label_names,
           "micro_f1_all": round(float(f1_score(Y, pred, average="micro")), 3),
           "macro_f1_all": round(float(f1_score(Y, pred, average="macro")), 3),
           "micro_f1_high_tier1": round(float(f1_score(Y[strata], pred[strata], average="micro")), 3),
           "micro_f1_low_tier1": round(float(f1_score(Y[~strata], pred[~strata], average="micro")), 3),
           "n_high_tier1": int(strata.sum()), "n_low_tier1": int((~strata).sum()),
           "per_label_f1": {l: round(float(f), 3) for l, f in zip(label_names, f1_score(Y, pred, average=None))}}
    out["classification"] = res
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
