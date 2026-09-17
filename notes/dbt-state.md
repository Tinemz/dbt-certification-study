# Topic 07 — Leveraging the dbt state

2 sub-skills. Smallest topic on the exam, and the one that interlocks most with topics 04 and 06.
All paths below are relative to `vendor/dbt-docs/website/docs/`.

---

## 07-01 — Understanding state and state selection

**What it is.** dbt operations are **stateless and idempotent**: a run does not need to know about
any other run. But dbt *writes* state as **artifacts**, and a later invocation can read them by
pointing `--state` at their directory. State enables three things and nothing else:

| Feature | What state gives it |
|---|---|
| `state:` selector | Compare current project **code** against the manifest → new / modified nodes |
| Deferral (`--defer`) | Resolve `ref()` for unselected, unbuilt upstream nodes to the state environment |
| `dbt clone` | Clone nodes based on their location in the state manifest |

`state` selector + deferral together = **Slim CI**.

Source: `reference/node-selection/state-selection.md`

### Artifacts that carry state

| Artifact | Produced by | Feeds |
|---|---|---|
| `manifest.json` | commands that read the project | `state:` selector, `--defer`, `dbt clone` |
| `run_results.json` | `run`, `test`, `build`, `seed` | `result:` selector, `dbt retry` |
| `sources.json` | `dbt source freshness` | `source_status:` selector |

Source: `reference/artifacts/dbt-artifacts.md`, `reference/node-selection/configure-state.md`

### Flags and env vars

```shell
dbt run --select "state:modified+" --defer --state path/to/artifacts
```

| Flag | Env var (**1.11+**) | Env var (≤1.10) | Type |
|---|---|---|---|
| `--state` | `DBT_ENGINE_STATE` | `DBT_STATE` | path |
| `--defer` | `DBT_ENGINE_DEFER` | `DBT_DEFER` | boolean |
| `--defer-state` | `DBT_ENGINE_DEFER_STATE` | `DBT_DEFER_STATE` | path (optional) |

- Flag beats env var when both are set.
- `--defer-state` unset → deferral falls back to `--state`.
- Deferral requires **both** `--defer` and `--state`.
- `--state` artifacts must be schema-compatible with the running dbt version.
- Old syntax `DBT_ARTIFACT_STATE_PATH` / `DBT_DEFER_TO_STATE` deprecated in v1.5.

Source: `reference/node-selection/configure-state.md`, `reference/node-selection/defer.md`

### The `state` selector family

| Selector | Selects |
|---|---|
| `state:new` | No node with the same `unique_id` in the comparison manifest |
| `state:modified` | All new nodes **plus** any change to an existing node |
| `state:old` | A node with the same `unique_id` exists in the manifest |
| `state:unmodified` | All existing nodes with no changes |

`state:modified` subselectors (no subselectors exist for `old` / `unmodified`):

| Subselector | Detects |
|---|---|
| `.body` | Node body — model SQL, seed values |
| `.configs` | Any config, **excluding** `database` / `schema` / `alias` / `tags` / `meta` |
| `.relation` | `database` / `schema` / `alias` |
| `.persisted_descriptions` | `description`, only if `persist_docs` is enabled at that level |
| `.macros` | Upstream macros, directly or indirectly called |
| `.contract` | Contract `columns` `name` / `data_type`; removing or retyping a column errors |

`state:modified` also catches `access`, `deprecation_date`, `latest_version`, source `freshness` /
`quoting`, exposure `maturity`.

Source: `reference/node-selection/methods.md`

### Deferral

`--defer` makes dbt resolve `ref()` (and, in **1.11+**, `function()`) from the state manifest
**only if both**:

1. the node is **not** among the selected nodes, **and**
2. it does **not** exist in the database — or `--favor-state` is passed.

`--favor-state` prioritizes the state definition, except for nodes that are themselves selected.
Ephemeral models are **never** deferred — they are passthroughs for other `ref` calls.

Source: `reference/node-selection/defer.md`

### `result:` and `source_status:`

```shell
dbt build --select "1+result:fail" --state path/to/artifacts   # failed tests + their parents
dbt build --select "1+result:fail+" --state path/to/artifacts  # ...and everything downstream
dbt run --select "result:error+" "state:modified+" --state path/to/artifacts
```

| `result:<status>` | model | seed | snapshot | test |
|---|---|---|---|---|
| `error` | ✅ | ✅ | ✅ | ✅ |
| `success` | ✅ | ✅ | ✅ | |
| `skipped` | ✅ | | ✅ | ✅ |
| `fail` / `warn` / `pass` | | | | ✅ |

`source_status:fresher+` needs `sources.json` in **both** states — `dbt source freshness` must have
run in the previous job *and* again now.

Source: `reference/node-selection/configure-state.md`

### `dbt clone` vs deferral

| | Deferral | `dbt clone` |
|---|---|---|
| Creates warehouse objects | No | Yes |
| Cost | Cheaper, simpler — the default choice | Compute + storage |
| Zero-copy clone | n/a | Snowflake, Databricks, BigQuery; **pointer view** elsewhere |
| Reaches tools outside dbt (BI) | No | Yes |

- `dbt clone` will **not** recreate pre-existing relations in the target — use `--full-refresh`.
- Classic use: clone modified incremental models as the first CI step to avoid `full-refresh` cost.
- Raise `--threads`; clone statements are independent.

Source: `reference/commands/clone.md`

### Exam angles

- `--state` points at artifacts from a **previous invocation**, never at the current run's
  `target/` and never at a live warehouse or a git ref.
- `state:modified` compares **code**, not warehouse data.
- The `+` in `state:modified+` is **descendants**; downstream breakage is the point of Slim CI.
- Deferral needs `--defer` **and** `--state`, both.
- 1.11 renamed the env vars to the `DBT_ENGINE_*` prefix.

### Gotchas

- **`tags` and `meta` never trigger `state:modified`** — metadata only, resource level *and* column
  level. Intentional. `description` does, but only under `persist_docs`.
- **Seeds**: <1 MiB compared by file hash; ≥1 MiB compared by **file path only**, with a warning.
- **Macros**: anything depending on a changed macro, at any depth, is marked modified.
- **Vars / env vars**: dbt cannot trace the lineage, so a changed `var` does not by itself mark a
  model modified — only if it lands in a different config.
- `dbt test -s state:modified` picks up both tests selecting from modified resources *and* tests
  that are themselves new or modified — so a new test on an unbuilt model needs deferral.
- Deferred `relationships` tests query **across environments** — sampled dev data vs full prod
  makes referential-integrity results meaningless. Common fix: `--exclude test_name:relationships`.
- Behavior flag `state_modified_compare_more_unrendered_values` (1.9+) reduces false positives from
  env-aware logic.

Source: `reference/node-selection/state-comparison-caveats.md`

**Not in the exam outline:** managed **dbt State** (`dbt-state explain`, the Explain tab) is a dbt
platform product, distinct from local `--state`. `exam/topics.yml` names only state selection and
retry. Source: `reference/commands/state-explain.md`

---

## 07-02 — Using dbt retry

**What it is.** `dbt retry` re-executes the **last invocation from its point of failure**, reading
`run_results.json`. It never re-runs successful upstream nodes.

```shell
dbt retry
dbt retry --state path/to/previous/run   # defaults to the target directory
```

**Supported commands:** `build`, `compile`, `clone`, `docs generate`, `seed`, `snapshot`, `test`,
`run`, `run-operation`.

**Core flags (1.11):** `--threads`, `--vars`, `--target`, `--profile`, `--profiles-dir`,
`--project-dir`, `--target-path`, `--state`, `--full-refresh`.

### Exam angles

| Situation | `dbt retry` does |
|---|---|
| Failure **before any node ran** (connection, permission error) | **Nothing** — no recorded nodes. Check `run_results.json`, re-run the full job manually |
| Previous command **succeeded** | Finishes as **no operation** — "Nothing to do" |
| Some nodes ran, then a node failed | Re-executes from that failure point onward |
| Error **not fixed** before retrying | Fails again at the same node — retry is idempotent |

- **`dbt retry` reuses the prior command's selection**, including `--select`, `--exclude` and
  `--selector`. On dbt Core you **cannot** override them. (Overriding selectors on retry is a
  Fusion / v2.0 feature — not 1.11.)
- `--state` here means "directory containing `run_results.json`", **not** a comparison manifest.
  Same flag, different job than in state selection.

### Gotchas

- Retry is driven by `run_results.json`, so any command that does not produce one gives it nothing
  to work from.
- Skipped downstream nodes from the failed run are part of what retry picks back up — the count in
  the final `Done.` line reflects the whole original run, not just the retried nodes.

Source: `reference/commands/retry.md`
