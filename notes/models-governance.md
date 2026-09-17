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
        enforced: true
    columns:
      - name: customer_id
        data_type: int
      - name: country_name
        data_type: varchar
```

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

**What it is.** `versions` declares several live implementations of the **same** model, sharing one
name and most of their YAML. Consumers keep using `ref('model_name')` and may pin to a version.
`deprecation_date` (1.6+) announces when an old version stops being supported.

```yml
models:
  - name: dim_customers
    latest_version: 2
    config:
      contract: {enforced: true}
    columns:
      - name: customer_id
        data_type: int
      - name: country_name
        data_type: varchar
    versions:
      - v: 3                      # prerelease
      - v: 2                      # latest
      - v: 1                      # old
        deprecation_date: 2026-12-31
        columns:
          - include: '*'
            exclude: [country_name]
```

### Naming and resolution

| Concept | Default |
|---|---|
| File for `v: 2` | `dim_customers_v2.sql`; override with `defined_in` |
| File for the **latest** version | may drop the suffix: `dim_customers.sql` |
| Database alias | `<model_name>_v<v>`, from the `generate_alias_name` macro; override with `alias` |
| Unpinned `ref('dim_customers')` | resolves to `latest_version` |
| Pinned ref | `ref('dim_customers', v=2)`; cross-project `ref('project', 'model', v='3')` |

- `v` is required, numeric or string. **Do not** write the `v` in the identifier — dbt adds it.
- Non-numeric identifiers are sorted **alphabetically**.
- `latest_version` must be one of the declared identifiers. Default: greatest numeric, otherwise
  alphabetically last.
- Versions **above** `latest_version` are `prerelease`; **below** are `old`.
- `defined_in` and `alias` are independent of each other — coordinated only by convention.

### `include` / `exclude`

Each version's `columns` list may carry **at most one** `include`/`exclude` element.

| Field | Value |
|---|---|
| `include` | list of column names, or `'*'` / `'all'` (default) |
| `exclude` | list of names; **only** valid when `include` is `'*'` or `'all'` (default: empty) |

A version-specific column whose `name` matches a top-level column **overrides** it for that version.
If no version declares `columns`, all top-level columns apply to every version.

Not to be confused with `--select` / `--exclude`, which is node selection.

### Selection

```bash
dbt list --select "version:latest"      # only latest versions
dbt list --select "version:prerelease"  # newer than latest
dbt list --select "version:old"         # older than latest
dbt list --select "version:none"        # models that are not versioned
```

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

| Field | Required | Notes |
|---|---|---|
| `type` | yes | `not_null`, `unique`, `primary_key`, `foreign_key`, `check`, `custom` |
| `expression` | depends on type | Free text qualifying the constraint |
| `name` | no | Human-friendly name; supported by some platforms |
| `columns` | **model level only** | The columns the constraint applies to |
| `to` / `to_columns` | foreign_key, 1.9+ | `ref()` or `source()` — captures the dependency and works across environments |
| `warn_unenforced` | no | `False` silences the warning for supported-but-not-enforced constraints |
| `warn_unsupported` | no | `False` silences the warning for unsupported constraints |

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
