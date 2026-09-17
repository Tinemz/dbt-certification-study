# Study Plan — example: 15 days to a booked exam

> **This file is an example, kept in the repo to show the shape of a plan.** It came from a real
> 15-day run with the exam already booked. Running `/onboarding` overwrites it with yours, built
> from your experience, your available time and your own diagnostic — a different plan, in a
> different order, over a different number of days.

Target exam date: **2026-09-30**. Plan day 1 is 2026-09-15.

This is the one file in the repo whose purpose *is* progress tracking, so it carries the sequence
and standing state that everything else deliberately avoids. Live numbers are never written here —
run `.venv/bin/python3 status.py` for those.

---

## Next session: start here

1. `.venv/bin/python3 status.py` — current phase, weak sub-skills, attempt history.
2. Study the sub-skills it names under **NEXT**, using the `study-session` skill.
3. Re-test them with a `weak` drill (`/mock-exam`), which records the attempt as it grades.

If `status.py` warns that `vendor/dbt-docs` is missing, fix that first — no technical answer is
trustworthy without it. See "Setting up a new machine" in `README.md`.

---

## How the order is set

Day 1 is a `diagnostic` — one question per sub-skill, before any studying. It produces two numbers
per attempt: the raw score, and the score adjusted for lucky guesses. **The adjusted number is the
one to plan against**, because an answer that was a guess carries no knowledge even when it scores.

The phase order below is what that diagnostic produced. Re-running it on a fresh clone will
produce a different order, and the plan should follow yours, not this one.

**A passing practice score is not readiness.** The questions here are original and their difficulty
is not calibrated against the real exam. Treat anything under 80% on a full mock as not ready.

---

## The sequence

The backbone follows the official learning path checkpoints in `exam/learning-path.md`. Priority
*within* each phase comes from `progress.yml`, so it adapts as performance changes.

### Days 1–3 · Topics 07 and 02

The diagnostic ranked these lowest, and they are the cheapest to close — 5 sub-skills between them.

- **07** state and state selection, `dbt retry`. Covers `--state`, deferral, Slim CI, `dbt clone`
  vs deferral. These four interlock; study them as one unit.
- **02** contracts, model versions, constraints — the guide treats governance as one block, so the
  phase does too.
- Learning path: Checkpoint 2 (govern and debug) + Checkpoint 3 (state, clone, retry).

### Days 4–6 · Topics 04 and 06, plus the misconceptions

- **04** DAG failure points, `dbt clone`. **06** exposures, source freshness.
- Then every misconception the diagnostic surfaced — answered confidently and wrongly. Highest
  priority of anything in a plan, because a confident wrong answer gives no signal to check.
- Learning path: Checkpoint 3.

### Days 7–10 · Topics 01 and 05

The largest share of the exam — topic 01 alone is 14 of 31 sub-skills. For someone already working
in dbt this is usually consolidation rather than discovery, so it sits late. Do not spend days here
on sub-skills already marked `strong`.

- Learning path: Checkpoint 1 (materializations, incremental, snapshots, Jinja, packages, Python
  models) + Checkpoint 3 (testing).

### Days 11–12 · Full mock and review

- Run the **full** mode: 65 questions, 2 hours, timed.
- **Decision point.** Below 75%, remaking the booking beats sitting the exam — a retake costs
  another USD 200. This is a recommendation, not a rule.
- Review every miss against its `docs_ref`.

### Days 13–14 · Second mock and cleanup

- A second full mock, then close whatever is still weak.
- Re-read the 10 sample questions in the official study guide (linked from `README.md`) — they are
  the only calibrated signal available for real exam difficulty. They are © dbt Labs and are not
  reproduced in this repo.

### Day 15 · Buffer

Rest, or absorb a slipped day. Do not study new material the day before.

---

## Booking

The exam is online proctored through Talview: https://pages.talview.com/dbtlabs/certifications/

Check slot availability early — a plan does not survive a booking that cannot be made in time.
Rescheduling is free up to 24 hours before; no-shows are not refunded.

---

## Rules that keep this honest

- **Declare confidence truthfully**, including "chute". The quadrant analysis is the only thing
  that separates real knowledge from a lucky guess — the same sub-skill can score as a lucky guess
  in one attempt and as a confident wrong answer in the next, and only the confidence data shows
  it.
- **Record every drill in `exams/attempts/`**, or `progress.yml` drifts and the plan starts
  aiming at the wrong sub-skills.
- **A passing practice score is not readiness.** 12-question drills move ±8% per question.
