---
name: mock-exam
description: Administer a practice exam for the dbt Analytics Engineering Certification from the local question bank, grade it, and record the result. Use when the user wants a simulado, practice test, mock exam, or to check how ready they are.
---

# Mock exam

Administer a practice exam, grade it, and persist the result.

## Modes

| Mode | Size | Time | Scope |
|---|---|---|---|
| `full` | 65 questions | 2 h | All topics — mirrors the real exam |
| `quick` | 10–15 questions | untimed | One topic or a set of weak sub-skills |
| `weak` | 10–20 questions | untimed | Only sub-skills with `confidence: weak` or low accuracy |
| `diagnostic` | 1 per sub-skill (31) | untimed | Breadth-first gap finding, run before studying |

Default to `quick` and ask which mode if unclear.

`diagnostic` is the pre-study baseline: exactly one question per sub-skill in `exam/topics.yml`
(31 of them today),
so every area gets probed once. Expect a low score — its job is to locate gaps, not to measure
readiness. Save `full` for readiness checks later, once studying is underway.

## 1. Assemble

Read `exams/bank/*.yml` and `progress.yml`.

- Draw across topics in proportion to their sub-skill count (`exam/topics.yml`), so topic 01
  dominates a `full` exam the way it dominates the real one.
- Oversample sub-skills that are `weak`, unseen, or stale.
- Avoid questions whose `id` appears in the three most recent `exams/attempts/*.yml`.
- Mix `type` values — do not serve 65 multiple-choice questions.

If the bank cannot fill the requested size, say so and offer to run smaller or to generate the
missing questions first via `study-session`.

## 2. Administer

**Never reveal the answer, the explanation, or the `docs_ref` while the exam is in progress.**
You can see them in the bank; the user cannot.

- One question at a time. Number them (`Question 7 of 15`).
- Present the stem and options exactly as written. No hints, no narrowing, no tone that flags
  the correct option.
- Deliver the question in the format its `type` calls for — see **Question delivery** below.
- **Capture confidence with every answer**: `alta` (sure), `média` (leaning), `chute` (guessing).
  If the user omits it, ask once, then default to `média` if they skip again — do not nag on
  every question.
- Accept the answer, acknowledge it neutrally ("Recorded."), move on. No per-question feedback.
- For `full` mode, note the start time and warn at the 1 h and 1 h 45 min marks.
- If the user asks to stop early, grade what was answered and mark the attempt `partial: true`.

### Question delivery

Two channels, chosen by `type`.

| `type` | Channel |
|---|---|
| `multiple-choice`, `domc` | `AskUserQuestion` — clickable options |
| `fill-in-blank`, `matching`, `build-list`, `hotspot` | Plain chat text |

The split is a tool constraint, not a preference: `AskUserQuestion` takes 2–4 options per question,
so only these two formats survive it intact. Forcing `hotspot` into four candidate lines, or
`matching` into a chain of picks, makes the question easier than the real thing. Do not do it.

**`multiple-choice`** — one `AskUserQuestion` call carrying two questions:

1. the stem, with each option's letter as the `label` and the option text as the `description`;
2. confidence — `alta`, `média`, `chute`, in that order.

Put the `code` block (when present) and the numbered question header in the message text above the
call, not inside the option labels. Never reorder options or reword them to fit.

**`domc`** — one `AskUserQuestion` call per option presented, `Sim` / `Não`, following the domc
rule that the item terminates as soon as the user endorses a distractor. Ask confidence **once**,
after the item resolves — not per option.

**The four text formats** — present as before and accept a typed answer, asking for confidence
alongside it (e.g. `run_results.json / alta`).

## 3. Grade

Score 1 point per correct answer, 0 otherwise — same as the real exam. Report:

- **Score**: `X/Y (Z%)` and **PASS / FAIL** against the 65% cut line;
- a per-topic breakdown table;
- for each miss: the correct answer, the explanation, and the `docs_ref` path;
- **the confidence quadrants** (see below);
- the two or three sub-skills to attack next.

### Confidence quadrants

Raw accuracy hides two failure modes. Always report this matrix:

| | Correct | Wrong |
|---|---|---|
| **alta** | Mastered — skip in study planning | **Misconception — highest priority** |
| **média** | Solid but unconsolidated | Normal gap |
| **chute** | Lucky — treat as unknown, not as mastered | Known gap |

Priority order for what to study next:

1. **alta + wrong** — a confidently held false belief. These do the most damage on the real exam
   because nothing signals to the candidate that they should check.
2. **chute + correct** — inflates the score while hiding a gap. Never treat as mastered.
3. **chute/média + wrong** — ordinary gaps, studied in topic order.
4. **média + correct** — needs consolidation, not discovery.

Call out the count in each quadrant explicitly, and name every `alta + wrong` sub-skill.

## 4. Persist

Write `exams/attempts/YYYY-MM-DD-<mode>.yml`:

```yaml
date: 2026-09-15
mode: quick
partial: false
score: 11
total: 15
percent: 73.3
passed: true
answers:
  - id: mat-001
    subskill: 01-11
    given: [b]
    correct: false
    stated_confidence: alta      # alta | media | chute
    quadrant: misconception      # mastered | misconception | solid | gap | lucky
```

Then update `progress.yml`: increment `seen` and `correct`, set `last_seen` to today, and set
`confidence`:

- any `alta + wrong` answer → `weak`, regardless of accuracy — a misconception outranks the ratio;
- a `chute + correct` answer does **not** raise confidence above `unknown`;
- otherwise apply the accuracy thresholds documented at the top of `progress.yml`.

Do not commit unless the user asks. If they do, the commit message is in PT-BR.
