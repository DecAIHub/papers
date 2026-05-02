"""
Extract 845 project cards into schema-conforming JSON for Zenodo deposit.
Reads docs/projects/*.ru.commonmark.md → zenodo/project_cards.json + individual JSONs.
"""

import json, os, re, glob, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE, "..", "..", "projects")
ZENODO_DIR = os.path.join(BASE, "zenodo")
SCHEMA_SRC = os.path.join(BASE, "assets", "project_card.schema.json")

os.makedirs(ZENODO_DIR, exist_ok=True)

PASSPORT_MAP = {
    "Категория": "Category",
    "Категория (Category)": "Category",
    "Category": "Category",
    "Основная сеть (chain)": "chain",
    "chain": "chain",
    "Тип": "type",
    "Тип (type)": "type",
    "type": "type",
    "Модель токена (token_type)": "token_type",
    "token_type": "token_type",
    "AI‑компонент (ai_component)": "ai_component",
    "AI-компонент (ai_component)": "ai_component",
    "ai_component": "ai_component",
    "Use‑case (use_case)": "use_case",
    "Use-case (use_case)": "use_case",
    "use_case": "use_case",
}

LINK_MAP = {
    "Website": "website",
    "Docs": "documentation",
    "GitHub": "repository",
    "X": "social",
    "Discord": "social",
    "Telegram": "social",
}

CLAIM_KEYWORDS = {
    "ai_component": ["ai", "ии", "модел", "inference", "train", "llm", "ml ",
                      "machine learn", "нейро", "neural", "nlp", "gpt",
                      "семантич", "semantic", "intelligen", "copilot",
                      "analytics", "аналитик", "compute", "вычисл"],
    "use_case": ["use case", "use-case", "сценарий", "применен",
                  "portfolio", "trading", "marketplace", "gaming",
                  "content creat", "security audit", "identity",
                  "prediction", "labeling"],
    "token_type": ["токен", "token", "staking", "governance", "utility",
                    "reward", "payment", "erc-20", "bep-20", "spl",
                    "supply", "mint"],
    "chain": ["контракт", "contract", "mainnet", "chain", "сеть",
              "explorer", "etherscan", "basescan", "solscan", "bscscan",
              "polygonscan", "onchain", "on-chain", "on‑chain", "развёрнут"],
    "type": ["evm", "non-evm", "appchain", "l1", "l2", "rollup",
             "sidechain", "infrastructure"],
}


def infer_claim_field(description: str) -> str:
    desc_lower = description.lower()
    scores = {}
    for field, keywords in CLAIM_KEYWORDS.items():
        scores[field] = sum(1 for kw in keywords if kw in desc_lower)
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "Category"


def split_md_row(line: str) -> list[str]:
    """Split a markdown table row respecting escaped pipes (\\|)."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    placeholder = "\x00PIPE\x00"
    line = line.replace("\\|", placeholder)
    cells = [c.strip().replace(placeholder, "|") for c in line.split("|")]
    return cells


def _split_simple(line: str) -> list[str]:
    """Split a markdown row by literal pipe (legacy behaviour matching Article C)."""
    return [c.strip() for c in line.strip().split("|")]


def parse_table(text: str, header_pattern: str, *, escape_pipe: bool = True) -> list[dict]:
    """Find a markdown table after a line matching header_pattern.

    escape_pipe=True  → use split_md_row (handles \\|)
    escape_pipe=False → use simple split (matches legacy Article C counting)
    """
    splitter = split_md_row if escape_pipe else _split_simple
    lines = text.split("\n")
    rows = []
    in_table = False
    headers = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_table:
            if re.search(header_pattern, stripped, re.IGNORECASE):
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if candidate.startswith("|") and "|" in candidate[1:]:
                        cells = splitter(candidate)
                        cells = [c for c in cells if c]
                        if cells and not all(re.match(r'^[-:]+$', c) for c in cells):
                            headers = cells
                            in_table = True
                            break
        elif in_table:
            if stripped.startswith("|"):
                cells = splitter(stripped)
                cells = [c for c in cells if c]
                if all(re.match(r'^[-:]+$', c) for c in cells):
                    continue
                if cells:
                    rows.append(dict(zip(headers, cells)))
            elif stripped == "":
                continue
            else:
                break
    return rows


def clean_value(val: str) -> str | None:
    if not val or val.strip() in ("—", "–", "-", "н/д", "N/A", ""):
        return None
    val = val.strip()
    val = re.sub(r'\*\*', '', val)
    val = val.strip('` ')
    return val if val else None


def extract_card(filepath: str) -> dict | None:
    fname = os.path.basename(filepath)
    match = re.match(r'(\d+)_(.+)\.ru\.commonmark\.md$', fname)
    if not match:
        return None

    num, slug = match.groups()
    project_id = f"{num}-{slug}"

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    passport = {
        "Category": None,
        "chain": None,
        "type": None,
        "token_type": None,
        "ai_component": None,
        "use_case": None,
    }
    passport_rows = parse_table(text, r"Паспорт проекта|Passport")
    for row in passport_rows:
        field_name = row.get("Поле", row.get("Field", ""))
        field_name = re.sub(r'\*\*', '', field_name).strip()
        value = row.get("Значение", row.get("Value", ""))
        value = clean_value(value)

        if field_name in PASSPORT_MAP:
            schema_field = PASSPORT_MAP[field_name]
            passport[schema_field] = value

    if not passport["Category"] and not passport["chain"]:
        return None

    links = {"website": None, "documentation": None, "repository": None, "social": []}
    link_rows = parse_table(text, r"Ссылки|Links")
    for row in link_rows:
        link_type = row.get("Тип", row.get("Type", ""))
        link_type = re.sub(r'\*\*', '', link_type).strip()
        url = row.get("Ссылка", row.get("URL", row.get("Link", "")))
        url = clean_value(url)

        if not url:
            continue

        if link_type in LINK_MAP:
            target = LINK_MAP[link_type]
            if target == "social":
                links["social"].append(url)
            else:
                links[target] = url

    if not links["social"]:
        links["social"] = None

    last_verified = None
    for row in passport_rows:
        field_name = re.sub(r'\*\*', '', row.get("Поле", row.get("Field", ""))).strip()
        if "Last verified" in field_name or "last_verified" in field_name.lower():
            val = clean_value(row.get("Значение", row.get("Value", "")))
            if val and re.match(r'\d{4}-\d{2}-\d{2}', val):
                last_verified = val
            break

    evidence = []
    ev_rows = parse_table(text, r"^##\s*Evidence|Evidence.*таблица", escape_pipe=False)
    for row in ev_rows:
        tier_val = row.get("Tier", row.get("Тип", ""))
        tier_val = re.sub(r'\*\*', '', tier_val).strip()
        tier_val = tier_val.replace("‑", "-")

        source = row.get("Источник", row.get("Source", row.get("URL", "")))
        source = clean_value(source)

        description = row.get("Что доказывает", row.get("Description", row.get("What", "")))
        description = description if description else ""

        if not source or not tier_val:
            continue

        if tier_val not in ("Tier-1", "Tier-2", "Tier-3"):
            if "1" in tier_val:
                tier_val = "Tier-1"
            elif "2" in tier_val:
                tier_val = "Tier-2"
            elif "3" in tier_val:
                tier_val = "Tier-3"
            else:
                continue

        claim_field = infer_claim_field(description)

        entry = {
            "claim_field": claim_field,
            "source_url": source,
            "tier": tier_val,
            "verified_date": last_verified,
        }
        evidence.append(entry)

    seen_urls = set()
    deduped = []
    for entry in evidence:
        if entry["source_url"] not in seen_urls:
            seen_urls.add(entry["source_url"])
            deduped.append(entry)
    evidence = deduped

    if not evidence:
        evidence.append({
            "claim_field": "Category",
            "source_url": links.get("website") or "https://unknown",
            "tier": "Tier-1",
            "verified_date": last_verified,
        })

    card = {
        "project_id": project_id,
        "schema_version": "1.0.0",
        "passport": passport,
        "links": {
            "website": links["website"],
            "documentation": links["documentation"],
            "repository": links["repository"],
            "social": links["social"],
        },
        "evidence": evidence,
    }
    return card


def main():
    pattern = os.path.join(PROJECTS_DIR, "*.ru.commonmark.md")
    files = sorted(glob.glob(pattern))
    print(f"Found {len(files)} project files")

    cards = []
    errors = []
    for fpath in files:
        try:
            card = extract_card(fpath)
            if card:
                cards.append(card)
            else:
                errors.append(os.path.basename(fpath))
        except Exception as e:
            errors.append(f"{os.path.basename(fpath)}: {e}")

    print(f"Extracted: {len(cards)} cards")
    if errors:
        print(f"Skipped/errors: {len(errors)}")
        for e in errors[:10]:
            print(f"  - {e}")

    combined_path = os.path.join(ZENODO_DIR, "project_cards.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print(f"Written: {combined_path} ({len(cards)} records)")

    cards_dir = os.path.join(ZENODO_DIR, "cards")
    os.makedirs(cards_dir, exist_ok=True)
    for card in cards:
        card_path = os.path.join(cards_dir, f"{card['project_id']}.json")
        with open(card_path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)

    print(f"Written: {len(cards)} individual JSON files to {cards_dir}/")

    if os.path.exists(SCHEMA_SRC):
        import shutil
        shutil.copy2(SCHEMA_SRC, os.path.join(ZENODO_DIR, "project_card.schema.json"))
        print("Copied schema to zenodo/")

    passport_fields = ["Category", "chain", "type", "token_type", "ai_component", "use_case"]
    print("\n--- Passport completeness ---")
    for field in passport_fields:
        n_present = sum(1 for c in cards if c["passport"].get(field))
        n_missing = len(cards) - n_present
        pct = n_missing / len(cards) * 100 if cards else 0
        print(f"  {field}: {n_present} present, {n_missing} missing ({pct:.1f}%)")

    ev_counts = [len(c["evidence"]) for c in cards]
    print(f"\n--- Evidence ---")
    print(f"  Total entries: {sum(ev_counts)}")
    print(f"  Mean per card: {sum(ev_counts)/len(cards):.1f}")
    print(f"  Min: {min(ev_counts)}, Max: {max(ev_counts)}")


if __name__ == "__main__":
    main()
