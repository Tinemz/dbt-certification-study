# Topic 05 — Implementing dbt tests

All paths below are relative to `vendor/dbt-docs/website/docs/`.

---

## 05-01 — Using generic, singular, custom, custom generic, and unit tests

**What it is.** Two families. **Data tests** (generic, singular, custom generic) are `select`
queries that return failing rows against a *built* relation — zero rows means pass. **Unit tests**
validate a model's SQL logic against static fixture inputs *before* the model is materialized.

### The five kinds at a glance

| Kind | Defined where | Applied how | Runs against | Result |
|---|---|---|---|---|
| Built-in generic | ships with dbt | by name in YAML `data_tests:` | built data | count of failing rows |
| Singular | `.sql` file in `tests/` | automatically — never referenced in YAML | built data | count of failing rows |
| Custom generic | `{% test %}` block in `tests/generic/` or `macros/` | by name in YAML `data_tests:` | built data | count of failing rows |
| Custom (override of built-in) | `{% test unique(...) %}` in your project | same name as built-in — yours wins | built data | count of failing rows |
| Unit | `unit_tests:` YAML under `model-paths` | `model:` + `given:` + `expect:` | static fixtures | pass (0) / fail (1) |

### Built-in generic tests

Exactly four: `unique`, `not_null`, `accepted_values`, `relationships`.

```yaml
models:
  - name: orders
    columns:
      - name: order_id
        data_tests:
          - unique
          - not_null
      - name: status
        data_tests:
          - accepted_values:
              arguments:            # v1.10.5+
                values: ['placed', 'shipped', 'completed', 'returned']
      - name: customer_id
        data_tests:
          - relationships:
              arguments:
                to: ref('customers')
                field: id
```

- `arguments:` = inputs to the test macro (`values`, `to`, `field`).
- `config:` = framework options (`severity`, `where`, `store_failures`). Never under `arguments:`.
- Data tests attach to **models, sources, seeds, snapshots**.

### Singular test

```sql
-- tests/assert_total_payment_amount_is_positive.sql
select order_id, sum(amount) as total_amount
from {{ ref('fct_payments') }}
group by 1
having total_amount < 0
```

- Test name = file name. One `select` per file. Jinja (`ref`, `source`) allowed.
- No trailing semicolon — it can make the test fail.
- Runs on `dbt test` automatically. Referencing it in a model's YAML → **error**.
- Description goes in a YAML under `tests/`, top-level `data_tests:` with `name:`.

### Custom generic test

```sql
-- tests/generic/test_is_even.sql
{% test is_even(model, column_name) %}
    select {{ column_name }} from {{ model }}
    where ({{ column_name }} % 2) = 1
{% endtest %}
```

- Location: `tests/generic/` (under `test-paths`) **or** `macros/`.
- Standard args: `model`, `column_name`. The arg is **always** named `model`, even on a source,
  seed, or snapshot. Both are supplied by YAML context — don't pass them.
- Extra args go in the signature (`field`, `to`) and are passed via `arguments:`.
- A `config()` inside the block sets the **default** for every instance; the YAML instance overrides.
- Defining a test block named like a built-in (`unique`) replaces the built-in project-wide.
- Documenting it under `macros:` → prefix the name with `test_` (`test_not_empty_string`).

### Unit test

**What it is.** A test of a model's SQL **logic**, not of its data. Each upstream `ref`/`source`
is replaced by a small, fixed set of fake rows (mock data). dbt runs the model's SQL on those rows
and compares the output with the rows you declared as expected. Runs **before** the model is
materialized. One unit test = one test case → result is pass (0) / fail (1).

```yaml
unit_tests:
  - name: test_is_valid_email_address
    model: dim_customers                  # the one model under test
    given:                                # mock inputs — one per ref/source the model reads
      - input: ref('stg_customers')
        rows:
          - {email: cool@example.com, email_top_level_domain: example.com}
      - input: ref('top_level_email_domains')
        rows:
          - {tld: example.com}
    expect:                               # expected output of the model — exactly one
      rows:
        - {email: cool@example.com, is_valid_email_address: true}
```

| Element | What it is | Where it goes | Rule |
|---|---|---|---|
| Unit test YAML | the `unit_tests:` block | any `.yml` under `model-paths` (`models/`) | **Not** `tests/` |
| `model` | the model under test | inside the unit test | exactly one |
| `given` | list of mock inputs | inside the unit test | every `ref`/`source` in the model must be declared, or "node not found" at compile |
| `input` | which upstream is mocked: `ref('…')` or `source('…', '…')` | each `given` item | seed: optional — an omitted seed is used as-is |
| `expect` | rows the model must output for those inputs | inside the unit test | exactly one (an object, not a list) |
| `rows` | mock data written **inline** in the YAML | a `given` item or `expect` | empty input = `rows: []` |
| `fixture` | mock data kept in a **separate file**, referenced by file name without extension (instead of `rows`) | file in `tests/fixtures/` (a `fixtures` subdir of `test-paths`); key on a `given` item or `expect` | `csv` or `sql` files only |
| `format` | how the mock data is written: `dict` (default), `csv`, `sql` | a `given` item or `expect` | see table below |
| `overrides` | replaces `macros`, `vars`, `env_vars` values during the test | inside the unit test | only those referenced **directly** in the model |
| `versions` | which versions of a versioned model to test | inside the unit test | default: **all** versions; narrow with `include`/`exclude` |

**`format`** — same options for `given` and `expect`.

| `format` | Inline `rows` looks like | `fixture` file | Columns to supply |
|---|---|---|---|
| `dict` (default) | YAML dicts: `- {id: 1, name: gerda}` | not supported | only the relevant ones |
| `csv` | CSV string: `id,name` / `1,gerda` | `tests/fixtures/<name>.csv` | only the relevant ones |
| `sql` | a query: `select 1 as id, 'gerda' as name` | `tests/fixtures/<name>.sql` | **all** columns; required when the input is **ephemeral**; no Jinja |

```yaml
    given:
      - input: ref('stg_customers')
        format: csv
        fixture: stg_customers_input      # → tests/fixtures/stg_customers_input.csv
    expect:
      format: csv
      fixture: dim_customers_expected     # → tests/fixtures/dim_customers_expected.csv
```

**Incremental models.** Must override `is_incremental` (`true` or `false`). In incremental mode,
mock the current table with `input: this`. `expect` = rows the materialization **inserts/merges**,
not the final table.

**`dbt_utils.star`.** Must be overridden with a column list — fixtures replace the `ref`, so `star`
gets no relation.

**Prerequisite.** The model's **direct parents** must exist in the warehouse. Cheap way:
`dbt run --select "stg_customers top_level_email_domains" --empty`.

**Not supported:** non-SQL models, models in another project, `materialized view`, recursive SQL,
introspective queries.

### When to write a unit test

Yes: regex, date math, window functions, many-branch `case when`, truncation, custom logic,
previously-buggy logic, unseen edge cases, before a refactor, critical models (public, contracted,
upstream of an exposure).
No: warehouse functions like `min()` — already tested by the warehouse.

### Running and selecting

| Goal | Command |
|---|---|
| Only unit tests | `dbt test --select "test_type:unit"` / `--resource-type unit_test` |
| Only data tests | `dbt test --select "test_type:data"` |
| Unit tests of one model | `dbt test --select "dim_customers,test_type:unit"` |
| Skip unit tests in prod | `--exclude-resource-type unit_test` or `DBT_ENGINE_EXCLUDE_RESOURCE_TYPES` (1.11) |
| Order in `dbt build` | unit tests → materialize model → data tests |

Recommended: run unit tests in **dev and CI only** — static inputs, so prod runs waste compute.

**Exam angles.**
- "Validate logic before building" → unit test. "Assert on built data" → data test.
- "Reusable across many models" → custom generic. "One-off query" → singular.
- Unit test result is binary (0/1); data test reports the **number** of failing rows.
- Unit test YAML in `tests/` is wrong; fixture files in `tests/fixtures/` are right.
- Ephemeral parent → `format: sql`.

**Gotchas.**
- `tests:` is still an alias for `data_tests:`, but both keys on the same resource is an error.
- Test inputs as top-level properties next to the test name are deprecated — nest under
  `arguments:` (required in v2).
- One example in `best-practices/custom-generic-tests.md` nests `severity` under `arguments:`.
  That contradicts the rule in `docs/build/data-tests.md`: `severity` is a `config`.
- `--store-failures` writes to a schema suffixed `dbt_test__audit`; each run **replaces** the
  previous failures of that test.

Sources:
- docs/build/data-tests.md
- docs/build/unit-tests.md
- best-practices/custom-generic-tests.md
- reference/resource-properties/unit-tests.md
- reference/resource-properties/unit-test-input.md
- reference/resource-properties/unit-test-overrides.md
- reference/resource-properties/data-formats.md
- reference/resource-properties/unit-testing-versions.md
- reference/global-configs/resource-type.md
- snippets/_unit-tests-prereqs.md (under `website/`, not `website/docs/`)
