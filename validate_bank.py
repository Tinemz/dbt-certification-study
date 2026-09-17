#!/usr/bin/env python3
"""Validate the question bank. Run after editing exams/bank/*.yml.

Checks every question against the schema documented in CLAUDE.md and resolves
every docs_ref against the vendored docs. Exits non-zero on any violation.

    .venv/bin/python3 validate_bank.py
"""
import glob
import os
import sys
from collections import Counter

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))


def load():
    topics = yaml.safe_load(open(os.path.join(ROOT, "exam/topics.yml")))
    questions = []
    for path in sorted(glob.glob(os.path.join(ROOT, "exams/bank/*.yml"))):
        questions += yaml.safe_load(open(path))
    return topics, questions


def validate(topics, questions):
    """Fail loudly rather than drill a broken question."""
    subskills = {s["id"] for t in topics["topics"] for s in t["subskills"]}
    errors = []
    seen = set()
    for q in questions:
        qid = q.get("id", "<no id>")
        if qid in seen:
            errors.append(f"{qid}: duplicate id")
        seen.add(qid)
        if q.get("subskill") not in subskills:
            errors.append(f"{qid}: unknown subskill {q.get('subskill')}")
        if not os.path.isfile(os.path.join(ROOT, "vendor/dbt-docs", q.get("docs_ref", ""))):
            errors.append(f"{qid}: docs_ref does not resolve")
        t = q.get("type")
        if t == "multiple-choice":
            if not set(q.get("answer", [])) <= set(q.get("options", {})):
                errors.append(f"{qid}: answer not among options")
        elif t == "domc":
            opts = q.get("domc_options", [])
            if not any(o["keyed"] for o in opts) or not any(not o["keyed"] for o in opts):
                errors.append(f"{qid}: domc needs both keyed and distractor options")
        elif t == "fill-in-blank":
            if not q.get("answer"):
                errors.append(f"{qid}: no accepted answers")
        elif t == "matching":
            pairs = q.get("pairs", [])
            if len({p["right"] for p in pairs}) != len(pairs):
                errors.append(f"{qid}: duplicate right-hand values")
        elif t == "build-list":
            if len(q.get("sequence", [])) < 3:
                errors.append(f"{qid}: sequence too short")
        elif t == "hotspot":
            lines = q.get("code", "").rstrip("\n").split("\n")
            if not 1 <= q.get("answer_line", 0) <= len(lines):
                errors.append(f"{qid}: answer_line outside the code block")
            if q.get("format_source") != "inferred":
                errors.append(f"{qid}: hotspot must declare format_source: inferred")
        else:
            errors.append(f"{qid}: unknown type {t}")
        if q.get("code") and not q.get("code_lang"):
            errors.append(f"{qid}: code block without code_lang")
    return errors


def main():
    if not os.path.isdir(os.path.join(ROOT, "vendor/dbt-docs/website/docs")):
        print("VALIDATION FAILED: vendor/dbt-docs is missing, so no docs_ref can be verified.\n"
              "See 'Setting up a new machine' in README.md.", file=sys.stderr)
        return 1

    topics, questions = load()
    errors = validate(topics, questions)
    if errors:
        print("INVALID\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1

    by_type = Counter(q["type"] for q in questions)
    print(f"OK  {len(questions)} questions across {len(by_type)} formats")
    for t, n in by_type.most_common():
        print(f"    {n:>3}  {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
