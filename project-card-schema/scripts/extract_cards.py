"""
Parse the curated project-card registry (markdown, one card per project) into an
intermediate JSON used to build the ABPC deposit (v1.1.0).

Input : directory with cards named  NNN_slug.ru.commonmark.md
Output: cards_raw.json  - one object per card with passport (raw values), links
        (all link types), evidence rows (URL rows and "no primary source found"
        rows kept apart), claim-intensity flags, launch_date / last_verified.

Usage : python extract_cards.py <cards_dir> <out_json>
"""
import json
import re
import sys
from pathlib import Path

NBH = "\u2011"  # non-breaking hyphen used in the cards (e.g. "Tier‑1")

EMPTY = {"", "—", "–", "-", "н/д", "N/A", "n/a", "—."}

# passport row label -> field key. Keys in parentheses win when present.
LABEL_MAP = {
    "Название проекта": "name",
    "Категория": "Category",
    "Категория (Category)": "Category",
    "Category": "Category",
    "Тип": "type",
    "Тип (type)": "type",
    "type": "type",
    "Контракт токена": "token_contract",
    "Токен (стандарт)": "token_standard",
    "Last verified": "last_verified",
}
PAREN_KEYS = {
    "chain": "chain",
    "token_type": "token_type",
    "ai_component": "ai_component",
    "use_case": "use_case",
    "launch_date": "launch_date",
    "ticker": "ticker",
    "status": "status",
    "aliases": "aliases",
}

LINK_TYPE_MAP = {
    "Website": "website",
    "Docs": "documentation",
    "Whitepaper": "whitepaper",
    "GitHub": "repository",
    "Releases / Changelog": "releases",
    "Roadmap": "roadmap",
    "Security advisories": "security_advisories",
    "Explorer": "explorer",
    "App / Demo": "app",
    "Audit report(s)": "audit",
    "Bug bounty": "bug_bounty",
    "CoinGecko": "coingecko",
    "CoinMarketCap": "coinmarketcap",
    "X": "social",
    "Discord": "social",
    "Telegram": "social",
    "Medium": "social",
}
MULTI_LINK_KEYS = {"explorer", "audit", "social"}

def extract_urls(cell):
    """All http(s) tokens in a table cell (cells may hold 'url ; url' or 'url (comment)')."""
    if not cell:
        return []
    out = []
    for tok in re.split(r"[\s;]+", cell):
        if tok.startswith("http"):
            tok = tok.rstrip(".,;")
            if tok.endswith(")") and tok.count("(") < tok.count(")"):
                tok = tok[:-1]
            if tok not in out:
                out.append(tok)
    return out


FLAG_RE = re.compile(r"-\s*\*\*((?:AI|OC|TK)_\d)\s*\(decision\):\*\*\s*([01])")
DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?")


def clean(v):
    if v is None:
        return None
    v = v.strip()
    v = re.sub(r"\*\*", "", v).strip().strip("`").strip()
    if v in EMPTY:
        return None
    return v or None


def split_row(line):
    """Split a markdown table row on unescaped pipes."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    s = s.replace("\\|", "\x00")
    return [c.strip().replace("\x00", "|") for c in s.split("|")]


def is_sep(cells):
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells)


def table_after(lines, start_idx, stop_at_heading=True):
    """Return table rows (as cell lists) that follow line index start_idx."""
    rows = []
    started = False
    for j in range(start_idx + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("|"):
            cells = split_row(s)
            if is_sep(cells):
                continue
            rows.append(cells)
            started = True
        elif s == "":
            if started and j + 1 < len(lines) and not lines[j + 1].strip().startswith("|"):
                break
            continue
        else:
            if started or (stop_at_heading and s.startswith("#")):
                break
    return rows


def find_heading(lines, pattern):
    rx = re.compile(pattern)
    for i, l in enumerate(lines):
        if rx.match(l.strip()):
            return i
    return None


def parse_launch_date(raw):
    if not raw:
        return None
    m = DATE_RE.match(raw.strip())
    if not m:
        return None
    y, mo, d = m.groups()
    if mo and d:
        return f"{y}-{mo}-{d}"
    if mo:
        return f"{y}-{mo}"
    return y


def parse_card(path: Path):
    m = re.match(r"(\d+)_(.+)\.ru\.commonmark\.md$", path.name)
    if not m:
        return None
    num, slug = m.groups()
    project_id = f"{num}-{slug}"
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # ---- passport -------------------------------------------------------
    passport = {}
    hi = find_heading(lines, r"^##\s*Паспорт проекта")
    if hi is not None:
        for cells in table_after(lines, hi):
            if len(cells) < 2 or cells[0] in ("Поле", "Field"):
                continue
            label = clean(cells[0]) or ""
            label_norm = label.replace(NBH, "-")
            key = None
            pm = re.search(r"\(([a-z_]+)\)\s*$", label_norm)
            if pm and pm.group(1) in PAREN_KEYS:
                key = PAREN_KEYS[pm.group(1)]
            elif label_norm in LABEL_MAP:
                key = LABEL_MAP[label_norm]
            if key:
                passport[key] = clean(cells[1])

    # ---- links ------------------------------------------------------------
    links = {}
    link_rows_raw = []
    li = find_heading(lines, r"^###\s*Ссылки")
    if li is not None:
        for cells in table_after(lines, li):
            if len(cells) < 2 or cells[0] in ("Тип", "Type"):
                continue
            ltype = clean(cells[0]) or ""
            url_cell = clean(cells[1])
            urls = extract_urls(url_cell)
            link_rows_raw.append({"type": ltype, "value": url_cell})
            if not urls:
                continue
            # strip a trailing qualifier such as "Explorer (Ethereum)" but keep "Audit report(s)"
            base = re.sub(r"\s+\(.*\)\s*$", "", ltype).strip()
            if base.startswith("Audit report"):
                base = "Audit report(s)"
            key = LINK_TYPE_MAP.get(base)
            if key is None:
                links.setdefault("other", []).append({"type": ltype, "url": urls[0]})
                continue
            if key in MULTI_LINK_KEYS:
                links.setdefault(key, [])
                for u in urls:
                    if u not in links[key]:
                        links[key].append(u)
            else:
                if key not in links:
                    links[key] = urls[0]
                else:
                    links.setdefault("other", []).append({"type": ltype, "url": urls[0]})

    # ---- evidence ---------------------------------------------------------
    evidence, gaps, dropped = [], [], 0
    ei = find_heading(lines, r"^##\s*Evidence")
    if ei is not None:
        for cells in table_after(lines, ei):
            if len(cells) < 2 or cells[0] in ("Tier", "Тир"):
                continue
            tier = clean(cells[0]) or ""
            tier = tier.replace(NBH, "-")
            tm = re.search(r"Tier-?\s*([123])", tier)
            tier = f"Tier-{tm.group(1)}" if tm else None
            src = clean(cells[1]) if len(cells) > 1 else None
            note = clean(cells[2]) if len(cells) > 2 else None
            urls = extract_urls(src)
            if urls:
                for u in urls:  # a cell may list several URLs supporting the same claim
                    evidence.append({"tier": tier, "source_url": u, "source_cell": src, "claim_note": note})
            elif note:
                kind = "not_found" if re.search(r"не найден|не установлен|не подтвержд|не получен|не извлеч|недоступ", note) else "note"
                gaps.append({"tier": tier, "kind": kind, "claim_note": note})
            else:
                dropped += 1

    # ---- claim-intensity flags -------------------------------------------
    flags = {k: int(v) for k, v in FLAG_RE.findall(text)}

    return {
        "project_id": project_id,
        "file": path.name,
        "passport": passport,
        "launch_date": parse_launch_date(passport.get("launch_date")),
        "links": links,
        "link_rows": link_rows_raw,
        "evidence": evidence,
        "evidence_gaps": gaps,
        "evidence_rows_dropped": dropped,
        "claim_flags": flags,
    }


def main():
    cards_dir = Path(sys.argv[1])
    out = Path(sys.argv[2])
    cards = []
    for p in sorted(cards_dir.glob("*.ru.commonmark.md")):
        c = parse_card(p)
        if c:
            cards.append(c)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    n_ev = sum(len(c["evidence"]) for c in cards)
    n_gap = sum(len(c["evidence_gaps"]) for c in cards)
    n_drop = sum(c["evidence_rows_dropped"] for c in cards)
    print(f"cards: {len(cards)}; evidence rows with URL: {n_ev}; gap rows: {n_gap}; empty rows dropped: {n_drop}")
    print("flags per card:", sorted({len(c["claim_flags"]) for c in cards}))
    from collections import Counter
    lt = Counter()
    for c in cards:
        for k, v in c["links"].items():
            lt[k] += 1
    print("cards with link key:", dict(lt))
    other = Counter(o["type"] for c in cards for o in c["links"].get("other", []))
    print("unmapped link types (top 30):", other.most_common(30))
    print("cards with website:", sum(1 for c in cards if c["links"].get("website")))


if __name__ == "__main__":
    main()
