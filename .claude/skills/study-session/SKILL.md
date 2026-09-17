---
name: study-session
description: Run a focused study session on one exam topic — builds or extends the topic note from the official docs, then drills it with new practice questions. Use when studying for the dbt Analytics Engineering Certification and no specific question was asked.
---

# Study session

One session covers **one topic** (or a slice of one — topic 01 has 14 sub-skills and should be
split across sessions).

## 1. Pick the target

If the user named a topic, use it. Otherwise read `exam/topics.yml` and `progress.yml` and pick
by this order:

1. any sub-skill with `confidence: weak`;
2. any sub-skill with `seen: 0` (never drilled);
3. the sub-skill with the oldest `last_seen`.

State the choice and why in one line, then confirm before proceeding.

## 2. Teach it

Read the relevant docs via the `dbt-docs-lookup` procedure, plus the resources listed for that
checkpoint in `exam/learning-path.md`.

Write or extend `notes/<topic-slug>.md`. Structure per sub-skill:

```markdown
## <subskill-id> — <sub-skill name>

**What it is.** Two or three sentences, no filler.

**Syntax / config.** The real snippet from the docs.

**Exam angles.** What the exam is likely to probe: the distinctions, the defaults,
the flag that changes behaviour, the classic wrong answer.

**Gotchas.** Version-specific behaviour, things that differ from intuition.

Source: vendor/dbt-docs/website/docs/...
```

Rules for the note:
- English, slim, no narrative, no progress-tracking prose.
- Every claim traceable to a doc path.
- Prefer a table or a snippet over a paragraph.
- Do not pad with content outside the official outline in `exam/topics.yml`.

## 3. Drill it

Write 5–10 **original** questions into `exams/bank/<topic-slug>.yml`, using the schema documented
in the repo `CLAUDE.md`. Vary the `type` field across the six real exam formats — not everything
is multiple choice.

Then run them past the user one at a time, without revealing the answer up front (same discipline
as `mock-exam`). Deliver each question through the channel its `type` calls for — see
**Question delivery** in `mock-exam`: `multiple-choice` and `domc` go through `AskUserQuestion`
with confidence captured in the same call, the other four formats stay as chat text.

Update `progress.yml` for the sub-skills touched.

## 4. Close

Report in three lines:
- what got covered;
- accuracy on the drill;
- the recommended next target.

Do not commit unless the user asks. If they do, the commit message is in PT-BR.
