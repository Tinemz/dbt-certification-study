# Topic 01 — Developing and optimizing dbt models

14 sub-skills. The largest topic on the exam.
All paths below are relative to `vendor/dbt-docs/website/docs/`.

---

## 01-01 — Identifying and verifying any raw object dependencies

**What it is.** A source maps to one **database + schema** pair. Tables live under that source's
`tables:` list. `{{ source('name', 'table') }}` resolves to the physical object.

**Counting rule (exam favourite).** Same database + schema across N table references → **1 source
with N tables**, not N sources.

```yaml
sources:
  - name: jaffle_shop
    database: raw            # defaults to the target database
    schema: public           # defaults to the source name
    tables:
      - name: orders
        identifier: raw_orders   # use when the warehouse name differs
```

**Exam angles.**
- `schema` is what dbt uses to resolve the physical location; `name` is just the dbt-side label.
- `identifier` overrides the physical table name.
- To verify a suspect source: check `sources.yml` properties first, `dbt source freshness` second.

Source: `docs/build/sources.md`

---

## 01-02 — Understanding core dbt materializations

| Materialization | Builds | Use when |
|---|---|---|
| `view` | `create view` each run | Light transforms, always-fresh reads, low storage |
| `table` | `create table` each run, full rebuild | Read performance matters, rebuild cost is acceptable |
| `incremental` | Table, appended/merged on later runs | Large event data, full rebuild too expensive |
| `ephemeral` | Nothing — inlined as a CTE | Small reusable logic you never want to materialize |

**Ephemeral gotchas.** Not directly selectable, cannot be tested on its own, does not exist in the
warehouse, and is inlined into every downstream model that refs it.

Source: `docs/build/materializations.md`

---

## 01-03 — Modularity and DRY principles

- Staging → intermediate → marts. One source table per staging model, `stg_` prefix.
- Never repeat a transformation twice — push it upstream and `ref()` it.
- Macros and packages for repeated SQL patterns; `ephemeral` for reusable logic that should not land.

Source: `best-practices/how-we-structure/1-guide-overview.md`

---

## 01-04 — Commands: build, run, test, docs, show, snapshot, seed

| Command | Does |
|---|---|
| `dbt run` | Materializes models against the warehouse |
| `dbt test` | Runs data tests only |
| `dbt build` | run + test + snapshot + seed, **interleaved in DAG order** |
| `dbt compile` | Renders SQL only — does **not** touch the warehouse |
| `dbt show` | Previews a model's result set without materializing |
| `dbt snapshot` | Executes snapshots |
| `dbt seed` | Loads CSVs from `seeds/` |
| `dbt docs generate` | Builds the documentation site artifacts |

**The `dbt build` rule.** Tests run **before** their downstream models. A test `FAIL` causes
dependent nodes to be **SKIP**ped. Control this with `warn_if` / `error_if` thresholds on the test
config — not with `--fail-fast`, which does the opposite (stops on first failure).

Source: `reference/commands/build.md`, `reference/commands/compile.md`, `reference/commands/show.md`

---

## 01-05 — Logical model flow and clean DAGs

**`ref()` is what creates the edge.** dbt builds the DAG from `ref()` and `source()` calls — not
from file names, folders, or execution order. A hard-coded table name (`schema.table`) produces
**no dependency**, so dbt is free to build in the wrong order.

Every hard-coded reference must be replaced — in `from` **and** in every `join`.

Source: `docs/build/sql-models.md`, `reference/dbt-jinja-functions/ref.md`

---

### Node selection syntax (heavily tested)

| Selector | Selects |
|---|---|
| `my_model` | Just that model |
| `+my_model` | The model and **all** ancestors |
| `my_model+` | The model and **all** descendants |
| `+my_model+` | Ancestors, the model, and descendants |
| `1+my_model` | The model and **first-degree** parents only |
| `my_model+1` | The model and first-degree children only |
| `@my_model` | Model, its descendants, and the ancestors of those descendants |

The integer goes **on the side the arrow points from** — `1+my_model`, never `+1my_model`.

Other methods: `tag:`, `path:`, `config.materialized:`, `source:`, `state:`, `result:`.

Source: `reference/node-selection/syntax.md`, `reference/node-selection/graph-operators.md`

---

## 01-06 — Configurations in dbt_project.yml

Configs cascade by folder path; more specific wins. The `+` prefix disambiguates a config key from
a folder name.

```yaml
models:
  my_project:
    +materialized: view          # default for everything
    marts:
      +materialized: table       # override for the marts/ folder
      +schema: marts
```

**Precedence, weakest to strongest:** `dbt_project.yml` → property YAML `config:` block →
in-file `{{ config() }}` block.

Source: `reference/dbt_project.yml.md`, `reference/configs-and-properties.md`

---

## 01-07 — dbt Packages

Declared in `packages.yml`, installed with `dbt deps` into `dbt_packages/`.

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
  - git: "https://github.com/org/repo.git"
    revision: main
  - local: ../shared_macros
```

Packages bring macros, models, and tests into your project — everything in them becomes part of
your DAG and builds with your project.

Source: `docs/build/packages.md`

---

## 01-08 — Python models

- Live in `.py` files, define `def model(dbt, session)`, and **must return a DataFrame**.
- Dependencies use `dbt.ref("model")` / `dbt.source("src", "tbl")`, not Jinja.
- Config via `dbt.config(materialized="table")` inside the function.
- Only `table` and `incremental` materializations are supported.
- Warehouse support is limited (Snowpark, Databricks, BigQuery/Dataproc).
- **The `--empty` and `--sample` flags are ignored on Python models.**

Source: `docs/build/python-models.md`

---

## 01-09 — The `grants` config

Applies privileges **at build time** to models, seeds, and snapshots. After a build, dbt makes the
object's grants match the config **exactly** — it issues both `grant` and `revoke`.

```yaml
models:
  - name: specific_model
    config:
      grants:
        select: ['reporter', 'bi_tool']
```

Project-wide default in `dbt_project.yml` uses `+grants:`. Prefixing a privilege with `+`
(`+select:`) **adds to** inherited grants instead of replacing them.

Use hooks instead when you need row/column-level access, masking policies, future grants, or
grants on objects dbt does not create.

Source: `reference/resource-configs/grants.md`

---

## 01-10 — Creating snapshots in YAML

Modern snapshots are defined in YAML under `snapshots/`, with `relation` pointing at the source or
model to track.

```yaml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      schema: snapshots
      unique_key: id
      strategy: timestamp        # timestamp | check
      updated_at: updated_at     # required for timestamp
      # check_cols: [status, amount]   # required for check; or 'all'
      hard_deletes: ignore       # ignore | invalidate | new_record
```

| Strategy | Requires | Detects change via |
|---|---|---|
| `timestamp` | `updated_at` | A reliable updated-at column |
| `check` | `check_cols` | Comparing listed columns (or `all`) |

`timestamp` is preferred when a trustworthy timestamp exists — it is cheaper and catches every
change. Snapshots implement Type 2 SCD via `dbt_valid_from` / `dbt_valid_to`.

Source: `docs/build/snapshots.md`

---

## 01-11 — Selecting the optimal incremental strategy

**When incremental fits.** Large tables where rows are mostly **appended** and rarely updated.
It is the wrong choice when a large share of the dataset changes every run — there a full `table`
rebuild is simpler and often cheaper.

| Strategy | Behaviour | Fits |
|---|---|---|
| `append` | Inserts new rows, no dedup | Immutable event logs |
| `merge` | Upsert on `unique_key` | Records that can update |
| `delete+insert` | Deletes matching keys, reinserts | Adapters without efficient merge |
| `insert_overwrite` | Replaces whole partitions | Partitioned warehouses (BigQuery, Spark) |
| `microbatch` | Time-bounded independent batches | Large time-series data |

Support varies by adapter — `insert_overwrite` is not available on Postgres or Redshift, for
instance. Custom strategies: define a `get_incremental_STRATEGY_sql` macro and set
`incremental_strategy: STRATEGY`; dbt does not validate the name beyond finding the macro.

**`is_incremental()`** is true only when the model already exists, is incremental, and the run is
not `--full-refresh`. It guards the filter that limits the scanned rows.

Source: `docs/build/incremental-models.md`, `docs/build/incremental-strategy.md`

---

## 01-12 — Dry runs with the `--empty` flag

Limits refs and sources to **zero rows**. dbt still executes the SQL against the warehouse, so it
validates dependencies, column names, and schema — without the cost of reading input data.

Supported on `run`, `build`, `snapshot`, and `compile` (and `seed` from v1.12).

**Classic exam trap.** Tests still run under `--empty`, but they run against empty tables — so a
`unique` test passes even when the real source has duplicates. `--empty` does not skip tests and
does not change how a test works.

Ignored on Python models.

Source: `docs/build/empty-flag.md`

---

## 01-13 — Sample mode with the `--sample` flag

Goes one step beyond `--empty`: builds with a **time-based slice** of real data.

- Available on `run` and `build` only.
- Requires `event_time` to be configured on the refs/sources you want filtered.
- Two spec forms: relative (`--sample="3 days"`, granularity in hours/days/months/years) and
  static (a defined start/end window).
- Not all joins will necessarily be populated — it validates, it does not guarantee completeness.
- Ignored on Python models; seeds build fully but are sampled when referenced downstream.

Source: `docs/build/sample-flag.md`

---

## 01-14 — Advanced materializations: microbatch

An incremental strategy for **large time-series datasets**. Splits the run into independent,
idempotent batches — by default one day each — based on `event_time` and `batch_size`.

**Requirements.**
- `event_time` on the microbatch model **and on every upstream model you want filtered**.
- A parent without `event_time` (e.g. a small dimension) is **not** filtered — it gets a full scan
  on every batch.
- `event_time` is a time column for range filtering; it is **not** `partition_by`, which groups rows.

**Why it wins.** Each batch can be built, retried, and backfilled independently, with parallel
execution — no hand-written conditional backfill logic.

Under the hood dbt picks the most efficient per-adapter mechanism: `merge` on Postgres,
`delete+insert` on Redshift and Snowflake, `insert_overwrite` on BigQuery and Spark,
`replace_where` on Databricks.

Source: `docs/build/incremental-microbatch.md`, `reference/resource-configs/event-time.md`
