# dbt Analytics Engineering Certification — Study Repo

Preparation for the **dbt Analytics Engineering Certification Exam** (dbt Core 1.11).

The [official study guide][guide] defines *what is on the exam*. The official dbt documentation —
vendored locally — defines *what the correct answer is*. Claude works on top of both: it explains
topics, writes notes, drills original practice questions, and tracks performance per sub-skill.

No technical answer here is written from memory. Every claim and every practice question cites a
file in the vendored docs.

[guide]: https://www.getdbt.com/dbt-assets/certifications/dbt-certificate-study-guide-version-1-11

## Why this exists

Studying for this exam means answering two questions over and over: *what is actually on it*, and
*what does dbt actually do*. Each has exactly one honest source — the official outline and the
official documentation. Everything else, including an LLM answering from memory, is a guess in a
confident tone.

So the sources are wired into the workflow rather than trusted to discipline:

- **Nothing is answered from memory.** The dbt docs are vendored locally and every question carries
  a `docs_ref` into them. `validate_bank.py` refuses to pass a question whose reference does not
  resolve, so a broken source fails loudly instead of quietly teaching the wrong thing.
- **The questions are original.** The guide's own 10 samples are © dbt Labs and never enter the
  bank — and memorising 10 questions would not help anyway.
- **Confidence is recorded with every answer**, because a lucky guess and real knowledge score the
  same. The report separates them, and a confident wrong answer outranks everything else in the
  plan: nothing signals you to go check it.
- **The plan comes from a diagnostic**, not from a template. `/onboarding` measures first, then
  orders the topics.

Built while preparing for the exam, and kept working after it.

## What is in here today

| | |
|---|---|
| Practice questions | 93, across all six exam formats |
| Sub-skill coverage | all 31 have at least one question; 18 have only two |
| Topic notes | 3 of 7 topics written (01, 02, 07) |

The thin spots are real and worth knowing before you clone: a `weak` drill on a sub-skill with two
questions will start repeating itself. Both numbers grow as `/study-session` runs — it writes new
questions into the bank as it goes.

## Exam at a glance

| Item | Value |
|---|---|
| Length | 65 questions, 2 hours |
| Passing score | 65% — shown immediately after completion |
| Scoring | 1 point per correct answer, no negative marking, all questions weighted equally |
| Version | dbt Core 1.11 |
| Format | Online proctored via Talview, Caveon web browser |
| Price | USD 200 per attempt — retakes are paid |
| Language | English and Japanese |
| Expiration | 2 years after the date awarded |

An undisclosed number of unscored research questions is mixed in, indistinguishable from the
scored ones. Rescheduling and cancellation are free up to 24 hours before; no-shows are not
refunded. Recommended background: SQL proficiency and 6+ months of hands-on dbt experience.

Registration: https://pages.talview.com/dbtlabs/certifications/ ·
Certification questions: certification@dbtlabs.com · Accessibility: accessibility@dbtlabs.com

## Topics

| # | Topic | Sub-skills |
|---|---|---|
| 01 | Developing and optimizing dbt models | 14 |
| 02 | Managing dbt models governance | 3 |
| 03 | Debugging data modeling errors | 5 |
| 04 | Troubleshooting and optimizing dbt pipelines | 2 |
| 05 | Implementing dbt tests | 3 |
| 06 | Implementing and maintaining external dependencies | 2 |
| 07 | Leveraging the dbt state | 2 |

The official guide publishes no percentage weights. The full outline lives in
[`exam/topics.yml`](exam/topics.yml) — nothing outside it is on the exam.

## Learning path

The route dbt Labs recommends in the [study guide][guide], mapped to the topics above.

| Checkpoint | Focus | Covers |
|---|---|---|
| 0 · Prerequisites | SQL (joins, aggregations, CTEs, window functions) and git (branching, PRs) | — |
| 1 · Build a foundation | Materializations, incremental models, snapshots, seeds, Jinja and macros, packages, Python models, the `--empty` and `--sample` flags | Topic 01 |
| 2 · Govern and debug | Contracts, model versions, constraints, model access, reading dbt logs, `dbt compile`, behavior change flags | Topics 02, 03 |
| 3 · Resilient pipelines at scale | Generic/singular/custom/unit tests, exposures, source freshness, `dbt clone`, deferral, state selection, `dbt retry` | Topics 04–07 |

Each checkpoint in the guide lists dbt Studio courses, documentation pages, commands, and
readings. The full breakdown is in [`exam/learning-path.md`](exam/learning-path.md).

## Layout

```
exam/            topics outline + learning path, distilled from the official guide
notes/           topic summaries grounded in the docs, one file per topic slug
exams/bank/      practice question bank -- original questions, six exam formats
exams/attempts/  graded attempt history
progress.yml     per-sub-skill performance -- the only performance record
plan.yml         your plan's phases, written by /onboarding (generated, gitignored)
status.py        derives the current state; the entry point for a session
validate_bank.py validates the question bank; run after editing it
STUDY-PLAN.md    your plan in prose -- the one in this repo is an example
vendor/          vendored dbt docs (gitignored, see setup)
```

## First run

After the setup below, start with:

```
/onboarding
```

It asks how much dbt you have actually shipped, how much time you have and whether the exam is
booked, then runs a diagnostic — one question per sub-skill, before any studying. Out of that come
two files: `plan.yml`, which `status.py` reads, and your own `STUDY-PLAN.md`, which replaces the
example in this repo.

The plan is ordered by what the diagnostic found, not by the topic order in the guide: worst
adjusted accuracy first, with any confidently-wrong answer promoted to the first phase.

## How to use it

Ask in plain language, or invoke a skill directly:

- `/onboarding` — build (or rebuild) your study plan.
- `/study-session` — study a topic: builds the note from the docs, then drills it.
- `/mock-exam` — practice exam (`quick`, `weak`, `diagnostic`, or a full 65-question run), graded
  and recorded.
- `/dbt-docs-lookup` — one-off dbt question answered from the official docs, with the source path.

Questions are delivered one at a time in the chat, in all six exam formats: multiple choice, fill
in the blank, matching, hotspot, build list, and DOMC.

Every answer also records how confident you were — `alta`, `média` or `chute`. That is what
separates the two failure modes raw accuracy hides: a confident wrong answer (a misconception, the
most dangerous kind, because nothing signals you to check) and a lucky guess that scored as
knowledge.

## Setting up a new machine

```bash
# 1. the repo
git clone https://github.com/Tinemz/dbt-certification-study.git
cd dbt-certification-study

# 2. python dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. the vendored dbt docs -- gitignored, ~19 MB via sparse checkout
git clone --filter=blob:none --no-checkout --depth 1 --branch current \
  https://github.com/dbt-labs/docs.getdbt.com.git vendor/dbt-docs
git -C vendor/dbt-docs sparse-checkout set website/docs website/snippets
git -C vendor/dbt-docs checkout current

# 4. confirm it all works
.venv/bin/python3 status.py
```

Step 3 is not optional: without it no answer can be grounded, and `status.py` warns you. The full
docs repo is 1.7 GB — the sparse checkout keeps it at ~19 MB. Refresh it with
`git -C vendor/dbt-docs pull`.

Commands spell out `.venv/bin/python3` on purpose: it works whether or not the virtualenv is
activated.

The official study guide is not in this repo — it is © dbt Labs. [Download it][guide] separately
if you want it alongside.

## Picking up where you left off

```bash
.venv/bin/python3 status.py
```

Prints the current plan phase, weak sub-skills ranked by what matters now, attempt history with
scores adjusted for lucky guesses, and what to study next. Everything is derived from
`progress.yml` and `exams/attempts/` — nothing stored that can go stale.

Then read [`STUDY-PLAN.md`](STUDY-PLAN.md) for the full sequence.

## Notes

- Study material is written in English on purpose — the exam is in English.
- Bank questions are original, written from the topics outline plus the official docs.
- The guide names six question formats but only illustrates multiple choice. Questions whose
  format shape is an inference are marked `format_source: inferred`.
- Commit messages are in PT-BR while the study material is in English. That split is deliberate.
- `progress.yml` ships with every counter at zero and `exams/attempts/` empty. Run a
  `diagnostic` first: it fills them in, and the plan in `STUDY-PLAN.md` reorders itself around
  what it finds.
