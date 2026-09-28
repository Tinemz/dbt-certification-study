# Topic 06 — Implementing and maintaining external dependencies

2 sub-skills. Both describe the **edges of the DAG**: exposures mark what consumes the project
downstream, source freshness guards what feeds it upstream.
All paths below are relative to `vendor/dbt-docs/website/docs/`.

---

## 06-01 — Implementing dbt exposures

**What it is.** An exposure defines and describes a **downstream use** of the project — a dashboard,
notebook, application, ML pipeline. It is a metadata node: it is never built or materialized. Its
payoff is twofold — selecting everything that feeds a consumer, and a dedicated page on the docs
site for data consumers.

### Declaration

Nested under an `exposures:` key, in any `.yml` inside `models/`, at any depth. The same file may
also define `sources:` and `models:`.

```yaml
# models/exposures.yml — any .yml under models/, any depth
exposures:
  - name: weekly_jaffle_metrics      # required; snake_case id
    label: Jaffles by the Week       # display name; free text
    type: dashboard                  # required
    maturity: high
    url: https://bi.tool/dashboards/1
    description: >
      Did someone say "exponential growth"?

    depends_on:                      # expected: what the consumer reads
      - ref('fct_orders')
      - ref('dim_customers')
      - source('gsheets', 'goals')
      - metric('count_orders')

    owner:                           # required: name or email
      name: Callum McData
      email: data@jaffleshop.com
```

### Properties

| Element | Tier | What it is | Where it goes | Rule |
|---|---|---|---|---|
| `exposures:` | — | the block listing exposures | top level of any `.yml` in `models/` | Same file may hold `sources:` / `models:` |
| `name` | **Required** | unique id | exposure entry | snake case; letters, numbers, underscores **only** |
| `type` | **Required** | kind of consumer | exposure entry | `dashboard`, `notebook`, `analysis`, `ml`, `application` |
| `owner` | **Required** | who owns the consumer | exposure entry | `name` **or** `email` — at least one; extra properties allowed |
| `depends_on` | **Expected** | nodes the consumer reads | exposure entry (list) | `ref`, `source`, `metric` |
| `label` | Optional | human-readable name | exposure entry | spaces, capitals, special characters allowed |
| `url` | Optional | link to the consumer | exposure entry | activates **View this exposure** on the docs site |
| `maturity` | Optional | how stable the consumer is | exposure entry | `high`, `medium`, `low` |
| `description` | Optional | docs text | exposure entry | — |
| `tags`, `meta` | Optional | general properties | under `config:` (v1.10+) | — |
| `enabled` | Optional | turn off the exposure | exposure entry or `dbt_project.yml` | — |

Source: `docs/build/exposures.md`, `reference/exposure-properties.md`

### Selection

The `exposure:` method selects the **parent** resources of an exposure — it is meaningless without
the `+` operator in front.

```bash
dbt run  --select "+exposure:weekly_kpis"                 # everything feeding one exposure
dbt test --select "+exposure:*"                           # everything upstream of all exposures
dbt ls   --select "+exposure:*" --resource-type source    # just the sources behind them
```

Source: `reference/node-selection/methods.md`

**Exam angles.**

- Which three properties are required: `name`, `type`, `owner`. `depends_on` is *expected*, not
  required; `url` and `maturity` are optional.
- `owner` needs **name or email**, not both.
- The five legal `type` values — a sixth invented one (`report`, `bi`, `metric`) is the classic
  distractor.
- `name` rejects spaces and special characters; `label` is what exists to carry them.
- `+exposure:name` selects parents. `exposure:name` alone selects the exposure node itself, which
  builds nothing.

**Gotchas.**

- The `depends_on` **YAML property** is unrelated to the `-- depends_on` **SQL comment directive**
  used at the top of a model file.
- Exposures are never built. `dbt run` on an exposure selector runs its *parents*.
- Depending on a `source()` directly is legal but, per the docs, highly unlikely to be needed.
- Automatic exposures from platform integrations behave like manual ones but exist only in dbt's
  metadata system — there is no YAML for them.

Source: `docs/build/exposures.md`, `reference/exposure-properties.md`

---

## 06-02 — Implementing source freshness

**What it is.** A `freshness` block declares how old the newest record in a source table may be
before dbt warns or errors. `dbt source freshness` queries the sources, compares against the
thresholds, and writes the result to `sources.json`.

### Configuration

```yaml
sources:
  - name: jaffle_shop
    database: raw
    config:
      freshness:                              # changed to config in v1.9
        warn_after: {count: 12, period: hour}
        error_after: {count: 24, period: hour}
      loaded_at_field: _etl_loaded_at         # changed to config in v1.10

    tables:
      - name: customers                       # inherits the source-level block

      - name: orders
        config:
          freshness:                          # overrides the source-level block
            warn_after: {count: 6, period: hour}
            error_after: {count: 12, period: hour}
            filter: datediff('day', _etl_loaded_at, current_timestamp) < 2

      - name: product_skus
        config:
          freshness: null                     # excluded from freshness checks
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| `freshness` | the thresholds block | `config:` of a source (all its tables) or of a table (overrides) | Under `config` since v1.9 |
| `warn_after` / `error_after` | max age before a warning / an error | inside `freshness` | One **or** both; **neither** → freshness not calculated |
| `count` | size of the threshold | inside `warn_after` / `error_after` | positive integer |
| `period` | unit of the threshold | inside `warn_after` / `error_after` | `minute`, `hour`, `day` |
| `filter` | `where` clause added to the freshness query | inside `freshness` | boolean SQL expression |
| `freshness: null` | opt-out | table (or source) `config:` | the documented way to exclude |
| `loaded_at_field` | column/expression holding the load timestamp | source or table `config:` | Under `config` since v1.10. Required unless the adapter reads metadata |
| `loaded_at_query` | custom SQL returning the timestamp | source or table `config:` | v1.10+. Not together with `loaded_at_field` |

### How dbt computes the timestamp

| Given | dbt uses |
|---|---|
| `loaded_at_field` provided | a select query against that column or expression |
| `loaded_at_field` absent | warehouse **metadata tables**, where the adapter supports it |
| `loaded_at_query` provided (**v1.10+**) | the custom SQL expression |

`loaded_at_query` and `loaded_at_field` are mutually exclusive. Metadata-based freshness is
supported on Snowflake, Redshift, BigQuery (`dbt-bigquery` 1.7.3+) and Databricks (Fusion).

### Hierarchy

Source-level `freshness` and `loaded_at_field` apply to **every table** in that source; a
table-level block **overrides** it. Useful because tables in one source usually share the
`loaded_at_field`.

### The command

```bash
dbt source freshness                                       # all sources
dbt source freshness --select "source:snowplow"            # one source
dbt source freshness --select "source:snowplow.event"      # one source table
dbt source freshness --output target/source_freshness.json # relocate the artifact
```

- Only subcommand of `dbt source`.
- Writes `target/sources.json`; `-o` / `--output` relocates it.
- A **stale** source makes dbt exit with a **nonzero exit code**.
- `sources.json` records `max_loaded_at`, `snapshotted_at`, `max_loaded_at_time_ago_in_s`, `state`
  and the `criteria` applied.

Feeds the `source_status:` selector on a later invocation:

```bash
dbt source freshness
dbt build --select "source_status:fresher+" --state path/to/prod/artifacts
```

Source: `reference/commands/source.md`, `reference/resource-properties/freshness.md`

**Exam angles.**

- Omitting **both** `warn_after` and `error_after` disables freshness for that source — it does not
  default to anything.
- Table-level beats source-level; the source block is the fallback, not the winner.
- `freshness: null` is the documented way to exclude, not deleting the block from a parent.
- Nonzero exit code on stale data is what makes the command usable as a pipeline gate.
- `--select` on `dbt source freshness` takes `source:` selectors, not model names.
- The artifact is `sources.json`, not `run_results.json`.

**Gotchas.**

- Config migration is version-specific and testable on 1.11: `freshness` moved under `config` in
  **v1.9**; `loaded_at_field` moved under `config` in **v1.10**.
- `loaded_at_field` is *optional* only on adapters that read warehouse metadata; elsewhere it is
  required.
- The BigQuery wildcard guard (`bigquery_reject_wildcard_metadata_source_freshness`) is **v1.12** —
  out of scope for a 1.11 exam.
- `source_status:fresher+` requires `dbt source freshness` to be **re-run**, so there is a current
  `sources.json` to compare against the one in `--state`.

Source: `reference/resource-properties/freshness.md`, `reference/commands/source.md`
