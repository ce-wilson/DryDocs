---
title: "Bootstrap / initial-load triage — findings prior to the PEX trace (company-side, transcribed)"
created: 2026-08-28
transcribed: 2026-08-30
status: open
classification: Internal   # names a company container-registry host, a Confluence space, a real SID
transcription_note: >
  Transcribed on this desktop from the company-side session's own file,
  `internal/research/triage-bootstrap-2026-08-28.md` in the company worktree. The findings text
  is reproduced as written; two CONNECTION COORDINATES are placeholdered here because they
  identify nothing needed for comparison and the real values stay in the company-side original:
  the internal container-registry hostname (`<internal-registry>`) and the operator's user id in
  the worktree path and Confluence space (`<user>`). Identifiers — command names, constraint
  names, label names, Confluence page ids, counts — are reproduced in full, per the registered-id
  rule (a name identifies; only host/port/service/credential connects).
venue_of_the_original: "company desktop / container neo4jtest / database drydocs / bolt://localhost:7687"
worktree_of_the_original: "C:\\Users\\<user>\\scratch\\projects\\DryDocs\\.claude\\worktrees\\dd-lineage"
branch_of_the_original: feat/dd_lineage
tags: [bootstrap, initial-load, triage, doc-drift, schema-hygiene, controlm, back-flow]
---

# Bootstrap / initial-load triage — 2026-08-28 (company-side)

> **Split note (theirs).** That file is the pre-PEX half of the 2026-08-28 session. The PEX
> data-flow trace begins in its own log, `pex-controlm-trace.md`, starting at the first
> `ingest-controlm` invocation. Nothing below is a PEX finding.

> **Why this copy exists.** The company session recorded eight defects against a checkout of
> this codebase. Several are ours, several are theirs, and two are the same staleness class
> already logged here as Idea-210. The comparison against producer `main` is in
> [§ Comparison](#comparison-against-producer-main) at the end — that section is this desktop's
> work, not theirs.

## Method — the two rules every finding there obeys

1. **Executed, not recalled.** Every claim is the output of a command run in the venue named in
   the frontmatter. Where a count is quoted, the query that produced it is quoted with it.
2. **Availability test (the neutrality constraint).** A fact counts as a working path only if a
   current support member could reach it with support-level access, without asking the person
   who built it. Each finding therefore carries a knowledge stamp: `SUPPORT-REACHABLE`,
   `SME-ONLY`, or `UNREACHABLE`.

## Environment — confirmed live (theirs)

| Check | Result |
|---|---|
| branch | `feat/dd_lineage` |
| git common dir | shared across worktrees |
| `VIRTUAL_ENV` | cleared to empty as the session's first command |
| venv | worktree-local `.venv` |
| python | 3.12.10 |
| `drydocs check` | `Server: 5.20.0` + `APOC OK.` |
| container | `neo4jtest`, up 4 days, `0.0.0.0:7474->7474`, `0.0.0.0:7687->7687` |
| edition | Enterprise — multi-DB available |
| plugins | `/var/lib/neo4j/plugins` holds `apoc.jar` + `graph-data-science.jar` |
| databases | `ddschema`, `drydocs`, `neo4j`, `system` — all online |
| `.env` resolution | resolves from the **worktree** root, not the main checkout |

## Census trail — the whole initial load, from empty

Database `drydocs`. The graph was wiped by the SME immediately before the run, so the baseline is
a true zero and every later number is a pure delta.

```cypher
// the census, re-run at each step
MATCH (n) RETURN count(n)
MATCH ()-[r]->() RETURN count(r)
MATCH (n:OntologyTerm) RETURN count(n)
SHOW CONSTRAINTS YIELD name RETURN count(*)
```

| Point | Nodes | Rels | OntologyTerm | Constraints |
|---|---|---|---|---|
| baseline (post-wipe) | 0 | 0 | 0 | 62 |
| after `bootstrap` | 120 | 18 | 98 | 62 |
| after dropping 2 typo constraints | 120 | 18 | 98 | 60 |
| after `bootstrap-schema-graph` | 120 | 18 | 98 | 60 |
| after `apply-ontology-supplement` (base) | 167 | 45 | 145 | 60 |
| after `apply-seal-supplement` | 202 | 75 | 160 | 60 |
| after `apply-supplements` (full chain) | 276 | 94 | 194 | 60 |

`bootstrap` seeds ontology scaffolding only — 98 `:OntologyTerm` plus facet classes
(`MediaType` 18, `ProvProperty` 14, `Metric` 10, `DcatProperty` 8, `ProvClass` 7, `SwoClass` 7,
`DprodClass` 6, `OrgProperty` 6, `SwoProperty` 6, `DcatClass` 5, `Dimension` 5, `DqvClass` 5,
`DqvProperty` 5, `OrgClass` 5, `DprodProperty` 3, `OlClass` 3) plus one `:Company`, five
`:BusinessSegment`, one `:Agent`, one `:SoftwareAgent`. Edges: `IN_DIMENSION` 10,
`HAS_BUSINESS_SEGMENT` 4, `HAS_BUSINESS_SEGMENT_HISTORICAL` 4.

**Observation worth carrying:** the constraints already existed at the zero baseline. The SME's
wipe was a data delete, not a database drop — **a clean graph is not necessarily a clean schema.**

## Working paths confirmed

### WP-1 — per-database routing is real

`bootstrap-schema-graph` wrote 72 nodes / 106 rels into `ddschema` and left `drydocs` at exactly
120 / 18. The ADR 0002 topology routing is implemented, not aspirational.

`ddschema` holds a model diagram expressed as a graph: 72 `:SchemaMeta` nodes, each also carrying
the label it represents, wired with exemplar edges (`WAS_ATTRIBUTED_TO` 6,
`QUALIFIED_ATTRIBUTION` 4, `HAD_ROLE` 3, `HAS_THEME` 3, `RUNS_ON` 3, `WAS_GENERATED_BY` 3,
`HAS_DEV_TEAM` 2, `HAS_SUB_LOB` 2).

Stamp: SUPPORT-REACHABLE — two counts, before and after.

### WP-2 — supplement idempotency holds

Re-running an already-applied supplement is a clean verified no-op: in the full chain, `base`
reported `160 -> 160` and `seal` reported `160 -> 160`, both `OK: yes`.

Stamp: SUPPORT-REACHABLE.

### WP-3 — the supplement verifier does its job

Each supplement declares an ontology-term count and the command asserts every declared IRI is
present afterwards, printing declared/verified side by side. A supplement that ran but seeded
nothing would fail here rather than surfacing later as a loader silently matching zero nodes.
Observed: base 47/47, seal 15/15, catalog 24/24, registry 4/4, infrastructure 6/6.

Stamp: SUPPORT-REACHABLE.

### WP-4 — every run writes a HITL trail

Each invocation logs `[run-log] ~\logs\DryDocs\load.supplement.<stamp>.log`, outside the repo.
Observed stamps this session: `20260828-153516`, `20260828-153630`, `20260828-153725`.

Stamp: SUPPORT-REACHABLE.

## Findings

### F-1 — container image drift, config versus reality

`config/dev-environment.yaml` declares `image: neo4j:2026.05.0-enterprise`. The running container
is `<internal-registry>/container-external/docker.io/neo4j/5.20.0-enterprise`.

Two consequences, and the second matters more:

1. The company desktop pulls through the internal mirror, so the bare `docker.io` tag in the
   committed config is not usable there as written.
2. That config's own comment states the store "was written by 2026.05.0 — cannot downgrade to
   5.26". A 5.20.0 server opened this store without complaint, so **this store was never written
   by 2026.05.0.** The committed config describes the producer's container, not the company one.
   Any instruction keyed to that image is wrong on that machine.

Verdict: GAP (config correctness) · Stamp: SUPPORT-REACHABLE (`docker inspect`) ·
Tier: haiku · Guard already exists: `tests/unit/test_dev_environment.py`.
Company-side only — likely a DD-series item; DD is never allocated in a normal groom, so this
needs an explicit SME call.

### F-2 — the initial-load runbook still describes the retired 4-DB topology

Confluence "Control-M Initial-Load Runbook -v3" (page `6265538694`, space `~<user>`, page
version 1, authored 2026-08-11, supersedes v2 page `6239417594`) assumes `drydocs` / `ddlineage`
/ `ddcontext` / `ddall`. Live topology is `drydocs` + `ddschema` only — `ddcontext` and `ddall`
were retired 2026-08-18 (G32/G102), `ddlineage` folded earlier.

This is the sharpest instance of the project's own premise: a runbook written 2026-08-11 was
stale by 2026-08-18, with **no change of owner and no handover** — the drift needs only seven days
and a normal architecture decision.

Verdict: GAP (doc correctness) · Stamp: SUPPORT-REACHABLE · Tier: haiku.

**Worth preserving from that page** — it records a real past failure. v2 ordered `pat_app_links`
before `seal_applications`, which fails:

```
Neo.ClientError.Schema.ConstraintValidationFailed
```

because `pat_app_links.cypher` does `MERGE (a:BusinessApplication {seal_id: row.seal_id})` with
`ON CREATE SET a.is_stub = true` (leaving `app_id` null), while `seal_applications.cypher` merges
on `{app_id}`. **SEAL must load before PAT.**

### F-3 — three stale constraints survived on retired or unknown labels

Live in `drydocs` but declared in no `drydocs_core/schema/**/*.cypher`:

| Constraint | Label | Disposition |
|---|---|---|
| `ais_capability_id` | `:AisCapability` | **DROPPED** this session — SME confirmed typo leftover |
| `ais_tool_id` | `:AisTool` | **DROPPED** this session — SME confirmed typo leftover |
| `membership_id` | `:Membership` | **RETAINED** — K4 retired the reified Membership pattern 2026-07-10; still open |

Both drops were preceded by a zero-node safety check:

```cypher
// never drop a constraint that is still guarding live nodes
MATCH (n:AisCapability) RETURN count(n)   // -> 0
MATCH (n:AisTool)       RETURN count(n)   // -> 0
```

Constraints outlive data wipes, so a retired-label constraint can silently enforce an old
identity rule against any future load that reuses the label.

**Open item:** `membership_id`. SME direction was to note that code references exist which should
be marked deprecated, and explicitly **not to chase that path** — recorded here, not acted on.

Verdict: GAP (schema hygiene) · Stamp: SUPPORT-REACHABLE (`SHOW CONSTRAINTS`) · Tier: sonnet.

**Derived idea:** `bootstrap` already verifies "58/58 declared present". It could also report
live-but-undeclared constraints as a drift warning — the asymmetry is the whole reason these
three survived unnoticed.

### F-4 — the run-drydocs skill misdescribes the CLI, in two ways

`.claude/skills/run-drydocs/SKILL.md`:

1. Documents the supplement chain as `base -> seal -> catalog -> registry` (four).
   **Reality is five** — `infrastructure` follows `registry`.
2. Lists `refresh-catalog`, `refresh-applications`, `refresh-teams` as commands and calls
   `refresh-reference` "deprecated; delegates to the above three". **This is exactly backwards.**
   Observed:

```
drydocs refresh-catalog
  -> No such command 'refresh-catalog'.   EXIT=2
```

`refresh-reference` is the only one of the four that is registered.

Verdict: GAP (doc correctness) · Stamp: SUPPORT-REACHABLE · Tier: haiku.

### F-5 — the same wrong names propagated into that session's own code survey

Before running anything, an exploration pass produced a CLI inventory listing `refresh-catalog`,
`refresh-applications`, `refresh-teams`, `verify-reference`, `verify-controlm`,
`load-folder-attribution`, `code-graph-freshness` and `render-plan-board`. **None are registered.**
The pass had read the skill file and docs rather than the importable object, and produced a
confident, well-cited, wrong answer that only execution exposed.

This is the availability test running in the opposite direction: a plausible answer no support
member could have acted on successfully. It is also a live demonstration of the repo's own J37
rule — never parse a render when the object is importable.

**Method correction adopted for the remainder of the work:** command names come from
`drydocs.cli.app.registered_commands`, never from prose.

Verdict: GAP (method) · Stamp: SUPPORT-REACHABLE · Tier: haiku.

### F-6 — DevX Fabric surfaces are under-registered

`config/source-registry.yaml` has a `devx` system row and two datasets, `devx:bitbucket-repo` and
`devx:githubrepo`, both `confirmed: false` / census-only. Real projects expose more tool surfaces
than that:

| Surface | Registry dataset |
|---|---|
| `tools/bitbucket` | `devx:bitbucket-repo` — registered, census-only |
| GitHub org team | `devx:githubrepo` — registered, census-only |
| Confluence space | **none** |
| Jira project | **none** |
| `tools/jules` | **none** |
| Artifactory container-release / -base / -sandbox | **none** |

Verdict: GAP (source coverage) · Stamp: SUPPORT-REACHABLE · Tier: sonnet — adding census-only
datasets to an existing system row changes no schema, no ontology and no boundary, and
`tests/unit/test_source_registry.py` gives it a written acceptance test.

The per-SEAL values belong in an `internal/sdlc-surfaces/` twin, never in the tracked config row.

## Authoritative CLI inventory (theirs) — 67 commands

Read from `drydocs.cli.app.registered_commands`, not from `--help` and not from prose.

```
analyze-variables, apply-catalog-supplement, apply-contacts-supplement,
apply-employee-audit-edges, apply-infrastructure-supplement, apply-locations-supplement,
apply-ontology-supplement, apply-platforms-supplement, apply-registry-supplement,
apply-resource-pools-supplement, apply-seal-deployments-supplement, apply-seal-supplement,
apply-sosa-supplement, apply-supplements, bootstrap, bootstrap-schema-graph, check,
convert-vendor-docs, docs-coverage, docs-diff, docs-fetch, docs-preview, docs-publish,
docs-register, docs-status, docs-verify, export-cmdline-staging, fid-census,
graph-review, graph-verify, ingest-controlm, ingest-controlm-xml, landing-zones,
lineage-review, load, load-batch-orchestrators, load-bmc-docs, load-code-snapshot,
load-dev-teams, load-doc-traceability, load-email-extracts, load-employee-roster,
load-manual-mappings, load-seal-attribution, load-server-inventory, load-snow-app-group,
load-snow-group-members, load-snow-support-crosswalk, load-snow-support-groups,
load-snow-tom-responsibilities, load-software-registry, load-vendor-docs, m1-verify,
m3-verify, m6-verify, new-doc-section, normalize-variables, parse-cmdline-staging,
patch-window, prune-snapshots, refresh-reference, reset, resolve-cmdline-staging,
sme-notes, snapshot, sweep-removed, verify
```

`reset` and `snapshot` are registered and undocumented in the skill. `reset` in particular is
worth understanding before anyone runs it by accident.

Legacy per-supplement verbs are thin aliases onto the G29 chain with an implicit `--only`:
`apply-ontology-supplement` prints a table titled `apply-supplements` and applies only `base`.

## `DRYDOCS_DATA_ROOT` — not the evidence folder

Two roots, two jobs, easy to conflate:

- `DRYDOCS_DATA_ROOT` is DryDocs' own out-of-repo payload store (G19,
  `drydocs_core/data_root.py`) with a contracted layout — `rua/incoming`,
  `rua/extracted/<bundle>`, `dpl-registry/<seal>`, `catalog/`, `catalog/screenshots/` — swept by
  `tests/unit/test_data_root.py`.
- The SME's manual evidence intake has no code contract at all.

Also note `[Environment]::SetEnvironmentVariable(...,'User')` does not affect an already-running
shell, and the value chosen matched `DEFAULT_DATA_ROOT` (`Path.home()/"data"/"DryDocs"`) anyway,
so it changed nothing functionally.

## Tools and skills used (theirs)

| Tool / skill | Used for |
|---|---|
| `run_in_terminal` | every executed command; the sole source of evidence there |
| Confluence publish tool (`-page`) | fetching runbook v3 by page id |
| `read_file`, `grep_search`, `file_search`, `list_dir` | repo inspection |
| Explore subagent | initial code survey — **produced F-5's wrong CLI inventory** |
| skill `run-drydocs` | run procedure — **and the subject of F-4** |
| skill `controlm-db` | Control-M table grounding (consulted, not yet exercised) |
| memory (session / repo) | session plan and standing rules |

Notable: two of the tools in that table are themselves findings. The Explore subagent produced a
wrong inventory (F-5) and the run-drydocs skill it partly read is wrong (F-4).

## Handoff (theirs)

The main session owns the hand-loader list and may change this code. Nothing in that file had
been actioned beyond the two SME-directed constraint drops. Open items, in rough priority:

1. **F-3 open item** — `membership_id` on the K4-retired `:Membership`, plus the code references
   the SME wants marked deprecated (explicitly out of scope there).
2. **F-4** — correct the run-drydocs skill: five supplements, and the `refresh-*` reversal.
3. **F-2** — bring runbook v3 to the 2-DB topology, keeping its SEAL-before-PAT note.
4. **F-1** — reconcile `config/dev-environment.yaml` with the mirrored image tag.
5. **F-6** — register the missing `devx:*` surfaces as census-only datasets.
6. **Derived idea** — bootstrap-time drift warning for live-but-undeclared constraints.

---

<!-- anchor: comparison-against-producer-main -->
## Comparison against producer `main` (this desktop, 2026-08-30)

Everything in this section was executed on this desktop against `main` at the working tree, by
reading importable objects rather than prose — the method correction F-5 itself argues for.
Venue (J18): desktop, this checkout, no Neo4j connection required for any of it.

| Finding | Status here | Evidence on producer `main` |
|---|---|---|
| **F-1** image drift | **HALF CONFIRMED, half theirs** | `config/dev-environment.yaml:18` declares `image: neo4j:2026.05.0-enterprise` with the exact comment quoted. The mirrored-registry half is company-only — this desktop pulls direct. Their point 2 stands as a *company* correction: the committed config describes the producer's container. |
| **F-2** runbook 4-DB topology | **theirs** | Confluence page in their space. G32/G102 retirements are ours and already landed. |
| **F-3** stale constraints | **RESOLVED HERE, and further than they knew** | `membership_id` was **DROPPED at G99 (2026-08-18)** — `drydocs_core/schema/constraints.cypher:106`. `pat_team_roles.cypher` no longer writes `:Membership`; it writes the qualified-attribution shape. `:AisCapability` / `:AisTool` appear nowhere in `drydocs_core/schema/`. All three are live-graph residue on their instance, not producer defects. |
| **F-4 claim 1** — chain is five, not four | **CONFIRMED, AND WORSE** | `default_chain()` returns `['base','seal','catalog','registry','infrastructure']` — five. `.claude/skills/run-drydocs/SKILL.md:68` says four, **and so does the command's own docstring**, `drydocs/cli_ingest.py:517`. Their finding named only the skill; the docstring is the same error one layer deeper, and a docstring is what a reader trusts most. |
| **F-4 claim 2** — `refresh-*` reversal | **DOES NOT REPRODUCE — their tree predates G79** | On `main`, `refresh-catalog`, `refresh-applications` and `refresh-teams` are all registered (`drydocs/cli_ingest.py:213`), and `refresh-reference` is the deprecated alias that delegates to them (`:356-371`, "deprecated (G79)"). `CHAINS` keys are exactly those three. The skill is **correct here**. Their observed `EXIT=2` is the pre-G79 state. |
| **F-5** wrong CLI inventory | **PARTLY A TREE DIFFERENCE, NOT ONLY A METHOD FAILURE** | Of the eight names the subagent listed as unregistered, **seven ARE registered on `main`**: `refresh-catalog`, `refresh-applications`, `refresh-teams`, `verify-reference`, `verify-controlm`, `load-folder-attribution`, `code-graph-freshness`. Only `render-plan-board` exists nowhere. The method rule they adopted is right and we already enforce it (J37, `tests/unit/test_no_render_parsing.py`) — but the subagent was substantially describing *this* tree while running against *theirs*. |
| **F-6** DevX under-registered | **NOT APPLICABLE — no `devx` rows exist here** | `grep devx config/source-registry.yaml` returns nothing. The `devx` system row and its two datasets are company-side additions that have never been ported back. That is itself a back-flow finding. |
| **CLI inventory 67 vs 50** | **large divergence, both directions** | `main` registers **50** commands. Theirs has 67, including a whole `docs-*` family (`docs-diff`, `docs-fetch`, `docs-preview`, `docs-publish`, `docs-register`, `docs-status`), `graph-review`, `graph-verify`, `sme-notes`, `new-doc-section`, `ingest-controlm-xml`, `m6-verify`, `load-snow-*`, `load-employee-roster`, `load-dev-teams`, `load-seal-attribution`, `apply-contacts/locations/platforms/resource-pools/seal-deployments-supplement`. Several of those are the SME-review/HITL toolkit already named as the top back-flow candidate. `main` has `load-essential-graphrag` and `profile-folder-set`, which theirs does not. |
| **Derived idea** — bootstrap reports live-but-undeclared constraints | **new, and it is a real gap here too** | Nothing on `main` reports the undeclared direction; the verifier only asserts declared-present. Worth an IDEAS entry. |

### What this comparison establishes

1. **Two producer defects.** F-4 claim 1 is live on `main` in two places (the skill and the
   docstring), and the derived drift-warning idea names a real asymmetry in `bootstrap`.
2. **Four findings are their tree being behind ours.** F-4 claim 2 and most of F-5 are pre-G79
   and pre-G99 states. This is the third recorded instance of a company-side review reporting
   staleness as a defect — the same class already logged as Idea-210, whose six wrong facts came
   from a checkout predating S8/S13/G78/G79. That is now a pattern with a cause, not a
   coincidence: a review run against an un-ported checkout will keep manufacturing defects.
3. **Two are genuinely theirs.** F-1's mirrored image tag and F-2's runbook are company
   artifacts; neither has a producer-side deliverable.
4. **F-6 and the 17-command gap are back-flow inventory,** not defects — they enumerate what the
   company tree has that `main` does not, which is exactly what the drydocs-review back-flow epic
   needs and has never had in measured form.
