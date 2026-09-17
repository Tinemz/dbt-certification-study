#!/usr/bin/env python3
"""Print the current state of study. Run this first in any new session.

Reads progress.yml, exams/attempts/*.yml and the question bank. Derives
everything -- nothing here is a stored snapshot that can go stale.

    python3 status.py
"""
import datetime
import glob
import os
import sys
from collections import Counter

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
EXAM_DATE = datetime.date(2026, 9, 30)
CUT = 65

PHASES = [
    (1, 3, "Topics 07 and 02", "Weakest at diagnostic; only 5 sub-skills between them", ["07", "02"]),
    (4, 6, "Topics 04 and 06 + the misconceptions", "Thinnest coverage; misconceptions rank first", ["04", "06"]),
    (7, 10, "Topics 01 and 05", "Largest share of the exam; consolidation, not discovery", ["01", "05"]),
    (11, 12, "Full 65-question mock + review", "First real readiness measurement", []),
    (13, 14, "Second mock + remaining weak spots", "", []),
    (15, 15, "Buffer / exam day", "", []),
]
PLAN_START = datetime.date(2026, 9, 15)


def rel(p):
    return os.path.join(ROOT, p)


def bar(n, total, width=22):
    filled = 0 if not total else round(width * n / total)
    return "#" * filled + "." * (width - filled)


def main():
    if not os.path.isdir(rel("vendor/dbt-docs/website/docs")):
        print("!! vendor/dbt-docs is missing -- technical answers cannot be grounded.")
        print("   See 'Setting up a new machine' in README.md.\n")

    progress = yaml.safe_load(open(rel("progress.yml")))["subskills"]
    topics = yaml.safe_load(open(rel("exam/topics.yml")))["topics"]
    tname = {t["id"]: t["name"] for t in topics}

    questions = []
    for f in sorted(glob.glob(rel("exams/bank/*.yml"))):
        questions += yaml.safe_load(open(f))
    qcount = Counter(q["subskill"] for q in questions)

    today = datetime.date.today()
    left = (EXAM_DATE - today).days
    day_n = (today - PLAN_START).days + 1

    print("=" * 66)
    print("  dbt Analytics Engineering Certification -- study status")
    print("=" * 66)
    print(f"  Target exam date : {EXAM_DATE}  ({left} days away)" if left >= 0
          else f"  Target exam date : {EXAM_DATE}  (PASSED {-left} days ago)")

    phase = next((p for p in PHASES if p[0] <= day_n <= p[1]), None)
    if phase:
        print(f"  Plan day {day_n} of 15  ->  {phase[2]}")
        if phase[3]:
            print(f"                          {phase[3]}")
    elif day_n < 1:
        print(f"  Plan starts {PLAN_START}")
    else:
        print(f"  Plan day {day_n} -- past the 15-day window in STUDY-PLAN.md")

    # ---- attempt history -------------------------------------------------
    print("\n  ATTEMPTS")
    attempts = []
    for f in sorted(glob.glob(rel("exams/attempts/*.yml"))):
        attempts.append(yaml.safe_load(open(f)))
    if not attempts:
        print("    none yet -- run a diagnostic in the exam app")
    for a in attempts:
        lucky = sum(1 for x in a.get("answers", []) if x.get("quadrant") == "lucky")
        quads = a.get("quadrants") or Counter(x.get("quadrant") for x in a.get("answers", []))
        lucky = lucky or quads.get("lucky", 0)
        adj = round(100 * (a["score"] - lucky) / a["total"], 1)
        flag = "PASS" if a["percent"] >= CUT else "under"
        note = "  (reconstructed)" if a.get("reconstructed") else ""
        print(f"    {a['date']}  {a['mode']:<10} {a['score']:>2}/{a['total']:<3} "
              f"{a['percent']:>5}%  {flag:<5}  adjusted {adj}%{note}")
    if attempts:
        print("    adjusted = score minus lucky guesses. Plan against that number.")

    # ---- weak sub-skills -------------------------------------------------
    order = {"weak": 0, "unknown": 1, "ok": 2, "strong": 3}
    weak = sorted(
        (k for k, v in progress.items() if v["confidence"] in ("weak", "unknown")),
        key=lambda k: (order[progress[k]["confidence"]], k),
    )
    print(f"\n  NEEDS WORK  ({len(weak)} of {len(progress)} sub-skills)")
    for k in weak:
        v = progress[k]
        acc = f"{v['correct']}/{v['seen']}" if v["seen"] else "unseen"
        print(f"    {k}  {v['confidence']:<8} {acc:<8} {qcount[k]}q   {v['name'][:52]}")

    # ---- topic coverage --------------------------------------------------
    print("\n  TOPIC COVERAGE  (confidence across sub-skills)")
    for t in topics:
        subs = [s["id"] for s in t["subskills"]]
        good = sum(1 for s in subs if progress[s]["confidence"] in ("ok", "strong"))
        nq = sum(qcount[s] for s in subs)
        print(f"    {t['id']}  {bar(good, len(subs))}  {good}/{len(subs)} solid   "
              f"{nq:>2}q   {tname[t['id']][:40]}")

    print(f"\n  BANK  {len(questions)} questions")
    fmt = Counter(q["type"] for q in questions)
    print("    " + "  ".join(f"{k} {v}" for k, v in fmt.most_common()))

    # Order by the plan's current phase, not alphabetically: the phase decides
    # which topics matter now, and weak beats unknown inside that.
    focus = phase[4] if phase else []
    ranked = sorted(weak, key=lambda k: (
        0 if progress[k]["topic"] in focus else 1,
        order[progress[k]["confidence"]],
        k,
    ))
    print("\n  NEXT")
    if not weak:
        print("    1. No weak sub-skills left -- run a full 65-question mock")
    else:
        top = ranked[:3]
        why = f" (phase focus: topics {', '.join(focus)})" if focus and any(
            progress[k]["topic"] in focus for k in top) else ""
        print(f"    1. Study: {', '.join(top)}{why}")
        for k in top:
            print(f"         {k}  {progress[k]['name'][:56]}")
        print("    2. Then ask for a 'weak' drill to re-test them")
    print("    3. Every drill is graded and recorded in exams/attempts/")
    print("\n  Read STUDY-PLAN.md for the full 15-day sequence.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
