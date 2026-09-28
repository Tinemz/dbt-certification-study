# Topic 02 — Managing dbt models governance

3 sub-skills. Contracts, versions and constraints are one mechanism seen from three angles: a
contract is the promise, constraints are the platform-level enforcement of part of that promise,
and versions are how the promise changes without breaking consumers.

All paths below are relative to `vendor/dbt-docs/website/docs/`.

---

## 02-01 — Adding contracts to models to ensure the shape of models

**What it is.** `contract: {enforced: true}` makes dbt guarantee that the dataset the model returns
matches the YAML exactly: `name` and `data_type` for **every** column, plus any `constraints` the
materialization and platform support. Enforcement happens at build time — a mismatch fails the run.

```yml
models:
  - name: dim_customers
    config:
      materialized: table
      contract:
        enforced: true        # turns the contract on
        # alias_types: false  # opt out of type aliasing
    columns:                  # EVERY column the model returns
      - name: customer_id     # must match the SQL output
        data_type: int        # must match the SQL output
      - name: country_name
        data_type: varchar
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| `contract.enforced` | turns the contract on | model `config:` (YAML, `config()` or `dbt_project.yml`) | `true` → mismatch fails the build **before** the table is materialized |
| `alias_types` | converts generic names to platform types (`string` → `text`) | under `contract:` | Default `true`; unknown names pass through as-is |
| `columns[].name` | a column the model must return | model YAML | All columns, no partial contracts |
| `columns[].data_type` | its required type | each column | Compared by type, not size/precision |
| `constraints` | platform-level rules (see 02-03) | column or model level | Only as supported by materialization + platform |
| `on_schema_change` | incremental models only | model `config` | Use `append_new_columns` or `fail`; `sync_all_columns` can drop a column = breaking change |

| Rule | Detail |
|---|---|
| Every column declared | Contracts apply to **all** columns; partial declaration is not allowed |
| Type aliasing | `string` → `text` on Postgres/Redshift. Opt out with `alias_types: false` |
| Size / precision / scale | **Not compared**. `varchar(256)` vs `varchar(257)` does not fail |
| Numeric defaults | An unspecified `numeric` may default to scale 0 and fail enforcement — declare `numeric(38, 6)`. 1.7+ warns when precision/scale are omitted |
| Tests | **Not part of the contract.** The contract is shape, not quality |

**Breaking changes** against a previous state (contract error):

- removing an existing column;
- changing the `data_type` of an existing column;
- removing or modifying a `constraint` on an existing column (1.6+);
- removing a contracted model by deleting, renaming or disabling it (1.9+) — **versioned** models
  raise an **error**, unversioned models raise a **warning**.

Source: `reference/resource-configs/contract.md`, `docs/mesh/govern/model-contracts.md`,
`snippets/_versions-contracts.md`

---

## 02-02 — Creating different versions of our models and deprecating the old ones

**What it is.** `versions` declares several implementations of the **same** model that live in the
repo and the warehouse **at the same time** — one `.sql` file and one table/view per version,
sharing one name and one YAML entry. The top-level YAML (`columns`, `config`) is the shared
baseline; each version entry states only how it differs. Unpinned `ref('model_name')` resolves to
`latest_version`; consumers may pin one version. `deprecation_date` (1.6+) announces when an old
version stops being supported. Purpose: ship a **breaking** change without breaking consumers.

```yml
# models/_dim_customers.yml
models:
  - name: dim_customers
    latest_version: 2             # target of unpinned ref('dim_customers')
    config:
      contract: {enforced: true}  # shared by all versions
    columns:                      # shared baseline
      - name: customer_id
        data_type: int
      - name: country_name
        data_type: varchar
    versions:
      - v: 3                      # above latest → prerelease; file dim_customers_v3.sql
      - v: 2                      # latest; file dim_customers_v2.sql or dim_customers.sql
      - v: 1                      # below latest → old; file dim_customers_v1.sql
        deprecation_date: 2026-12-31
        columns:
          - include: '*'          # start from all baseline columns...
            exclude: [country_name]  # ...minus this one
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| `versions` | list of the model's versions | model entry in YAML | — |
| `v` | version identifier | each `versions` item | **Required**. Numeric or string; non-numeric sorted **alphabetically**. Don't write the letter `v` — dbt adds it |
| `latest_version` | version unpinned `ref()` resolves to | model entry (top level) | Must be a declared `v`. Default: greatest numeric, else alphabetically last. Above it = `prerelease`, below = `old` |
| Version SQL file | the implementation of one version | `models/` | Default name `<model>_v<v>.sql`; the **latest** may be `<model>.sql`. File names globally unique |
| `defined_in` | overrides the file name (no extension) | each `versions` item | Independent of `alias` |
| `alias` | overrides the warehouse name | version entry or the version's model config | Default `<model>_v<v>`, from `generate_alias_name` |
| `columns` + `include` / `exclude` | which baseline columns this version has | each `versions` item | At most **one** `include`/`exclude` element per version (see below) |
| `columns[].name` in a version | adds or overrides a column for that version | each `versions` item | Same `name` as a baseline column → overrides it |
| `deprecation_date` | when this version stops being supported | a `versions` item or the model | See `deprecation_date` below |
| `ref('m', v=2)` | pinned reference | consumer SQL | Cross-project: `ref('project', 'm', v='3')` |

**`include` / `exclude`**

| Field | Value | Default |
|---|---|---|
| `include` | list of column names, or `'*'` / `'all'` | `'*'` |
| `exclude` | list of names; **only** valid when `include` is `'*'` or `'all'` | empty |

No version declares `columns` → all baseline columns apply to every version. Not to be confused
with `--select` / `--exclude`, which is node selection.

### Selection

```bash
dbt list --select "version:latest"      # only latest versions
dbt list --select "version:prerelease"  # newer than latest
dbt list --select "version:old"         # older than latest
dbt list --select "version:none"        # models that are not versioned
```

### The documented migration pathway

Verbatim order from the docs — develop, **bump**, **deprecate**, **update refs**, remove:

1. Develop the new version alongside the existing one.
2. **Bump `latest_version`** so new `ref()` calls resolve to it.
3. **Set `deprecation_date`** on the old version — opens the migration window.
4. **Update downstream references** to the new version.
5. Remove the old version once the date passes.

Steps 2 and 3 come **before** step 4: the new version has to be canonical and the window has to be
announced before consumers are asked to move. Removing first breaks consumers immediately.

**What step 4 actually covers.** Bumping `latest_version` already redirects every *unpinned* `ref()`
— those need no edit. The manual migration is for references that do **not** follow the pointer:

| Consumer | Follows a `latest_version` bump? |
|---|---|
| `ref('dim_customers')` | ✅ automatic |
| `ref('dim_customers', v=1)` — pinned | ❌ manual |
| Cross-project `ref('proj', 'dim_customers', v=1)` | ❌ manual |
| BI / external tools reading `analytics.dim_customers_v1` | ❌ manual |

Pinning to a specific version is *how consumers survive the migration window* — so pins are the
expected state during it, and clearing them is what unblocks step 5.

Cadence advice: don't version every small change. Prefer non-breaking additions, and bump `latest`
on a predictable schedule (once or twice a year, announced in advance), dropping unused columns then.

Source: `docs/mesh/govern/model-versions.md`

### `deprecation_date`

```yml
models:
  - name: dim_customers
    deprecation_date: 2026-12-31 00:00:00.00+00:00
```

- RFC 3339: `YYYY-MM-DD hh:mm:ss.sss±hh:mm`, `YYYY-MM-DD hh:mm:ss.sss`, or `YYYY-MM-DD`.
- **No UTC offset → the system time zone of the dbt execution environment.**
- Works with or without model versions.

| Warning | Raised when | Affects |
|---|---|---|
| `DeprecatedModel` | parsing a project that defines a deprecated model | producer |
| `DeprecatedReference` | referencing a model whose date has **passed** | producer + consumers |
| `UpcomingReferenceDeprecation` | referencing a model with a **future** date | producer + consumers |

`WARN_ERROR_OPTIONS` promotes any of these warnings to runtime errors.

### Exam angles

- Version a model for a **breaking** change (removing/renaming a column, changing a data type or
  nullability). A non-breaking addition, like a new column or a bug fix, does **not** need a version.
- Unpinned `ref` → `latest_version`, not the highest `v`, whenever `latest_version` is set explicitly.
- `version:` selection has four values, including `none` for unversioned models.
- Model versions are **not** version control: several versions live in the repo and in the warehouse
  **at the same time**.

### Gotchas

- **Deprecation does not delete anything.** dbt does not drop relations for deprecated models; they
  keep being built until `enabled: false` or removal.
- A past `deprecation_date` produces a **warning**, not an error, unless promoted by
  `WARN_ERROR_OPTIONS`.
- There is **no node selection syntax** for `deprecation_date` — use `dbt ls --output json
  --output-keys ... deprecation_date`.
- Model file names must be **globally unique**, including versioned files.
- `state:modified` catches changes to `latest_version` and `deprecation_date`.

**Not on the 1.11 exam:** `latest_version_pointer` (a config that auto-creates a view pointing at the
latest version) is **1.12+**. Source: `reference/resource-configs/latest_version_pointer.md`

On **1.11** the same effect is a do-it-yourself pattern: a `create_latest_version_view()` macro
guarded by `model.version == model.latest_version`, called from an `on-run-end` hook. That is the
answer if the exam asks how to give BI tools an unversioned name.
Source: `docs/mesh/govern/model-versions.md`

Source: `reference/resource-properties/versions.md`, `reference/resource-properties/latest_version.md`,
`reference/resource-properties/deprecation_date.md`, `docs/mesh/govern/model-versions.md`,
`reference/node-selection/methods.md`

---

## 02-03 — Defining constraints in YAML to enforce data integrity at the platform level

**What it is.** A constraint is validated by the **data platform** as rows are written. If validation
fails, the create or insert fails and the operation is **rolled back** — invalid data never lands in
the table. This is the opposite order from a dbt test, which queries the table **after** it is built.

### Prerequisites

| Requirement | Detail |
|---|---|
| Materialization | **`table` or `incremental` only**. Never applied on `view` or `ephemeral` |
| Contract | The model must declare `contract: {enforced: true}`, with `data_type` on every column |

### Structure

```yml
models:
  - name: dim_customers
    config:
      materialized: table
      contract: {enforced: true}

    # model-level
    constraints:
      - type: primary_key
        columns: [customer_id, valid_from]
      - type: foreign_key
        columns: [country_code]
        to: ref('dim_countries')
        to_columns: [country_code]
      - type: check
        columns: [start_date, end_date]
        expression: "start_date < end_date"
        name: dates_in_order

    columns:
      - name: customer_id
        data_type: int
        # column-level
        constraints:
          - type: not_null
          - type: unique
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| `constraints` (column level) | list of constraints on one column | under a `columns[]` item | Recommended for single-column constraints |
| `constraints` (model level) | list of constraints spanning columns | model entry, sibling of `columns` | Required for multi-column constraints and for several `primary_key`s |
| `type` | the kind of constraint | each constraint | **Required**. `not_null`, `unique`, `primary_key`, `foreign_key`, `check`, `custom` |
| `columns` | the columns it applies to | each constraint, **model level only** | Its presence = model-level constraint |
| `expression` | free text qualifying the constraint (e.g. a `check` condition) | each constraint | Required depending on `type` |
| `name` | human-friendly name | each constraint | Optional; supported by some platforms |
| `to` / `to_columns` | the referenced relation and its columns | `foreign_key` constraint (1.9+) | `ref()` or `source()` — captures the dependency, works across environments |
| `warn_unenforced` | `False` silences "definable, not enforced" warning | each constraint | Does not change enforcement |
| `warn_unsupported` | `False` silences "not definable" warning | each constraint | Does not change enforcement |

- Single-column constraints belong **on the column**; that is the documented recommendation.
- **Multiple `primary_key` constraints must be declared at the model level** — several `primary_key`
  entries at column level are not supported.

### Platform support

Three categories: **definable and enforced**, **definable and not enforced** (metadata only, still
rendered into the DDL), and **not definable** (absent from the DDL).

| Constraint | Postgres | Snowflake | Redshift | BigQuery |
|---|---|---|---|---|
| `not_null` | enforced | **enforced** | **enforced** | **enforced** |
| `primary_key` | enforced | definable only | definable only | definable only |
| `foreign_key` | enforced | definable only | definable only | definable only |
| `unique` | enforced | definable only | definable only | not definable |
| `check` | enforced | not definable | not definable | not definable |

Postgres supports and enforces the ANSI SQL constraints plus row-level `check`. Most analytical
platforms enforce only `not_null`.

### Exam angles

- **Constraint vs test.** A constraint is platform-level and blocks the write; a test is a dbt query
  run afterwards and reports `fail`. On most warehouses only `not_null` actually blocks anything.
- A constraint on a `view` or `ephemeral` model is **never applied**.
- No enforced contract → no constraints.
- `columns:` on a constraint means it is **model-level**.

### Gotchas

- "Definable and not enforced" still lands in the templated DDL — useful for catalog and ERD tools,
  and for platforms that can use the key for query optimization. It guarantees nothing about the data.
- Silencing warnings (`warn_unenforced`, `warn_unsupported`) does not change enforcement.
- Removing or modifying a constraint on a contracted model is a **breaking change** (1.6+), which is
  also what `state:modified.contract` detects.

Source: `reference/resource-properties/constraints.md`, `snippets/_constraints-table.md`,
`reference/resource-configs/contract.md`
