# Learning Path

The path recommended by dbt Labs in the [official study guide](https://www.getdbt.com/dbt-assets/certifications/dbt-certificate-study-guide-version-1-11). Each checkpoint lists courses,
documentation, readings, and hands-on experience. Reorder based on your own background.

---

## Checkpoint 0 — Prerequisites

Start after developing foundational git and SQL skills.

- **SQL**: joins, aggregations, CTEs, window functions.
- **Git**: branching strategies, basic commands, pull requests.

---

## Checkpoint 1 — Build a Foundation

Covers topic 01 almost entirely.

**Courses** (dbt Studio)
- dbt Fundamentals
- Materialization Fundamentals
- Refactoring SQL for Modularity
- Analyses and Seeds
- Snapshots
- Incremental Models
- Jinja, Macros, and Packages

**Documentation**
- Add sources to your DAG · Source configurations
- Materializations · Materialization best practices
- `dbt_project.yml` · dbt Packages · Python models · `grants`
- Add snapshots to your DAG
- About incremental models · About incremental strategy
- About microbatch incremental models
- About the `--empty` flag · About the `--sample` flag

**Commands**
`dbt build` · `dbt run` · `dbt test` · `dbt show` · `dbt snapshot` · `dbt seed` · `dbt docs generate`

**Readings**
- dbt viewpoint
- How we structure our dbt projects
- Refactoring legacy SQL to dbt
- Best practice workflows

**Experience**
- Creating a dbt pipeline from scratch
- Refactoring SQL for performance
- Implementing all core materializations
- Utilizing packages and macros

---

## Checkpoint 2 — Govern and Debug Your Models

Covers topics 02 and 03.

**Courses**
- dbt Mesh — Model Governance module

**Documentation**
- Model contracts · Model versions · Constraints
- Debugging errors · `dbt compile` command
- Behavior changes · About flags (global configs)

**Readings**
- Data product management: best practices

**Experience**
- Being familiar with model access, contracts and versions
- Understanding data product (producer and consumer) management best practices
- Identifying, understanding and debugging errors in dbt logs

---

## Checkpoint 3 — Build Resilient Pipelines at Scale

Covers topics 04, 05, 06 and 07.

**Courses**
- Advanced Testing
- Unit Testing
- Exposures

**Documentation**
- Add data tests to your DAG · Testing and documenting sources
- Writing custom generic data tests · Data test configurations · Unit tests
- About `dbt test` command
- Add Exposures to your DAG · Exposure properties
- `dbt source freshness`
- About `dbt clone` command · Clone incremental models
- About state in dbt · `state` method · `dbt retry`

**Commands**
`dbt test` · `dbt source freshness` · `dbt clone` · `dbt retry` · `dbt state`

**Readings**
- How we structure our dbt projects
- Test smarter not harder
- Test smarter not harder: Where should tests go in your pipeline?
- Your Essential dbt Project Checklist
- To defer or to clone, that is the question

---

## Additional Resources

- dbt Slack community: `#dbt-certification`, `#learn-on-demand`, `#advice-dbt-help`, `#advice-dbt-for-power-users`
- Certification questions: certification@dbtlabs.com
- Registration: Talview — https://pages.talview.com/dbtlabs/certifications/
