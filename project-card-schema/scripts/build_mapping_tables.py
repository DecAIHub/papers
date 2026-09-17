"""
Apply the vocabulary rules (vocab.py) to every distinct raw passport value and
write reviewable mapping tables (one row per distinct raw value).

Usage: python build_mapping_tables.py <cards_raw.json> <out_dir>
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import vocab


def main():
    cards = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)

    def write(name, header, rows):
        with open(out / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)

    # chain
    c = Counter(vocab.render_english(k["passport"].get("chain")) for k in cards if k["passport"].get("chain"))
    write("mapping_chain.csv", ["raw_value", "n", "canonical"],
          [(v, n, vocab.map_chain(v)) for v, n in c.most_common()])
    # type
    c = Counter(vocab.render_english(k["passport"].get("type")) for k in cards if k["passport"].get("type"))
    write("mapping_type.csv", ["raw_value", "n", "canonical"],
          [(v, n, vocab.map_type(v)) for v, n in c.most_common()])
    # token_type
    c = Counter(vocab.render_english(k["passport"].get("token_type")) for k in cards if k["passport"].get("token_type"))
    rows = []
    for v, n in c.most_common():
        cls, mechs = vocab.map_token_type(v)
        rows.append((v, n, cls, " | ".join(mechs) if mechs else ""))
    write("mapping_token_type.csv", ["raw_value", "n", "canonical", "mechanisms"], rows)
    # Category
    c = Counter()
    for k in cards:
        v = k["passport"].get("Category")
        if v:
            for lab in [x.strip() for x in v.split("|") if x.strip()]:
                c[lab] += 1
    rows = []
    for lab, n in c.most_common():
        canon = [lab] if lab in vocab.CATEGORY_CANON else vocab.CATEGORY_MAP.get(lab, ["Other"])
        rows.append((lab, n, " | ".join(canon)))
    write("mapping_Category.csv", ["raw_label", "n", "canonical"], rows)
    unmapped = [lab for lab, n in c.items() if lab not in vocab.CATEGORY_CANON and lab not in vocab.CATEGORY_MAP]
    print("\nCategory labels without explicit mapping (-> Other):", unmapped)


if __name__ == "__main__":
    main()
