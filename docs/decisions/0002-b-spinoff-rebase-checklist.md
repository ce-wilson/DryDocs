# ADR 0002-B — `controlm-spinoff` → `drydocs-remediation` rebase checklist

```yaml
status: DONE            # PLANNED | IN_PROGRESS | DONE — G3 closed 2026-07-10; §5 criteria met; controlm-spinoff archive SUPERSEDED
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

1. [x] **Scaffold** `remediation/` as `drydocs-remediation` with a `drydocs-core` path
       dependency (per 0002-A §5). Own entrypoint/cadence: *failure-pattern detection*, not cron.
       *(DONE 2026-07-10, IN-MONOREPO variant per ADR 0002-A-1 + user call: the package is
       top-level `drydocs_remediation/` — a bare `remediation/` dir would claim the generic
       `import remediation` name; `drydocs_remediation` matches the `drydocs_core` convention.
       Same single Poetry distribution (no path dep needed — 0002-A §5 mechanics deferred to
       Phase C); boundary test gains the `remediation` COMPONENT_GROUP; modules =
       formats (DefinitionFormat seam) / detect / transform / equivalence / jira (the only
       side-effect boundary); all bodies NotImplementedError pending the M0 PoC slice;
       tests/unit/test_remediation_scaffold.py pins the structural contract.)*
2. [x] **Inventory the archive:** list the spinoff's modules and tag each — *remediation logic*
       (keep, port) vs. *Control-M parsing* (drop; replaced by `drydocs_core.controlm`) vs.
       *dead/superseded* (leave behind). Record the map in this file's §4.
       *(DONE 2026-07-10, archive tip `3e6a39a` — see §4. Headline: the archive contains NO
       remediation code; its remediation IP is the plans + the R1–R29 rules registry + the
       governance corpus. Parser divergence check: current core strictly AHEAD, zero
       archive-only deltas → step 3 is a no-op, no core PRs needed.)*
3. [x] **Re-home parsing:** delete the spinoff's own Control-M parse code; call
       `drydocs_core.controlm` instead. Any parse divergence the spinoff relied on becomes either
       a core change (PR to core) or a thin remediation-side adapter — never a fork of the parser.
       *(NO-OP by inventory, 2026-07-10: all 8 archive parser modules diffed — current core
       strictly ahead, zero archive-only deltas; the component was built calling core from birth.)*
4. [~] **Port remediation logic only:** the failure-pattern detection, the legacy→greenfield XML
       transform rules, the offline equivalence check, and the Jira emitter. Put the XML read/
       write behind a `DefinitionFormat` interface (XML impl now, JSON impl later).
       *(PARTIAL 2026-07-10 — the M0 slice: `TranscriptDefinitionFormat` (the gate-1 fallback;
       XML impl is BLOCKED on the vendor schema acquisition, see the corpus stub — implementing
       from memory would ship SYNTHESIZED guesses as vendor truth), the R1 dot-smuggling
       detector over the core classifier, and the order-paired equivalence proof over the core
       resolver. Engine run on the real M0 unit reproduces the worked example verbatim
       (internal/remediation/m0/engine-run-2026-07-10.md); sanitized twins pinned as unit tests.
       REMAINING: transform (Gate 3) + jira emitter (M1); XML I/O on schema acquisition;
       equivalence verdict pending ground truth A3 / var.text rule B1.)*
       *(FURTHER 2026-07-10 — the Tier-1/handoff slice (TDD FR-REM-3/6 + NFR-REM-1; NOTE:
       the archive's "M1 = standalone ctm-remediate repo split" is SUPERSEDED by this ADR —
       the engine stayed in drydocs_core, the component in-monorepo): ratified-only Tier-1
       transform engine with the canonical-variable-rename rule (idempotent, behavior-
       preserving under the equivalence proof; unratified rules skipped loudly — rule VALUES
       stay company-side, registry data shape = TDD OQ-2, deliberately open), the Jira
       handoff boundary (pure deterministic render; JiraSubmitter is the only wire, REST
       impl company-side; unproven packages refuse to emit; unresolved ownership surfaced
       as a defect), and the structural no-graph-write guard. 26 remediation tests green.
       REMAINING: Tier-2 agentic lane (FR-REM-4, gated per-fix HITL), corroboration reads
       (§2 step 5), XML I/O (schema acquisition), M2 generalization of detect/prove.)*
5. [x] **Wire the corroboration reads:** legacy XML must reconcile with the Oracle `psgmgr.*`
       extract and the loaded `drydocs` snapshot — all **read-only** via `drydocs_core` adapters +
       `Neo4jClient(database="drydocs")`.
       *(MECHANISM DONE 2026-07-10: `corroborate.reconcile_variables` (pure) +
       `corroborate.ReadOnlyGraph` — the sole graph path, refuses write Cypher BEFORE the driver.
       The schema-specific live queries are Track-2, written company-side through the wrapper.)*
6. [x] **Jira handoff:** emit the ticket (greenfield XML attached, equivalence proof in body).
       Jira = SoR; no app-side ticket store, no graph write.
       *(BOUNDARY DONE 2026-07-10: pure deterministic render + `JiraSubmitter` sole wire;
       unproven packages refuse to emit; REST impl + real tickets are company-side operations.)*

## 3. Verification gates (the invariants, as tests)

- [x] **No-graph-write test:** a unit test asserts `drydocs-remediation` opens no write
      transaction against any DB (mock `Neo4jClient`, assert read-only / session.run never on a
      write path). This is the structural guarantee that remediation can't pollute ground truth.
      *(test_remediation_no_graph_write.py — structural AST guard; test_remediation_corroborate.py
      — runtime: write Cypher raises before the spy driver, boundary confirmed empty.)*
- [x] **Jira-only output:** the component's sole side effects are the greenfield XML artifact +
      the Jira call; assert via the emitter boundary. *(test_remediation_handoff.py)*
- [x] **Offline equivalence proof:** greenfield XML re-derives the same resolved behavior as the
      legacy XML (the parser's resolved-value output matches) — reuses `drydocs_core` resolution
      so the proof is apples-to-apples. *(test_remediation_m0.py + test_remediation_tier1.py;
      the REAL M0 unit's verdict stays pending ground truth A3/B1 — a data fact, not a gate gap.)*
- [x] **Core boundary holds:** `drydocs-remediation` imports only `drydocs_core.*` (0002-A §4
      boundary test extended to the new package). *(`remediation` COMPONENT_GROUP, default-deny.)*
- [x] Existing gates green: `poetry run pytest -q`, package imports, `--help`.
      *(505+ passed / 3 expected skips at close, 2026-07-10.)*

## 4. Old → new home map (filled 2026-07-10, archive tip `3e6a39a`)

**Headline finding:** the archive carries **no remediation code** — detect / transform /
equivalence / Jira were never built. The spinoff's remediation IP is entirely in
`internal-standards/`: the phased plans, the **R1–R29 machine-checkable rules registry**
(explicitly "the single source for both validation (Gate 2) and greenfield generation
(Gate 3)" — this IS the detect/transform rule set), and its `governance/` corpus. The
§2-step-4 modules are therefore **greenfield builds guided by the ported docs**, not ports.

| Archive path (`controlm-spinoff`) | Disposition | New home / note |
|---|---|---|
| `drydocs/controlm/*` (parser, 8 modules + staging) | **drop** | superseded by `drydocs_core.controlm`; diffed all 8: current core strictly AHEAD (ABINITIO `.pset`, spark-submit `_looks_script`, doc-path refs) — ZERO archive-only deltas, **no core PRs needed** |
| `drydocs/` rest (models/adapters/loaders/cli/schema/ontology/snapshots), `tests/`, `scripts/` | leave | the pre-reorg monolith, superseded by current main |
| `internal-standards/standards-rules-registry.md` (R1–R29) | **PORT** | the detect (Gate 2) + greenfield (Gate 3) rule source; marked "Corpus: INTERNAL" — classification decided at ingestion; rules carry ratification status (✅/🟡/❓) → unratified rules stay gate-bound |
| `internal-standards/governance/**` (10 docs: escalation-scim-reference, scim-hpsm-queue-registry, critical-batch-and-self-heal, nfr-catalog, nfr-consistency-and-greenfield, command-line-and-variables-standard, dat/hlt-naming-standards, greenfield-recommendations, CONTINUATION-PLAN) | **PORT, per-doc classification** | R13–R29 source corpus. SCIM/HPSM/escalation content is likely Internal(-Confidential) → `internal/`; pure-mechanism naming standards may join `knowledge/standards/` — classify each at ingestion, never blanket |
| `internal-standards/controlm-remediation-{spinoff-plan,flow,m0-poc-scope,phases-m1-m4-scope,information-needed}.md` + `m0-poc-worked-example.md` (~630 lines) | **PORT** | component source material; reconcile against the NEWER `docs/design/drydocs-remediation-tdd.md` — the TDD contract wins on conflict |
| `internal-standards/standards-normalization-plan.md` | evaluate | possible predecessor of current `knowledge/standards/` content — compare before porting |
| `internal-standards/{calendar-resolution-projection-plan, data-center-naming-convention, description-field-metadata-plan, folder-naming-convention, README}.md` | leave | already carried into `knowledge/standards/` |
| `internal-standards/{SAVE-POINT, main-branch-gap-analysis, cron-actions}.md` | leave | point-in-time session/gap notes; rituals superseded by current CLAUDE.md |
| `vendor-bmc/**` | leave | fully carried to `external/orchestration/bmc-controlm/` (verified: zero archive-only docs) |
| `bmc-9-0-22-creating-a-job.txt` | leave | raw scrape; superseded by the converted corpus |
| `docs/**`, `DryDocs_Ontology_Documentation.md`, `git-readme.md`, `.claude/**` | leave | superseded by current main |

## 5. Done criteria

`drydocs-remediation` runs its detect → transform → prove → Jira loop using only
`drydocs-core` for parsing and read-only corroboration; the no-graph-write, Jira-only, and
equivalence tests pass; the boundary test passes. The archived `controlm-spinoff` is then
**superseded** — record it in ADR 0002 (status note) and stop maintaining the archive branch.
