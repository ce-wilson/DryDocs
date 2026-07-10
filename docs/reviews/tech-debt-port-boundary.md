# Tech-debt audit — the publisher→consumer (port) boundary

**Date:** 2026-07-09 · **Scope:** producer `ce-wilson/DryDocs` (publisher) → company
`<org>/DryDocs` (consumer) port boundary — can the *known break points* be segregated?
· **Method:** `/tech-debt` framework (Impact + Risk) × (6 − Effort) · **Classification:** Internal-Public
(mechanism only).

**Verdict up front: yes, they can be segregated — and the repo already owns the pattern
to do it.** Every successful guard in this codebase is a *machine-readable ledger + a unit
test* (`classification.yaml` + `test_classification`, `MODULE_MAP.md` + `test_module_boundary`,
`source-mappings/*.yaml` + `test_source_mappings`, `backlog.yaml` + `test_backlog`). The port
boundary is the one governance surface still encoded **entirely as prose** — 676 lines of
`git-readme.md` + 348 lines of `docs/port-prompt.md` (24 ordinal steps) + the 164-line
`reconcile-port` skill ledger, three documents that explicitly promise to mirror each other
and have no test that they do. That is the root debt; everything below hangs off it.

---

## 1. Break-class inventory (the segregation)

The known breaks fall into six classes with *different* mechanics. Segregating them matters
because each class has a different correct resolution, and today they are interleaved in
the same prose documents.

### Class A — Reverse-direction collisions (Canonical-COMPANY)
Same path, both sides author it, and the **consumer wins** — the inverse of every other rule.
- Paths: `drydocs/graph_review.py`, `graph_verify.py`, `review_labels.py`, `sme_notes.py`,
  `gate_pages.py`, `drydocs/publishing/**`, `config/review-labels.yaml`,
  `config/gate-prompts/**`, `graph-tests/**` (the `drydocs-review` back-flow stream).
- Break mode: a mechanical cherry-pick clobbers the company's *wired* originals (real
  Confluence coordinates, real review labels, real gate specs) with the sanitized public
  template. Explicitly called the one place the direction reverses.
- Current guard: prose in three places. Nothing executable.

### Class B — Per-ENTRY collisions inside shared files
Path-level rules cannot resolve these; the collision is a single YAML entry or log block.
- `relationship_vocabulary.yaml` / `taxonomy-ontology-map.yaml`: normally Canonical-producer,
  **except** back-flow-origin entries (`m3_seal_app_ref`) where a company `active`/`confirmed`
  status must never be downgraded to the producer's `planned`/`proposed`.
- `config/gate-log.md`: append-only — merge is the chronological UNION of both sides' entries.
- `pyproject.toml`: union of deps, but the `version` string is per-repo cadence (keep consumer's);
  release tags never cherry-pick.
- Break mode: "take file wholesale" silently regresses consumer state. The rule exists only as
  prose caveats bolted onto the path-level rule.

### Class C — Integration-point hand-merges (both sides evolve forever)
- `drydocs/cli.py` (composition root), `drydocs/models/__init__.py`, `models/controlm.py`,
  `tests/unit/test_schema.py` (`EXPECTED_CONSTRAINTS` 44 vs 35), `test_controlm_cypher.py`
  (`scope_key` vs `folder_id` condition key).
- Break mode: every port re-conflicts on the same files; resolutions live in the collision
  ledger and depend on operator care. The `cli.py` case is structural: a single flat
  composition root accretes both sides' commands. (The `ENTRYPOINT_MODULES` exemption
  settled the *boundary-guard* fight; it did not shrink the merge surface.)

### Class D — Environment/wiring divergence (consumer is simply different)
- `drydocs/adapters/oracle_adapter.py` — company Kerberos/thick vs producer thin
  (**port-frozen**, keep company); the live multi-DB Neo4j target; Confluence connector
  wiring; ~175 company-only paths including data-bearing modules (`locations.py`,
  `seal_deployments.py`, `controlm_app_codes.py`) that must never back-flow as values.
- Break mode: not a merge conflict — a *capability* difference. Danger is a port that
  "reconciles" (deletes or overwrites) what the producer has never had.

### Class E — Gitignored-asset dependencies
- BMC 6.4.01 poster PDF (mitigated: transcribed into `controlm-db/references/er-model.md`),
  `drydocs/data/` samples (mitigated: Track-1 `skipif` guards — but a prior port *lost* the
  skip guard and re-derived it divergently), `internal-local/` (gate-page renders, Kerberos
  connection config, screenshots), `SDLC-Docs/` corpus.
- Break mode: code or acceptance criteria silently depend on an asset that does not travel.
  The Track-1/Track-2 split is the right pattern; its application is per-case and untested
  as a policy.

### Class F — Rename waves across disjoint history
- Done: `vendor/` → `external/orchestration/`, `NODE_QUICK_REFERENCE.md` rehome, seed-twin
  renames (`vendor-bmc-*` → `bmc-docs-*`). **Pending: the big one** — ADR 0002 Phase B
  (`drydocs/` → `drydocs-core` + component packages), which the port guide itself says will
  make the current per-file collision rules "**superseded**".
- Break mode: with no merge-base, every rename is delete+add on the consumer; each wave
  multiplies Class A–C collisions and invalidates the prose tables wholesale.

### Meta-class — the documentation debt that binds them
Three prose artifacts carry the dispositions; they self-describe as mirrors
("Mirrored in the reconcile-port skill's divergence ledger and docs/port-prompt.md");
port-prompt **step numbers are the declared authority** for newer streams — an ordinal
coupling that renumbers as steps grow; and nothing executable checks any of it.

---

## 2. Scoring — (Impact + Risk) × (6 − Effort)

| # | Debt item | Class | Impact | Risk | Effort | Priority |
|---|---|---|---|---|---|---|
| 1 | Port dispositions are prose-only; no machine-readable manifest, no guard test, 3 docs to keep in sync | meta | 5 | 5 | 2 | **40** |
| 2 | Phase B rename wave scheduled with no manifest to survive it (guide admits rules get superseded) | F | 4 | 5 | 1* | **45*** |
| 3 | Per-entry rules (status downgrade, gate-log union, version string) unenforced | B | 3 | 4 | 2 | **28** |
| 4 | Canonical-COMPANY surfaces share paths with generic templates (no physical segregation) | A | 4 | 4 | 3 | **24** |
| 5 | Skip-guard / gitignored-asset policy is per-case, not tested as policy | E | 3 | 3 | 2 | **24** |
| 6 | `cli.py` flat composition root = permanent hand-merge surface | C | 3 | 3 | 4 | **12** |
| 7 | Company-only data-bearing modules rely on prose "never back-flow" | D | 2 | 4 | 2 | **24** |

\* item 2's "effort 1" is a *sequencing decision* (do #1 before Phase B), not a build.

---

## 3. Remediation plan (phased, alongside feature work)

### Phase 1 — `PORT-MANIFEST.yaml` + guard test (items 1, 2, 3 — do first, before ADR 0002 Phase B)
One machine-readable ledger, schema `drydocs.port-manifest.v1`, one row per path/glob:

```yaml
- path: "drydocs/publishing/**"
  disposition: canonical-company        # clean-add | canonical-producer |
  stream: drydocs-review                #   canonical-company | union-append |
  note: "wired connector; producer copy is the sanitized template"   # per-entry | evaluate | never-port
- path: "config/gate-log.md"
  disposition: union-append
- path: "drydocs/ontology/relationship_vocabulary.yaml"
  disposition: per-entry
  entry_rule: "id-keyed; never downgrade status active/confirmed -> planned/proposed"
- path: "drydocs/adapters/oracle_adapter.py"
  disposition: canonical-company
  note: "port-frozen; Kerberos thick vs thin"
```

- `tests/unit/test_port_manifest.py`: schema-valid; every disposition in the enum;
  `per-entry` rows carry an `entry_rule`; **every tracked top-level path resolves to
  exactly one row** (the default-deny discipline `test_module_boundary` already proved).
- `git-readme.md` / `port-prompt.md` / `reconcile-port` shrink to narrative *around* the
  manifest; the manifest is the authority (kills the step-number coupling — rows are
  id-keyed, not ordinal). Both repos read the same file, so the consumer's `reconcile-port`
  run can drive resolution mechanically: checkout for `canonical-*`, scripted union for
  `union-append`, halt-for-human only on `per-entry` and `evaluate`.
- **Sequencing rule:** land the manifest *before* the ADR 0002 Phase B package split — the
  rename wave then becomes a manifest diff (path column updates) instead of a prose rewrite.

### Phase 2 — enforce the per-entry rules (item 3)
Small validators, reusing existing accessors: a vocab/map reconciler check ("no status
downgrade for ids marked back-flow-origin"), a gate-log append-only check (existing entries
are a prefix), and the pyproject version-string rule noted in the manifest. These run
consumer-side during `reconcile-port`, producer-side as plain unit tests.

### Phase 3 — physically segregate Class A (item 4)
The connector/overlay split the docmeta plan already gestures at: generic mechanism
(producer-authored, portable) vs wired connector + real config (consumer-authored,
`canonical-company`, ideally under paths the producer *never writes* — e.g.
`drydocs/publishing/connectors/` + `internal/` config overlays). End state: Class A shrinks
from nine colliding paths to zero — collisions become clean non-overlap. Do opportunistically
per module (natural moment: the Phase B split touches these files anyway).

### Phase 4 — policy tests for Class D/E (items 5, 7)
- A `never-port` disposition in the manifest for the data-bearing company-only modules
  (documents the rule where the tooling reads it).
- A producer-side test that every test reading `drydocs/data/` or `internal-local/` carries
  a skip guard (the exact failure a prior port hit).

### Deferred (accepted debt)
- Item 6 (`cli.py` composition root): live with the hand-merge; the entrypoint exemption is
  settled and a sub-app split was explicitly rejected. Revisit only at the Phase B move.

---

## 4. Business justification, one line each
1. **Manifest (P1):** every port today bets ~an operator-day and the company's wired review
   stack on prose being read correctly; one blind `checkout` of `drydocs/publishing/**`
   destroys real Confluence wiring.
2. **Sequencing (P1):** doing Phase B first forces a full prose rewrite *and* one
   unguarded high-collision port — the most dangerous single event on the roadmap.
3. **Per-entry guards (P2):** the `m3_seal_app_ref` downgrade scenario silently reverts an
   SME-confirmed gate decision — governance regression, not just code.
4. **Class A split (P3):** converts the only reverse-direction rule (the one most likely to
   be executed backwards) into ordinary non-overlapping paths.

---
*Sources read for this audit: `git-readme.md` (676 ln), `docs/port-prompt.md` (348 ln, 24 steps),
`.claude/skills/reconcile-port/SKILL.md` (collision + divergence ledgers), `MODULE_MAP.md`,
`tests/unit/test_module_boundary.py`, `tests/unit/test_publishing.py`, `PUBLISH-BOUNDARY.md`,
`knowledge/upgrade-plans/docmeta-component.md` (port §6 dispositions).*
