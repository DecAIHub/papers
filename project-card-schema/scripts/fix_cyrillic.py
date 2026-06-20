"""Fix Cyrillic values in zenodo JSON files."""

import json, re, os, sys

sys.stdout.reconfigure(encoding="utf-8")

# Directory holding project_cards.json and the cards/ subfolder (the Zenodo
# dataset, DOI 10.5281/zenodo.18900950). Override via argv[1] or DATA_DIR.
ZENODO = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATA_DIR", ".")

cyrillic_re = re.compile(r"[а-яА-ЯёЁ]")

FIXES = {
    "utility (не подтверждено) / meme": "utility",
    "discovery агентов и комьюнити вокруг токена": "other",
    "AI\u2011сервис (заявлено)": "other",
    "AI-сервис (заявлено)": "other",
}

CONTAINS_FIXES = [
    ("каталог", "agents"),
]

with open(os.path.join(ZENODO, "project_cards.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)

fixed = 0
for card in cards:
    for field in ["Category", "chain", "type", "token_type", "ai_component", "use_case"]:
        val = card["passport"].get(field)
        if val and cyrillic_re.search(val):
            if val in FIXES:
                card["passport"][field] = FIXES[val]
                fixed += 1
                print(f"  Fixed {card['project_id']}.{field}: {val!r} -> {FIXES[val]!r}")
                continue
            matched = False
            for substr, replacement in CONTAINS_FIXES:
                if substr in val:
                    card["passport"][field] = replacement
                    fixed += 1
                    print(f"  Fixed {card['project_id']}.{field}: {val!r} -> {replacement!r}")
                    matched = True
                    break
            if not matched:
                print(f"  UNFIXED {card['project_id']}.{field}: {val!r}")

    for ev in card.get("evidence", []):
        for key in ["source_url", "claim_field", "tier"]:
            val = ev.get(key)
            if val and cyrillic_re.search(val):
                print(f"  UNFIXED evidence {card['project_id']}.{key}: {val!r}")

with open(os.path.join(ZENODO, "project_cards.json"), "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=2)

cards_dir = os.path.join(ZENODO, "cards")
for card in cards:
    card_path = os.path.join(cards_dir, f"{card['project_id']}.json")
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)

print(f"\nFixed {fixed} fields total.")

remaining = 0
for card in cards:
    for field in ["Category", "chain", "type", "token_type", "ai_component", "use_case"]:
        val = card["passport"].get(field)
        if val and cyrillic_re.search(val):
            remaining += 1
            print(f"  STILL: {card['project_id']}.{field}: {val!r}")
print(f"Remaining Cyrillic in passport fields: {remaining}")
