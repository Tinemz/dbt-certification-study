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

**What it is.** A table that records how rows of a **mutable** source change over time (Type 2
SCD). Each `dbt snapshot` run compares the current source with the snapshot table: a changed row
gets its old version closed (`dbt_valid_to` set) and the new version inserted. First run = a copy
of the source plus meta fields. History can't be rebuilt — a snapshot is not recreated from source.

```yaml
# snapshots/orders_snapshot.yml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')   # what to track: source() or ref()
    config:
      schema: snapshots               # separate schema recommended
      unique_key: id                  # identifies a record across runs
      strategy: timestamp             # how change is detected
      updated_at: updated_at          # required by timestamp
      # check_cols: [status, amount]  # required by check (or 'all')
      dbt_valid_to_current: "to_date('9999-12-31')"  # instead of NULL for current rows
      hard_deletes: ignore            # what to do when a row disappears from the source
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| Snapshot YAML | the `snapshots:` block | `.yml` in `snapshots/`; configs also in `dbt_project.yml` | Legacy `{% snapshot %}` SQL blocks = v1.8 and earlier |
| `relation` | the source/model being tracked | top level of the snapshot entry | Needs transformation first? → `ref()` an **ephemeral** (or staging) model |
| `unique_key` | key matching a record between runs | `config:` | **Required**. Column, list, or expression. Must really be unique |
| `strategy` | how dbt detects that a row changed | `config:` | **Required**. `timestamp` \| `check` (see below) |
| `updated_at` | last-modified column | `config:` | Required only with `timestamp` |
| `check_cols` | columns compared for change | `config:` | Required only with `check`; list or `all` |
| `hard_deletes` | handling of rows deleted in the source | `config:` | `ignore` (default) \| `invalidate` \| `new_record` (see below) |
| `dbt_valid_to_current` | value of `dbt_valid_to` on current rows | `config:` | Default `NULL` |
| `snapshot_meta_column_names` | renames the meta fields | `config:` | Dict, e.g. `{dbt_valid_from: start_date}` |
| `schema` / `database` / `alias` | where the table is built | `config:` | Optional; `schema` goes through `generate_schema_name` |

**`strategy`**

| Value | Requires | Detects change by | Notes |
|---|---|---|---|
| `timestamp` (recommended) | `updated_at` | `updated_at` moved forward | One column to track; robust to added/removed source columns |
| `check` | `check_cols` | Comparing the listed column values | For sources without a reliable timestamp; `check_cols` may need updating as the schema evolves |

**`hard_deletes`**

| Value | Row deleted in source → |
|---|---|
| `ignore` (default) | nothing happens |
| `invalidate` | current row gets `dbt_valid_to` set (replaces legacy `invalidate_hard_deletes=true`) |
| `new_record` | a new row with `dbt_is_deleted = True` is inserted |

**Meta fields** (added to every row)

| Field | Meaning |
|---|---|
| `dbt_valid_from` | when this version became valid |
| `dbt_valid_to` | when it was invalidated; `NULL` (or `dbt_valid_to_current`) = current |
| `dbt_scd_id` | unique key per snapshot row (internal) |
| `dbt_updated_at` | source change timestamp at insertion (internal) |
| `dbt_is_deleted` | only with `hard_deletes: new_record` |

**Gotchas.**
- Snapshots **ignore** `--full-refresh` and the `full_refresh` config — history is never dropped.
- Downstream models read it with `ref('orders_snapshot')`.
- Useful only if `dbt snapshot` runs on a schedule.

Source: `docs/build/snapshots.md`, `snippets/_snapshot-full-refresh.md` (under `website/`)

---

## 01-11 — Selecting the optimal incremental strategy

**What it is.** A materialization that, after the first build, transforms only **new or changed**
rows and writes them into the existing table instead of rebuilding it. First run (or
`--full-refresh`) = full build. Later runs = the model's SQL filtered by an `is_incremental()`
block, then written using the **strategy**. Fits large tables where rows are mostly appended and
rarely updated; wrong when a large share of the data changes every run — a full `table` is simpler.

```sql
-- models/fct_daily_active_users.sql
{{
    config(
        materialized='incremental',
        unique_key='date_day',              -- grain; enables update instead of append
        incremental_strategy='delete+insert',
        on_schema_change='fail'             -- what to do if columns change
    )
}}

select date_trunc('day', event_at) as date_day, count(distinct user_id) as daily_active_users
from {{ ref('app_data_events') }}

{% if is_incremental() %}                   -- false on first run / --full-refresh
  where date_day >= (select coalesce(max(date_day), '1900-01-01') from {{ this }})
{% endif %}                                 -- {{ this }} = the existing target table

group by 1
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| `materialized='incremental'` | turns incremental on | `config()` / YAML `config:` / `dbt_project.yml` | — |
| `is_incremental()` | macro wrapping the "new rows" filter | model SQL | `true` only if: table exists **and** no `--full-refresh` **and** model is incremental. SQL must be valid either way |
| `{{ this }}` | the model's existing target table | model SQL, inside the `is_incremental()` block | Used to find the latest loaded timestamp |
| `unique_key` | column(s) defining the grain | `config` | Optional. Without it → append-only on most adapters. Columns must have no nulls. Prefer a list over `concat()` |
| `incremental_strategy` | how new rows are written | `config` | See below; support varies by adapter |
| `on_schema_change` | reaction when the model's columns change | `config` | See below |
| `merge_update_columns` / `merge_exclude_columns` | limit which columns a `merge` updates | `config` | `merge` only |
| `incremental_predicates` | extra SQL filters to limit the scan of the target table | `config` (list) | Advanced; syntax not checked; aliases `DBT_INTERNAL_DEST` (target) / `DBT_INTERNAL_SOURCE` (new) |
| `full_refresh` | force always/never full refresh | `config` | `true`/`false` **overrides** the `--full-refresh` flag |
| `--full-refresh` | drop and rebuild from scratch | CLI | Use when the model logic changed; `my_model+` refreshes downstream incrementals too |

**`incremental_strategy`**

| Value | Behaviour | Uses `unique_key` | Fits |
|---|---|---|---|
| `append` | inserts new rows, no dedup | no | immutable event logs |
| `merge` | upsert on `unique_key` | yes | records that can update |
| `delete+insert` | deletes matching keys, reinserts | yes | adapters without efficient merge |
| `insert_overwrite` | replaces whole partitions | **no** — works on partitions | partitioned warehouses (BigQuery, Spark) |
| `microbatch` | time-bounded independent batches | adapter-dependent (see 01-14) | large time-series data |

- Not on Postgres/Redshift: `insert_overwrite`. Not on BigQuery: `append`, `delete+insert`.
- Custom: define macro `get_incremental_<name>_sql`, set `incremental_strategy: <name>`.

**`on_schema_change`**

| Value | Column added to the model | Column removed from the model |
|---|---|---|
| `ignore` (default) | **not** added to the table | `dbt run` **fails** |
| `fail` | error | error |
| `append_new_columns` | added | kept in the table |
| `sync_all_columns` | added | removed (includes type changes) |

None backfill old rows for new columns → manual update or `--full-refresh`. Top-level columns only
(nested changes not tracked).

Source: `docs/build/incremental-models.md`, `docs/build/incremental-strategy.md`,
`snippets/_incremental-predicates.md` (under `website/`)

---

## 01-12 — Dry runs with the `--empty` flag

Limits refs and sources to **zero rows**. dbt still executes the SQL against the warehouse, so it
validates dependencies, column names, and schema — without the cost of reading input data.

Supported on `run`, `build`, `snapshot`, and `compile` (and `seed` from v1.12).

**Classic exam trap.** Tests still run under `--empty`, but they run against empty tables — so a
`unique` test passes even when the real source has duplicates. `--empty` does not skip tests and
does not change how a test works.

The mechanism: a data test returns the rows that **fail**, and passes when it returns none. Against
a zero-row table every test returns nothing, so every test passes **vacuously**. A green `--empty`
build proves the SQL compiles and the dependencies resolve; it proves nothing about the data.

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

**What it is.** An incremental **strategy** for large time-series data. dbt splits the run into
**batches** — one query per time period (`batch_size`, e.g. one day) — using the model's
`event_time`. Each batch is independent and idempotent: it can be built, run in parallel, retried,
or backfilled on its own. You write the SQL for **one batch** with no `is_incremental()` filter;
dbt filters every upstream that has `event_time` to the batch's window.

```sql
-- models/sessions.sql
{{ config(
    materialized='incremental',
    incremental_strategy='microbatch',
    event_time='session_start',   -- this model's time column
    begin='2020-01-01',           -- "beginning of time" for first / full builds
    batch_size='day'              -- one query per day
) }}

select ...
from {{ ref('page_views') }}      -- has event_time → auto-filtered to the batch
left join {{ ref('customers') }}  -- no event_time → full scan every batch
  on ...
```

```yaml
# models/staging/page_views.yml — upstream opts in to filtering
models:
  - name: page_views
    config:
      event_time: page_view_start
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| `incremental_strategy='microbatch'` | turns microbatch on | model `config` | Requires `materialized='incremental'` |
| `event_time` | column saying when the row occurred | model **and** each upstream to filter | **Required**. Upstream without it = not filtered. Not `partition_by` (that groups rows) |
| `begin` | start point for initial / full-refresh builds | model `config` | **Required**. dbt doesn't infer the data's min date |
| `batch_size` | batch granularity | model `config` | **Required**. `hour` \| `day` \| `month` \| `year` |
| `lookback` | extra prior batches reprocessed each run (late-arriving rows) | model `config` | Optional, default `1` |
| `concurrent_batches` | force parallel (`true`) / sequential (`false`) | model `config` | Optional; default = auto-detect |
| `unique_key` / `partition_by` | adapter-specific extras | model `config` | `unique_key` required on Postgres; `partition_by` required on BigQuery, Spark |
| `ref('x').render()` | opt one upstream out of auto-filtering | model SQL | Not recommended — full scan per batch |
| `--event-time-start` / `--event-time-end` | backfill a date range | CLI (`run` / `build`) | Must be passed **together** |
| `dbt retry` | reruns **only the failed batches** | CLI | — |

**Mechanism per adapter** (dbt picks it; you don't choose)

| Adapter | Runs each batch as |
|---|---|
| Postgres | `merge` (hence `unique_key` required) |
| Redshift, Snowflake | `delete+insert` |
| BigQuery, Spark | `insert_overwrite` (hence `partition_by` required) |
| Databricks | `replace_where` |

**Gotchas.**
- Recommended: `full_refresh: false` on microbatch models. `--full-refresh` alone reloads nothing
  unless `begin` is set; reprocess history with `--full-refresh --event-time-start … --event-time-end …`.
- All times (`event_time`, `begin`, the CLI flags) are assumed **UTC**.
- Not ideal without a reliable `event_time`, or when you need custom incremental logic.

Source: `docs/build/incremental-microbatch.md`, `reference/resource-configs/event-time.md`
