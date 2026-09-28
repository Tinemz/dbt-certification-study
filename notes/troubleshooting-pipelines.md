# Topic 04 — Troubleshooting and optimizing dbt pipelines

2 sub-skills. Interlocks heavily with topic 07 (state) — every recovery mechanism here reads an
artifact written by a prior invocation.
All paths below are relative to `vendor/dbt-docs/website/docs/`.

---

## 04-01 — Troubleshooting and managing failure points in the DAG

**What it is.** When a node fails mid-DAG, dbt decides three things: what stops, what is skipped,
and what a later invocation can pick back up. Managing failure points means controlling that
propagation (severity, `--fail-fast`) and recovering efficiently (`dbt retry`, `result:` selectors)
instead of rebuilding the whole project.

### Failure propagation in `dbt build`

| Event | Effect on downstream |
|---|---|
| Model errors | Downstream models are skipped |
| Test on upstream resource **errors** | Downstream resources `SKIP` entirely |
| Test returns **warn** (`severity: warn`) | Nothing is blocked, nothing is skipped |

Multi-parent tests:

- Test whose parents depend on each other (e.g. `relationships` between `model_a` and `model_b`):
  blocks and skips children of the **most-downstream parent only** (`model_b`).
- Test with **independent** parents: a downstream node is skipped only if it depends on **all** of
  those parents.

`dbt build` runs in DAG order and writes a **single** `manifest.json` and a **single**
`run_results.json` covering models, tests, seeds and snapshots together.

Order per model under `dbt build`: unit tests → materialize the model → data tests. A model whose
unit tests fail is never materialized.

Source: `reference/commands/build.md`

### Severity — the lever that stops the skipping

| Config | Default | Effect |
|---|---|---|
| `severity` | `error` | `error` blocks downstream; `warn` does not |
| `error_if` | `!=0` | Threshold expression to raise an error |
| `warn_if` | `!=0` | Threshold expression to warn |

Evaluation order:

- `severity: error` → check `error_if` first; if unmet, fall through to `warn_if`; if that is unmet,
  the test passes.
- `severity: warn` → `error_if` is **skipped entirely**, straight to `warn_if`.

Promote warnings back to errors with `--warn-error` (all warnings, including Jinja warnings and
deprecations) or `--warn-error-options` (specific types only).

Source: `reference/resource-configs/severity.md`

### `--fail-fast` / `-x`

Global flag for `dbt run`, `dbt build`, `dbt test`. Exits immediately on the **first** failure and
**terminates the connections of still-running models**. Stops on run errors *and* test errors.
Env var: `DBT_FAIL_FAST`.

```text
$ dbt run -x --threads 1
FailFast Error in model model_1 (models/model_1.sql)
  Failing early due to test failure or runtime error
```

Source: `reference/global-configs/failing-fast.md`

### `dbt retry`

Re-executes the **last invocation from the point of failure**, reading `run_results.json`.

| Situation | Behaviour |
|---|---|
| Previous command succeeded | Finishes as **no operation** ("Nothing to do") |
| Failure happened before any node ran (connection/permission error) | Retries nothing — no recorded nodes; re-run the full job manually |
| Errors not fixed | Idempotent — fails again at the same node |

Supported commands: `build`, `compile`, `clone`, `docs generate`, `seed`, `snapshot`, `test`,
`run`, `run-operation`.

Core flags: `--threads`, `--vars`, `--target`, `--profile`, `--profiles-dir`, `--project-dir`,
`--target-path`, `--state`, `--full-refresh`. `--state` points at a directory containing a previous
`run_results.json`; it defaults to the target directory.

Source: `reference/commands/retry.md`

### `result:` selectors — targeted recovery

Requires a prior `run`, `test`, `build` or `seed` to have produced `run_results.json`, passed via
`--state`.

| `result:<status>` | model | seed | snapshot | test |
|---|---|---|---|---|
| `result:error` | ✅ | ✅ | ✅ | ✅ |
| `result:success` | ✅ | ✅ | ✅ | |
| `result:skipped` | ✅ | | ✅ | ✅ |
| `result:fail` | | | | ✅ |
| `result:warn` | | | | ✅ |
| `result:pass` | | | | ✅ |

```bash
dbt run  --select "result:error" --state path/to/artifacts
dbt build --select "1+result:fail"  --state path/to/artifacts   # models feeding the failed tests
dbt build --select "1+result:fail+" --state path/to/artifacts   # plus everything downstream
dbt run  --select "result:error+" "state:modified+" --defer --state path/to/artifacts
```

`result:fail` is **test-only**. Tests have no downstream nodes, so `result:fail+` returns the failed
test and nothing else — the `1+` prefix is what reaches the model that produced the failure.

Source: `reference/node-selection/methods.md`, `reference/node-selection/configure-state.md`

### Source-side failure points

`dbt source freshness` writes `sources.json`. A later invocation selects on it:

```bash
dbt source freshness                                            # must re-run to compare states
dbt build --select "source_status:fresher+" --state path/to/prod/artifacts
```

Source: `reference/node-selection/methods.md`

### Diagnosing before running

| Tool | What it checks |
|---|---|
| `dbt debug` | Database connection, `dbt_project.yml` validity, system env, dependencies, adapter versions |
| `dbt debug --connection` | Connection only — the sole flag supported in Studio IDE and platform CLI |
| `--empty` | Schema-only dry run: refs and sources limited to zero rows, SQL still executes against the warehouse |
| `--debug` | Debug-**level logging**, unrelated to the `dbt debug` command |

Source: `reference/commands/debug.md`, `reference/commands/build.md`

**Exam angles.**

- `dbt retry` vs `--fail-fast`: retry **resumes** a run; fail-fast **stops** one. `--fail-fast` never
  resumes anything.
- `dbt retry` vs `state:modified`: retry selects by **failure point**, `state:modified` by **code
  change**. A transient warehouse error changes no code.
- `result:fail` vs `result:error`: `fail` is a test verdict; `error` is any resource that errored.
- Why a downstream model is `SKIP` rather than `ERROR`: an upstream test errored, not the model.
- Turning a blocking test into a non-blocking one: `severity: warn`, not `--exclude`.
- A `dbt retry` that reports "Nothing to do" means the prior invocation **succeeded**.

**Gotchas.**

- `dbt retry` on **Core** reuses the prior invocation's selection and **cannot** be overridden with
  `--select` / `--exclude` / `--selector`. Narrowing the retry scope that way is a Fusion (v2.0+)
  capability — out of scope for a 1.11 exam.
- `on_error: continue` (letting downstream models run past a failed model) is **v1.12**. On 1.11 a
  failed model always skips its children.
- State env var renamed at **1.11**: `DBT_ENGINE_STATE` (was `DBT_STATE`); likewise
  `DBT_ENGINE_DEFER_STATE` (was `DBT_DEFER_STATE`).
- `--fail-fast` cancels in-flight queries; the run is left partially applied, so it is a debugging
  flag, not a safety mechanism.
- Retry without fixing the underlying error is idempotent — it will not "eventually pass".

Source: `reference/commands/retry.md`, `reference/resource-configs/on_error.md`,
`reference/node-selection/defer.md`, `reference/global-configs/failing-fast.md`
