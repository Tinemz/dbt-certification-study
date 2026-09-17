# dbt-certification-study — Claude instructions

Study repository for the **dbt Analytics Engineering Certification Exam** (dbt Core 1.11).
`README.md` describes the project and its layout; this file holds the operating rules.

---

## Start here, every session

1. Run `.venv/bin/python3 status.py` — plan phase, weak sub-skills, attempt history, what is next.
2. **If `plan.yml` does not exist, run the `onboarding` skill before anything else.** There is no
   plan yet, so no priority is trustworthy: `STUDY-PLAN.md` in a fresh clone is someone else's.
3. Read `STUDY-PLAN.md` for the sequence and the standing decisions.
4. Confirm `vendor/dbt-docs/` exists before answering anything technical. If it is missing, stop
   and point the user at "Setting up a new machine" in `README.md` — an ungrounded answer is worse
   than no answer here.

Never state the user's scores from memory. They change every attempt; `status.py` derives them.

---

## Sources of truth

| Question | Answer lives in |
|---|---|
| What is on the exam? | `exam/topics.yml` (7 topics, 31 sub-skills, from the official guide) |
| How does dbt actually behave? | `vendor/dbt-docs/website/docs/` (official docs, vendored) |
| Exam format, cut line, question types | `README.md` |
| What to study and in what order | `exam/learning-path.md` |
| How well is the user doing? | `progress.yml` (rendered by `status.py` — never read stale copies) |
| What to do next, and by when | `STUDY-PLAN.md` (prose) and `plan.yml` (phases, read by `status.py`) |

Never invent exam scope. If something is not in `exam/topics.yml`, it is not on the exam.

---

## Anchoring rule

**No technical answer and no practice question without a verified source in the vendored docs.**

- Grep `vendor/dbt-docs/website/docs/` before answering. Cite the repo-relative path.
- Every bank question carries a `docs_ref` pointing to a file that exists in the clone.
- Falling back to live `docs.getdbt.com` is allowed only when the clone has no answer, and the
  response must say so explicitly.

The exam targets **dbt Core 1.11**. Flag anything newer, deprecated, or dbt Cloud-only — it
changes whether the behaviour is testable.

---

## Question bank schema

`exams/bank/<topic-slug>.yml` is a list of questions. Common fields:

```yaml
- id: inc-001                 # unique, short prefix by theme
  topic: "01"                 # topic id from exam/topics.yml
  subskill: 01-11             # sub-skill id from exam/topics.yml
  type: multiple-choice       # see the six formats below
  stem: "..."
  explanation: "Why the right answer is right and the tempting wrong one is wrong."
  docs_ref: website/docs/docs/build/incremental-models.md
  code: |                     # optional: rendered above the stem with line numbers
    select * from {{ ref('stg_orders') }}
  code_lang: sql              # required whenever `code` is present: sql | yaml | text
  format_source: inferred     # see "Format grounding" below
```

Per-type fields:

| `type` | Extra fields |
|---|---|
| `multiple-choice` | `options: {a: …}` + `answer: [a]` (always a list) |
| `fill-in-blank` | `answer: [...]` accepted strings; graded case-insensitively, leading dashes and a trailing colon ignored. Optional `answer_note` |
| `matching` | `pairs: [{left, right}]` — `right` values must be unique |
| `build-list` | `sequence: [...]` in the correct order |
| `hotspot` | `code` + `code_lang` + `answer_line` (1-based) |
| `domc` | `domc_options: [{text, keyed}]` — needs at least one keyed and one distractor |

Run `.venv/bin/python3 validate_bank.py` after editing the bank. It validates all of the above
and exits non-zero on any violation, including a `docs_ref` that does not resolve.

---

## Format grounding

The official guide **names** six formats but **only illustrates multiple choice** — all 10 of its
sample questions are multiple choice, and page 2 states they "do not represent all question
formats."

So: `multiple-choice` is the only format whose shape comes from the guide. Any question whose
format shape is an inference carries **`format_source: inferred`**. This keeps the repo's "never
invent exam scope" rule honest at the format level too.

- `domc` — named in the guide; mechanics documented publicly by Caveon (options one at a time,
  YES/NO, terminates on endorsing a distractor). Not marked inferred.
- `fill-in-blank`, `matching`, `build-list` — named in the guide; mechanics unambiguous.
- **`hotspot`** — named in the guide, mechanics **not determinable**. Implemented as identifying a
  line in a code block, and marked `inferred`. In the dbt learning-path courses, code-block
  questions are answered by **choosing an option**, which may mean this shape never appears on the
  real exam. The content is valid practice either way.

The confirmed-real shape the guide does show (samples Q08, Q09) is a **code block plus options** —
that is the `code` field on a `multiple-choice` question, not a separate type.

Bank questions are **original**. The 10 official sample questions stay in the study guide and
never enter the bank — reproducing them here would both breach the copyright and turn the bank
into a memorisation aid for questions the real exam does not ask.

---

## Language

- **All study artifacts are written in English** — notes, questions, explanations, exam references.
  The exam is in English; the material should not require translation under time pressure.
- **Conversation follows the user's language** (PT-BR by default).
- **Commits, branches, and PR titles/descriptions are in PT-BR.** This deliberately contrasts with
  the English content — do not "fix" it either way.

---

## Writing style

Slim, precise, no prose, no ambiguity. No decision-making narrative and no progress-tracking text
inside notes — `progress.yml` is where progress lives.

---

## Skills

- **`onboarding`** — first run: questionnaire, time budget, diagnostic, then write the plan.
- **`study-session`** — study a topic: build the note from the docs, then drill it.
- **`mock-exam`** — administer, grade, and record a practice exam.
- **`dbt-docs-lookup`** — answer a one-off dbt question, grounded in the vendored docs.

---

## Action gate

**Act without asking** — reading, grepping, running `status.py` or `validate_bank.py`.

**Plan and confirm first** — say what will change and why, then wait for a yes:

- editing `.claude/skills/`, `status.py`, `validate_bank.py`, or any config file;
- anything under `exam/` (read-only: the official outline and its distilled references);
- anything that leaves the machine — pushing, opening a PR, publishing anything.

**An explicit request is the confirmation.** If the user asked for it, do it — do not re-ask.

**Exception specific to this repo:** during an active `study-session` or `mock-exam`, writing to
`notes/`, `exams/bank/`, `exams/attempts/`, and `progress.yml` is the skill doing its job — no
separate gate per file.

Commits are never automatic. Commit only when asked.

---

## Copyright

The official study guide and its 10 sample questions are © 2026 dbt Labs and are **not** in this
repo. Download the guide from the link in `README.md` if you want a local copy, keep it untracked,
and never quote it into the question bank — the bank is original by design.
