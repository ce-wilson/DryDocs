# ADR 0002-B — `controlm-spinoff` → `drydocs-remediation` rebase checklist

```yaml
status: IN_PROGRESS     # PLANNED | IN_PROGRESS | DONE — G3 pulled 2026-07-10; archive inventory underway
date: 2026-06-26
companion_to: docs/decisions/0002-component-database-topology.md   # ADR 0002, D3
depends_on: docs/decisions/0002-a-drydocs-core-extraction-plan.md  # core must exist first
gated_by: ADR 0002 PROPOSED → ACCEPTED
source_branch: ce-wilson/DryDocs-v0-archive@controlm-spinoff        # archived, pre-reorg
target_package: remediation/  (drydocs-remediation)
skill: reconcile-port   # disjoint-history reconcile flow
```

> Realizes ADR 0002 follow-up #3 and answers the original request — "re-create the
> `controlm-spinoff` branch with this intent." The intent is **not** a literal cherry-pick: the
> archive predates the reorg, so we *re-home the spinoff's remediation logic onto the current
> `drydocs-core`* rather than replay its old internals.

---

## 0. What the spinoff actually is (from `drydocs_core/controlm/__init__.py`)

An **independent process** that:
1. **Imports** the *legacy* Control-M job/folder **definition XML** (the env imports/exports
   definitions as XML; Control-M 9.0.21.300).
2. **Analyzes / normalizes** it against the corroborating sources of truth — the Oracle
   `psgmgr.*` extract and the loaded Neo4j snapshot (must reconcile).
3. **Exports a *greenfield* definition XML** that re-derives the same resolved behavior
   (offline equivalence proof).
4. **Hands that off as a Jira** to the source application dev team — *they* hold deploy rights
   (separation of duties); we author, they implement; after it lands in prod the **next main
   load** reflects the change and the ticket closes.

**Critical invariant:** the remediation component **writes no graph.** Its only durable output
is the greenfield XML + the Jira. Neo4j is read-only context here; Jira is the system of record
for the handoff (ADR 0002, D3).

> Keep import/export behind a **format-agnostic interface** — XML is being phased out for BMC's
> JSON Automation API; do not bake XML assumptions into the engine (per the module docstring).

## 1. Preconditions (do not start until all true)

- [x] ADR 0002 is **ACCEPTED** (SME gate) — wiring is gated on acceptance. *(verified 2026-07-10)*
- [x] `drydocs-core` extraction (0002-A) is **DONE**; the core parser surface
      (`resolve_job`, `extract_container_command`, `Invocation`/`FileOp`, models, adapters) is
      importable as `drydocs_core.*`. *(physical relocate merged `0546e21`, 2026-07-10)*
- [x] Read access to `ce-wilson/DryDocs-v0-archive@controlm-spinoff` confirmed; clone it
      read-only for reference (it is *source material*, not a merge base — histories are
      disjoint after the reorg). *(ls-remote verified 2026-07-10: branch tip `3e6a39a`)*

## 2. Rebase steps (re-home, don't replay)

1. [ ] **Scaffold** `remediation/` as `drydocs-remediation` with a `drydocs-core` path
       dependency (per 0002-A §5). Own entrypoint/cadence: *failure-pattern detection*, not cron.
2. [ ] **Inventory the archive:** list the spinoff's modules and tag each — *remediation logic*
       (keep, port) vs. *Control-M parsing* (drop; replaced by `drydocs_core.controlm`) vs.
       *dead/superseded* (leave behind). Record the map in this file's §4.
3. [ ] **Re-home parsing:** delete the spinoff's own Control-M parse code; call
       `drydocs_core.controlm` instead. Any parse divergence the spinoff relied on becomes either
       a core change (PR to core) or a thin remediation-side adapter — never a fork of the parser.
4. [ ] **Port remediation logic only:** the failure-pattern detection, the legacy→greenfield XML
       transform rules, the offline equivalence check, and the Jira emitter. Put the XML read/
       write behind a `DefinitionFormat` interface (XML impl now, JSON impl later).
5. [ ] **Wire the corroboration reads:** legacy XML must reconcile with the Oracle `psgmgr.*`
       extract and the loaded `drydocs` snapshot — all **read-only** via `drydocs_core` adapters +
       `Neo4jClient(database="drydocs")`.
6. [ ] **Jira handoff:** emit the ticket (greenfield XML attached, equivalence proof in body).
       Jira = SoR; no app-side ticket store, no graph write.

## 3. Verification gates (the invariants, as tests)

- [ ] **No-graph-write test:** a unit test asserts `drydocs-remediation` opens no write
      transaction against any DB (mock `Neo4jClient`, assert read-only / session.run never on a
      write path). This is the structural guarantee that remediation can't pollute ground truth.
- [ ] **Jira-only output:** the component's sole side effects are the greenfield XML artifact +
      the Jira call; assert via the emitter boundary.
- [ ] **Offline equivalence proof:** greenfield XML re-derives the same resolved behavior as the
      legacy XML (the parser's resolved-value output matches) — reuses `drydocs_core` resolution
      so the proof is apples-to-apples.
- [ ] **Core boundary holds:** `drydocs-remediation` imports only `drydocs_core.*` (0002-A §4
      boundary test extended to the new package).
- [ ] Existing gates green: `poetry run pytest -q`, package imports, `--help`.

## 4. Old → new home map (fill during step 2)

| Archive module (`controlm-spinoff`) | Disposition | New home |
|---|---|---|
| _Control-M parse/resolve_ | drop | `drydocs_core.controlm` |
| _failure-pattern detection_ | port | `remediation/detect.py` |
| _legacy→greenfield XML transform_ | port (behind `DefinitionFormat`) | `remediation/transform.py` |
| _equivalence check_ | port | `remediation/equivalence.py` |
| _Jira emit_ | port | `remediation/jira.py` |
| _(to be enumerated)_ | | |

## 5. Done criteria

`drydocs-remediation` runs its detect → transform → prove → Jira loop using only
`drydocs-core` for parsing and read-only corroboration; the no-graph-write, Jira-only, and
equivalence tests pass; the boundary test passes. The archived `controlm-spinoff` is then
**superseded** — record it in ADR 0002 (status note) and stop maintaining the archive branch.
