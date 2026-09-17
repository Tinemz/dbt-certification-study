---
name: dbt-docs-lookup
description: Answer a dbt technical question by grounding the answer in the locally vendored official dbt documentation. Use whenever a question about dbt behaviour, syntax, configs, commands, or flags comes up while studying for the certification — never answer dbt questions from memory.
---

# dbt docs lookup

Answer dbt questions from the **official documentation**, never from memory. The local clone at
`vendor/dbt-docs/website/docs/` is the primary source.

## Procedure

1. **Locate.** Grep the local clone before writing anything:

   ```bash
   grep -ril "<term>" vendor/dbt-docs/website/docs/ | head -20
   ```

   Useful entry points:

   | Looking for | Start at |
   |---|---|
   | Command behaviour and flags | `website/docs/reference/commands/`, `website/docs/reference/global-configs/` |
   | Model/source/test configs | `website/docs/reference/resource-configs/`, `website/docs/reference/resource-properties/` |
   | Concepts (materializations, snapshots, tests, contracts) | `website/docs/docs/build/` |
   | Node selection syntax | `website/docs/reference/node-selection/` |
   | Recommended patterns | `website/docs/best-practices/` |
   | Vocabulary | `website/docs/terms/`, `website/docs/sql-reference/` |

2. **Read** the matching file(s) in full enough context to be sure — not just the grep line.

3. **Answer** with:
   - the direct answer first, in English;
   - the relevant snippet or config example from the docs;
   - a **Source** line citing the repo-relative path, e.g.
     `Source: vendor/dbt-docs/website/docs/docs/build/incremental-models.md`.

4. **Version check.** The exam targets **dbt Core 1.11**. If the docs mark a feature as newer,
   deprecated, or Cloud-only, say so explicitly — it changes whether it is testable.

## When the local clone has no answer

Only then fall back to `WebFetch` on `docs.getdbt.com`. Mark the answer clearly:

> Not found in the local clone — answered from docs.getdbt.com (live).

Then suggest refreshing the clone:

```bash
git -C vendor/dbt-docs pull
```

## Hard rules

- No answer without a verified source path or an explicit live-docs marker.
- If the docs are ambiguous or contradict your expectation, say so rather than smoothing it over.
- Link the answer back to the exam: name the topic and sub-skill from `exam/topics.yml` it maps to.
- If the question exposes a gap, offer to record it — a note in `notes/<topic-slug>.md` or a new
  question in `exams/bank/<topic-slug>.yml`.
