# graph-tests — data-driven acceptance suites for `graph-verify`

Each `*.yaml` file here is a **suite** of `TC-*` cases the `drydocs-review`
component's `graph-verify` runner executes against a live graph. A case is a Cypher
query plus an assertion on the result shape (`empty` / `nonempty` / `equals`).

- Loader + evaluator live in [`drydocs/review/graph_verify.py`](../drydocs/review/graph_verify.py)
  and are **pure/offline** (unit-tested with no Neo4j). Only running a suite touches
  the graph.
- **classification: Internal-Public.** The committed example
  ([`bmc-docs-smoke.yaml`](bmc-docs-smoke.yaml)) is a generic smoke test seeded from
  the bmc-docs corpus (BMC Control-M docs baseline; corpus id per ADR 0004). Real
  acceptance suites that encode internal counts/IDs belong in a gitignored
  `graph-tests/` twin, never here.

## Suite format

```yaml
classification: Internal-Public
schema: drydocs.graph-tests.v1
suite: <name>
description: <what this suite proves>
targets: [Label, Label]          # optional — validated against config/review-labels.yaml
cases:
  - id: TC-01
    description: <human-readable expectation>
    cypher: "MATCH ... RETURN ..."
    assert: empty | nonempty | equals
    expected: [{col: value}]     # required only for `equals`
    params: {}                   # optional bind params
```

## Assertions

| `assert` | passes when |
|---|---|
| `empty` | the query returns **zero** rows (e.g. "no orphan jobs") |
| `nonempty` | the query returns **at least one** row |
| `equals` | the returned rows deep-equal `expected` (a list of row dicts) |

A suite fails (non-zero exit) if any case fails.
