"""
Validate every record of the deposit against the JSON Schema (draft 2020-12).

Usage: python validate.py <project_cards.json> <project_card.schema.json>
Prints the number of valid records and a breakdown of violations by (path, message).
Exit code 1 if any record is invalid.
"""
import json
import sys
from collections import Counter

from jsonschema import Draft202012Validator, FormatChecker


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    schema = json.load(open(sys.argv[2], encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema, format_checker=FormatChecker())
    bad = 0
    kinds = Counter()
    for rec in data:
        errs = list(v.iter_errors(rec))
        if errs:
            bad += 1
            for e in errs:
                path = "/".join(str(p) for p in e.absolute_path if not isinstance(p, int))
                kinds[(path, e.validator)] += 1
    print(f"records: {len(data)}; valid: {len(data) - bad}; invalid: {bad}")
    for (path, val), n in kinds.most_common():
        print(f"  {n:5d}  {path or '<root>'}  [{val}]")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
